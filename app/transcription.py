import os
from typing import List, Dict, Any, Optional, Tuple
import torch
import whisper
from flask import current_app
from logging import getLogger

from app.config import AudioConfig, TranscriptionConfig
from app.errors import silence_error
from app.preprocessing import PreprocessingService

logger = getLogger(__name__)


class TranscriptionService:
    """Service for transcribing audio files using Whisper models."""

    @staticmethod
    def transcribe_audio(
            file_path: str,
            model: Any,
            languages: List[str],
            keywords: List[str],
            pre_process_file: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file using the provided model with support for multiple languages.

        Args:
            file_path: Path to the audio file
            model: Whisper model instance
            languages: List of language codes to transcribe into
            keywords: List of keywords to enhance recognition accuracy
            pre_process_file: Whether to preprocess the audio file

        Returns:
            Dictionary containing transcriptions and detailed segment information
        """
        try:
            # Get processed audio file and sample rate
            audio_file_path, sample_rate = TranscriptionService._prepare_audio(file_path, pre_process_file)

            # Load and validate audio
            audio = whisper.load_audio(audio_file_path)
            TranscriptionService._validate_audio(audio, file_path)

            audio_duration = len(audio) / sample_rate
            logger.info(f"Audio length: {audio_duration:.2f} seconds")

            # Create focus prompt with keywords if enabled
            focus_prompt = TranscriptionService._build_focus_prompt(keywords)

            # Split audio into overlapping segments
            segments = TranscriptionService._create_segments(audio, sample_rate)
            logger.info(f"Split audio into {len(segments)} segments for processing")

            # Process all segments for all languages
            all_results = TranscriptionService._process_segments(
                segments,
                model,
                languages,
                focus_prompt,
                sample_rate
            )

            # Combine segments into final transcriptions
            transcriptions = TranscriptionService._combine_transcriptions(all_results, languages)

            # Clean up temporary files
            if pre_process_file or current_app.config.get('AUDIO_ENABLE_PREPROCESSING', False):
                os.remove(audio_file_path)

            return {
                "transcriptions": transcriptions,
                "segments": all_results,
            }

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

    @staticmethod
    def _prepare_audio(file_path: str, pre_process_file: bool) -> Tuple[str, int]:
        """Prepare audio file for transcription and return its path and sample rate."""
        sample_rate = AudioConfig().get('sample_rate')

        if pre_process_file or current_app.config.get('AUDIO_ENABLE_PREPROCESSING', False):
            logger.info("Starting audio preprocessing")
            audio_file_path = PreprocessingService.preprocess_audio(file_path)
        else:
            logger.info("Audio preprocessing is disabled")
            audio_file_path = file_path

        return audio_file_path, sample_rate

    @staticmethod
    def _validate_audio(audio: Any, file_path: str) -> None:
        """Validate audio is not silent, raise appropriate error if it is."""
        if PreprocessingService.detect_silence(audio):
            logger.warning("Audio appears to be silent - transcription may not be meaningful")
            os.remove(file_path)
            raise ValueError("Silent audio detected")

    @staticmethod
    def _build_focus_prompt(keywords: List[str]) -> str:
        """Build a focus prompt from TranscriptionConfig and keywords."""
        config = TranscriptionConfig()
        focus_prompt = config.get('helper_prompt', '')

        if keywords and config.get('add_keywords', False):
            focus_prompt += f" {' '.join(keywords)}"

        logger.info(f"Focus prompt: {focus_prompt}")
        return focus_prompt

    @staticmethod
    def _create_segments(audio: Any, sample_rate: int) -> List[Tuple[int, Any]]:
        """Create overlapping segments from the audio for processing."""
        segment_length = 15 * sample_rate
        overlap = 7 * sample_rate

        segments = []
        for start in range(0, len(audio), segment_length - overlap):
            end = min(start + segment_length, len(audio))
            segment = audio[start:end]
            segments.append((start, segment))

            # If we've reached the end of the audio, break
            if end == len(audio):
                break

        return segments

    @staticmethod
    def _process_segments(
            segments: List[Tuple[int, Any]],
            model: Any,
            languages: List[str],
            focus_prompt: str,
            sample_rate: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Process all segments for all requested languages."""
        # Initialize results dictionary
        all_results = {lang: [] for lang in languages}

        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")


        use_fp16 = torch.cuda.is_available()
        logger.info(f"Using fp16: {use_fp16}")

        # Get model name for logging
        model_name = getattr(model, 'name', str(type(model)))
        logger.info(f"Using model: {model_name}")

        # Process each segment
        for i, (start_sample, segment) in enumerate(segments):
            logger.info(f"Processing segment {i + 1}/{len(segments)}")
            start_time = start_sample / sample_rate

            # Process for each language
            for lang_idx, language in enumerate(languages):
                # Create transcription options
                options = {
                    "language": language,
                    "temperature": 0.5,
                    "beam_size": 10,
                    "max_initial_timestamp": 1.0,
                    "word_timestamps": True,
                    "fp16": use_fp16,
                    "initial_prompt": focus_prompt
                }

                # Transcribe segment
                result = model.transcribe(segment, **options)

                # Create segment result with timing info
                segment_result = TranscriptionService._create_segment_result(
                    result, start_time, segment, sample_rate
                )

                all_results[language].append(segment_result)

        return all_results

    @staticmethod
    def _create_segment_result(
            result: Dict[str, Any],
            start_time: float,
            segment: Any,
            sample_rate: int
    ) -> Dict[str, Any]:
        """Create a structured result for a segment with timing information."""
        segment_result = {
            "text": result["text"].strip(),
            "start": start_time,
            "end": start_time + (len(segment) / sample_rate),
            "confidence": result.get("avg_logprob", 0)
        }

        # Extract word-level timestamps if available
        if "words" in result and result["words"]:
            segment_result["words"] = [
                {
                    "word": word_info["word"],
                    "start": start_time + word_info["start"],
                    "end": start_time + word_info["end"],
                    "confidence": word_info.get("confidence", 0)
                }
                for word_info in result["words"]
            ]

        return segment_result

    @staticmethod
    def _combine_transcriptions(
            all_results: Dict[str, List[Dict[str, Any]]],
            languages: List[str]
    ) -> Dict[str, str]:
        """Combine segment transcriptions into full text for each language."""
        transcriptions = {}

        for lang in languages:
            # Join all segments with appropriate spacing
            full_text = " ".join([segment["text"] for segment in all_results[lang]])
            # Clean up any double spaces
            full_text = " ".join(full_text.split())
            transcriptions[lang] = full_text

        logger.info("Segments combined into full transcriptions")
        return transcriptions
import os
from typing import List, Dict, Any, Optional, Tuple
import torch
import whisper
from flask import current_app
from logging import getLogger

from app.config import AudioConfig, TranscriptionConfig
from app.exceptions import SilenceError
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
            focus_tokens: Optional[List[str]] = None,
            pre_process_file: bool = False
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file using the provided model with support for multiple languages.

        Args:
            file_path: Path to the audio file
            model: Whisper model instance
            languages: List of language codes to transcribe into
            keywords: List of keywords to enhance recognition accuracy (also used for spotting)
            focus_tokens: Additional bias tokens injected into the prompt (request-level)
            pre_process_file: Whether to preprocess the audio file

        Returns:
            Dictionary containing transcriptions and detailed segment information
        """
        audio = whisper.load_audio(file_path)
        TranscriptionService._validate_audio(audio, file_path)

        audio_file_path, sample_rate, processed_audio = TranscriptionService._prepare_audio(
            file_path, audio, pre_process_file
        )

        audio_duration = len(processed_audio) / sample_rate
        logger.info(f"Audio length: {audio_duration:.2f} seconds")

        focus_prompt = TranscriptionService._build_focus_prompt(keywords, focus_tokens or [])

        segments = TranscriptionService._create_segments(processed_audio, sample_rate)
        logger.info(f"Split audio into {len(segments)} segments for processing")

        all_results = TranscriptionService._process_segments(
            segments,
            model,
            languages,
            focus_prompt,
            sample_rate
        )

        # Combine segments into final transcriptions
        transcriptions = TranscriptionService._combine_transcriptions(all_results, languages)

        if audio_file_path != file_path and os.path.exists(audio_file_path):
            os.remove(audio_file_path)

        return {
            "transcriptions": transcriptions,
            "segments": all_results,
        }

    @staticmethod
    def _prepare_audio(file_path: str, audio: Any, pre_process_file: bool) -> Tuple[str, int, Any]:
        """
        Prepare audio file for transcription and return its path, sample rate, and processed audio.
        Only preprocesses if enabled and audio is not silent.
        """
        sample_rate = AudioConfig().get('sample_rate')
        processed_audio = audio

        should_preprocess = pre_process_file or current_app.config.get('AUDIO_ENABLE_PREPROCESSING', False)

        if should_preprocess:
            logger.info("Starting audio preprocessing")
            audio_file_path = PreprocessingService.preprocess_audio(file_path)
            processed_audio = whisper.load_audio(audio_file_path)
        else:
            logger.info("Audio preprocessing is disabled")
            audio_file_path = file_path

        return audio_file_path, sample_rate, processed_audio

    @staticmethod
    def _validate_audio(audio: Any, file_path: str) -> None:
        """Validate audio is not silent, raise appropriate error if it is."""
        if PreprocessingService.detect_silence(audio):
            logger.warning("Audio appears to be silent - transcription may not be meaningful")
            raise SilenceError()

    @staticmethod
    def _build_focus_prompt(keywords: List[str], focus_tokens: List[str]) -> str:
        """Build a focus prompt from TranscriptionConfig and keywords."""
        config = TranscriptionConfig()
        focus_prompt = config.get('helper_prompt', '')

        if keywords and config.get('add_keywords', False):
            focus_prompt += f" {' '.join(keywords)}"

        # Add abstract focus tokens to the prompt (request overrides config)
        tokens = (focus_tokens or []) or config.get('focus_tokens', [])
        if tokens:
            # Append tokens directly to leverage Whisper's initial_prompt biasing
            focus_prompt += f" {' '.join(tokens)}"

        logger.info(f"Focus prompt: {focus_prompt}")
        return focus_prompt

    @staticmethod
    def _create_segments(audio: Any, sample_rate: int) -> List[Tuple[int, Any]]:
        """Create overlapping segments from the audio for processing."""
        cfg = TranscriptionConfig()
        segment_length = cfg.get('segment_length_sec', 15) * sample_rate
        overlap = cfg.get('segment_overlap_sec', 5) * sample_rate

        if len(audio) == 0:
            logger.warning("Audio length is zero, returning empty segments list")
            return []

        segments = []
        for start in range(0, len(audio), max(1, segment_length - overlap)):
            end = min(start + segment_length, len(audio))
            segment = audio[start:end]
            # Optionally skip clearly silent segments to save time
            if TranscriptionConfig().get('skip_silent_segments', True):
                try:
                    if PreprocessingService.detect_silence(segment):
                        continue
                except Exception:
                    # Be conservative: if silence detection fails, don't skip
                    pass
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
        """Process all segments for all requested languages with proper resource management."""
        all_results = {lang: [] for lang in languages}

        if not segments:
            logger.warning("No segments to process")
            return all_results

        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        use_fp16 = device == 'cuda'
        try:
            cuda_ver = getattr(torch.version, 'cuda', None)
        except Exception:
            cuda_ver = None
        logger.info(f"Using device: {device} | fp16: {use_fp16} | CUDA: {cuda_ver}")

        model_name = getattr(model, 'name', str(type(model)))
        logger.info(f"Using model: {model_name}")

        for i, (start_sample, segment) in enumerate(segments):
            logger.info(f"Processing segment {i + 1}/{len(segments)}")
            start_time = start_sample / sample_rate

            if use_fp16 and i > 0:  # Skip first segment as memory was likely cleaned before
                try:
                    torch.cuda.empty_cache()
                except Exception as e:
                    logger.warning(f"Error cleaning GPU cache: {str(e)}")

            # Process for each language
            for lang_idx, language in enumerate(languages):
                try:
                    cfg = TranscriptionConfig()
                    options = {
                        "language": language,
                        "task": cfg.get('task', 'transcribe'),
                        "temperature": cfg.get('temperature', 0.0),
                        "beam_size": cfg.get('beam_size', 1),
                        "best_of": cfg.get('best_of', 1),
                        "max_initial_timestamp": cfg.get('max_initial_timestamp', 1.0),
                        "word_timestamps": cfg.get('word_timestamps', False),
                        "condition_on_previous_text": cfg.get('condition_on_previous_text', False),
                        "no_speech_threshold": cfg.get('no_speech_threshold', 0.6),
                        "compression_ratio_threshold": cfg.get('compression_ratio_threshold', 2.4),
                        "fp16": use_fp16,
                        "initial_prompt": focus_prompt,
                    }

                    with torch.no_grad():
                        result = model.transcribe(segment, **options)

                    # Create segment result with timing info
                    segment_result = TranscriptionService._create_segment_result(
                        result, start_time, segment, sample_rate
                    )

                    all_results[language].append(segment_result)

                    del result

                except Exception as e:
                    logger.error(f"Error processing segment {i + 1} for language {language}: {str(e)}")
                    # Add empty segment to maintain sequence
                    all_results[language].append({
                        "text": "",
                        "start": start_time,
                        "end": start_time + (len(segment) / sample_rate),
                        "confidence": 0,
                        "error": str(e)
                    })

                    if use_fp16:
                        try:
                            torch.cuda.empty_cache()
                        except Exception as cleanup_error:
                            logger.warning(f"Error cleaning GPU cache after error: {str(cleanup_error)}")

        if use_fp16:
            try:
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            except Exception as e:
                logger.warning(f"Error in final GPU cleanup: {str(e)}")

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
            "text": result.get("text", "").strip(),
            "start": start_time,
            "end": start_time + (len(segment) / sample_rate),
            "confidence": result.get("avg_logprob", 0)
        }

        if "words" in result and result["words"]:
            segment_result["words"] = [
                {
                    "word": word_info.get("word", ""),
                    "start": start_time + word_info.get("start", 0),
                    "end": start_time + word_info.get("end", 0),
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
            full_text = " ".join([segment.get("text", "") for segment in all_results[lang]])
            full_text = " ".join(full_text.split())
            transcriptions[lang] = full_text

        logger.info("Segments combined into full transcriptions")
        return transcriptions

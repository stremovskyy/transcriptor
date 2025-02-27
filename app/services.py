import time
import traceback

import whisper
import signal
from typing import List, Dict, Any
from rapidfuzz import process, fuzz
from logging import getLogger

logger = getLogger(__name__)


class TranscriptionService:
    @staticmethod
    def transcribe_audio(
            file_path: str,
            model: Any,
            languages: List[str] = ['Ukrainian'],
            keywords: List[str] = [],
            confidence_threshold: int = 80
    ) -> Dict[str, Any]:
        try:
            # Load audio
            logger.info(f"Loading audio file: {file_path}")
            audio = whisper.load_audio(file_path)
            audio_duration = len(audio) / 16000  # Convert to seconds
            logger.info(f"Audio length: {audio_duration:.2f} seconds")

            # Get model name for logging
            model_name = getattr(model, 'name', str(type(model)))
            logger.info(f"Using model: {model_name}")

            # Manually segment the audio to ensure the entire content is processed
            # The default context size for Whisper is around 30 seconds
            segment_length = 25 * 16000  # 25 seconds at 16kHz, with overlap
            overlap = 5 * 16000  # 5 seconds overlap

            # Create segments with overlap
            segments = []
            for start in range(0, len(audio), segment_length - overlap):
                end = min(start + segment_length, len(audio))
                segment = audio[start:end]
                segments.append((start, segment))

                # If we've reached the end of the audio, break
                if end == len(audio):
                    break

            logger.info(f"Split audio into {len(segments)} segments for processing")

            # Process each segment and combine results
            all_results = {}
            for lang in languages:
                all_results[lang] = []

            for i, (start_sample, segment) in enumerate(segments):
                logger.info(f"Processing segment {i + 1}/{len(segments)}")

                # Process for primary language
                result = model.transcribe(
                    segment,
                    language=languages[0] if languages else None,
                    temperature=0.7,
                    beam_size=3,
                    fp16=False
                )

                # Calculate start time in seconds
                start_time = start_sample / 16000

                # Add segment results with timing info
                all_results[languages[0]].append({
                    "text": result["text"],
                    "start": start_time,
                    "end": start_time + (len(segment) / 16000)
                })

                # Process additional languages if provided
                if len(languages) > 1:
                    for language in languages[1:]:
                        lang_result = model.transcribe(
                            segment,
                            language=language,
                            temperature=0.7,
                            beam_size=3,
                            fp16=False
                        )

                        all_results[language].append({
                            "text": lang_result["text"],
                            "start": start_time,
                            "end": start_time + (len(segment) / 16000)
                        })

            # Combine segments into final transcriptions
            transcriptions = {}
            for lang in languages:
                # Join all segments with appropriate spacing
                full_text = " ".join([segment["text"].strip() for segment in all_results[lang]])
                # Clean up any double spaces
                full_text = " ".join(full_text.split())
                transcriptions[lang] = full_text

            logger.info("Segments combined into full transcriptions")

            # Process keywords if provided
            keyword_spots = {lang: {keyword: [] for keyword in keywords} for lang in languages}

            if keywords:
                logger.info(f"Processing keywords: {keywords}")
                for language in languages:
                    # Process keywords in each segment for more accurate time marks
                    for segment_data in all_results[language]:
                        segment_text = segment_data["text"]
                        segment_start = segment_data["start"]
                        segment_duration = segment_data["end"] - segment_data["start"]

                        words = segment_text.split()

                        for keyword in keywords:
                            matches = process.extract(
                                keyword,
                                words,
                                scorer=fuzz.ratio,
                                limit=10
                            )

                            for word, score, index in matches:
                                if score >= confidence_threshold:
                                    # Calculate time relative to segment
                                    relative_time = (index / len(words)) * segment_duration
                                    # Add segment start time for absolute position
                                    absolute_time = segment_start + relative_time

                                    keyword_spots[language][keyword].append({
                                        'word': word,
                                        'confidence': score,
                                        'time_mark': round(absolute_time, 2),
                                        'context': ' '.join(
                                            words[max(0, index - 2):min(len(words), index + 3)]
                                        )
                                    })

            return {
                "transcriptions": transcriptions,
                "keyword_spots": keyword_spots
            }

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise RuntimeError(f"Transcription failed: {e}")


class TextReconstructionService:
    @staticmethod
    def reconstruct_text(transcription, template, model, tokenizer, max_length=1500):
        try:
            messages = [{
                "role": "user",
                "content": (
                    f"Виправте помилки в тексті отриманому зі STT (Whisper) Українською мовою.\n"
                    f"Виправляйте очевидні помилки розпізнавання мовлення. Не додавайте форматування, коментарів чи додаткової інформації.\n"
                    f"STT текст для виправлення:\n{transcription}\n\n"
                    f"Результат має містити ВИКЛЮЧНО виправлений текст без будь-яких додатків."
                )
            }]
            prompt = tokenizer.apply_chat_template(messages, tokenize=False)

            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            input_length = inputs.input_ids.shape[1]

            # Generate text
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=max_length,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                repetition_penalty=1.1,
            )

            # Extract only new tokens
            generated_ids = outputs[:, input_length:]
            reconstructed_text = tokenizer.decode(generated_ids[0], skip_special_tokens=True)

            return {
                "original_transcription": transcription,
                "template": template,
                "reconstructed_text": reconstructed_text.strip()
            }

        except Exception as e:
            logger.error(f"Text reconstruction error: {e}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Text reconstruction failed: {e}")

def logging_callback(step, token_id, scores):
    if step % 10 == 0:
        logger.info(f"Generation step: {step}")
    return False
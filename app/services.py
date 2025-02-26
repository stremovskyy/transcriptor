import whisper
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
            logger.info(f"Audio length: {len(audio) / 16000:.2f} seconds")

            # Get model name for logging
            model_name = getattr(model, 'name', str(type(model)))
            logger.info(f"Using model: {model_name}")

            # This avoids potential dimension mismatches
            logger.info("Starting transcription with Whisper")
            result = model.transcribe(
                audio,
                language=languages[0] if languages else None,
                temperature=0.7,
                beam_size=3
            )

            transcriptions = {languages[0]: result["text"]}

            # For multiple languages, process each additionally
            if len(languages) > 1:
                for language in languages[1:]:
                    lang_result = model.transcribe(
                        audio,
                        language=language,
                        temperature=0.7,
                        beam_size=3
                    )
                    transcriptions[language] = lang_result["text"]

            # Process keywords if provided
            keyword_spots = {lang: {keyword: [] for keyword in keywords} for lang in languages}

            if keywords:
                logger.info(f"Processing keywords: {keywords}")
                for language in languages:
                    text = transcriptions[language]
                    words = text.split()

                    for keyword in keywords:
                        matches = process.extract(
                            keyword,
                            words,
                            scorer=fuzz.ratio,
                            limit=10
                        )

                        for word, score, index in matches:
                            if score >= confidence_threshold:
                                approx_time = (index / len(words)) * (len(audio) / 16000)

                                keyword_spots[language][keyword].append({
                                    'word': word,
                                    'confidence': score,
                                    'time_mark': round(approx_time, 2),
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

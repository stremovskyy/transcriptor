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
            audio = whisper.load_audio(file_path)

            SAMPLE_RATE = 16000
            CHUNK_SIZE = 26 * SAMPLE_RATE  # ~30 seconds

            chunks = [audio[i:i + CHUNK_SIZE] for i in range(0, len(audio), CHUNK_SIZE)]

            transcriptions = {language: [] for language in languages}
            keyword_spots = {lang: {keyword: [] for keyword in keywords} for lang in languages}

            for chunk_index, chunk in enumerate(chunks):
                chunk = whisper.pad_or_trim(chunk)
                mel = whisper.log_mel_spectrogram(chunk).to(model.device)

                for language in languages:
                    options = whisper.DecodingOptions(
                        language=language,
                        temperature=0.7,
                        beam_size=3,
                        patience=0.8
                    )

                    result = whisper.decode(model, mel, options)
                    transcriptions[language].append(result.text)

                    words = result.text.split()
                    chunk_start_time = chunk_index * 30

                    for keyword in keywords:
                        matches = process.extract(
                            keyword,
                            words,
                            scorer=fuzz.ratio,
                            limit=3
                        )

                        for word, score, index in matches:
                            if score >= confidence_threshold:
                                keyword_spots[language][keyword].append({
                                    'word': word,
                                    'confidence': score,
                                    'time_mark': chunk_start_time + (index * 0.5),
                                    'context': ' '.join(
                                        words[max(0, index - 2):index + 3]
                                    )
                                })

            return {
                "transcriptions": {
                    lang: ' '.join(transcriptions[lang]).strip()
                    for lang in transcriptions
                },
                "keyword_spots": keyword_spots
            }

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise RuntimeError(f"Transcription failed: {e}")

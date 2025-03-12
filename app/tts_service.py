import io
import logging
import time
import re
import torch
from pathlib import Path
from num2words import num2words
from scipy.io.wavfile import write as write_wav
import os
import numpy as np

# Import Coqui TTS (open source TTS toolkit)
from TTS.utils.synthesizer import Synthesizer
from TTS.utils.manage import ModelManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TTSService:
    def __init__(self, default_lang='uk', models_path=None):
        """
        Initialize a local TTS service with Ukrainian language support using Coqui TTS.

        Args:
            default_lang (str): Default language code ('uk' for Ukrainian)
            models_path (str): Path to store/access TTS models
        """
        # If models_path not provided, use a default location within the app
        if models_path is None:
            # Use a directory in the user's home folder to store models
            models_path = os.path.join(os.path.expanduser("~"), ".tts_models")

        self.default_lang = default_lang
        self.models_path = Path(models_path)
        self.models_path.mkdir(exist_ok=True, parents=True)

        # Configure supported languages and their properties
        self.supported_langs = {
            'uk': {
                'name': 'Ukrainian',
                'numerals': True,
                'abbreviations': True,
                'special_chars': True,
                'model_name': 'tts_models/uk/mai/glow-tts',
                'vocoder_name': 'vocoder_models/universal/libri-tts/fullband-melgan'
            },
            'en': {
                'name': 'English',
                'numerals': True,
                'abbreviations': False,
                'special_chars': False,
                'model_name': 'tts_models/en/ljspeech/tacotron2-DDC',
                'vocoder_name': 'vocoder_models/en/ljspeech/hifigan_v2'
            }
        }

        # Initialize model manager and synthesizers for each language
        self.model_manager = ModelManager()
        self.synthesizers = {}

        # Initialize synthesizer for default language
        logger.info(f"TTSService initialized with default language: {default_lang}")

    def _init_synthesizer(self, lang):
        """Initialize and load the TTS model for the specified language"""
        if lang not in self.supported_langs:
            raise ValueError(f"Language '{lang}' is not supported")

        if lang not in self.synthesizers:
            lang_config = self.supported_langs[lang]
            logger.info(f"Initializing {lang_config['name']} TTS model...")

            try:
                # Download model if not available locally
                model_result = self.model_manager.download_model(lang_config['model_name'])
                vocoder_result = self.model_manager.download_model(lang_config['vocoder_name'])

                # Check what's actually returned by download_model
                logger.debug(f"Model result type: {type(model_result)}")
                logger.debug(f"Model result: {model_result}")

                # Extract the actual paths based on the return value structure
                # If it's a tuple, first element is likely the path
                model_path = model_result[0] if isinstance(model_result, tuple) else model_result
                vocoder_path = vocoder_result[0] if isinstance(vocoder_result, tuple) else vocoder_result

                # Similarly for config paths - may need to adjust based on actual return values
                if isinstance(model_result, tuple) and len(model_result) > 1:
                    model_config = model_result[1]  # Assuming second element is config
                else:
                    # Try to find config in the same directory
                    model_dir = os.path.dirname(model_path)
                    model_config = os.path.join(model_dir, "config.json")

                if isinstance(vocoder_result, tuple) and len(vocoder_result) > 1:
                    vocoder_config = vocoder_result[1]
                else:
                    vocoder_dir = os.path.dirname(vocoder_path)
                    vocoder_config = os.path.join(vocoder_dir, "config.json")

                # Check the current version of TTS to use the right constructor
                # For newer versions of TTS library, use the updated constructor syntax
                try:
                    # Check if TTS.__version__ is available or use a different method
                    import TTS
                    tts_version = getattr(TTS, "__version__", "0.0.0")
                    logger.debug(f"Detected TTS version: {tts_version}")

                    # For newer versions, the constructor has changed
                    self.synthesizers[lang] = Synthesizer(
                        tts_checkpoint=model_path,
                        tts_config_path=model_config,
                        vocoder_checkpoint=vocoder_path,
                        vocoder_config=vocoder_config,
                        use_cuda=torch.cuda.is_available()
                    )
                except (ImportError, AttributeError) as e:
                    # Fallback to alternative constructor if needed
                    logger.debug(f"Using alternative constructor due to: {e}")
                    self.synthesizers[lang] = Synthesizer(
                        tts_checkpoint=model_path,
                        tts_config_path=model_config,
                        vocoder_checkpoint=vocoder_path,
                        vocoder_config=vocoder_config,
                        use_cuda=torch.cuda.is_available()
                    )

                logger.info(f"{lang_config['name']} TTS model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to initialize {lang_config['name']} TTS model: {str(e)}")
                raise

    def _preprocess_ukrainian_text(self, text):
        """
        Preprocess Ukrainian text to improve TTS quality:
        - Convert numbers to words
        - Handle abbreviations
        - Normalize punctuation and special characters
        - Handle special phonetic cases

        Args:
            text (str): The Ukrainian text to preprocess

        Returns:
            str: Preprocessed text optimized for TTS
        """
        logger.debug("Preprocessing Ukrainian text")

        # Convert numbers to Ukrainian words
        def replace_numbers(match):
            num = match.group(0)
            try:
                # Convert numeric string to integer
                return num2words(int(num), lang='uk')
            except:
                return num

        text = re.sub(r'\b\d+\b', replace_numbers, text)

        # Handle common Ukrainian abbreviations
        uk_abbreviations = {
            r'\bт\.д\.': 'так далі',
            r'\bт\.п\.': 'тому подібне',
            r'\bтис\.': 'тисяч',
            r'\bгрн\.': 'гривень',
            r'\bвул\.': 'вулиця',
            r'\bобл\.': 'область',
            r'\bр\.': 'рік',
            r'\bім\.': 'імені',
            r'\bст\.': 'століття',
            r'\bм\.': 'місто',
            r'\bп\.': 'пан',
            r'\bс\.': 'село'
        }

        for abbr, full in uk_abbreviations.items():
            text = re.sub(abbr, full, text)

        # Handle Ukrainian-specific phonetic patterns
        text = re.sub(r'ґ', 'г', text)  # Sometimes TTS struggles with ґ
        text = re.sub(r'(\w)-(\w)', r'\1 \2', text)  # Add space around hyphens in words

        # Add slight pauses around punctuation for better rhythm
        text = re.sub(r'([.,!?;:])', r' \1 ', text)
        text = re.sub(r'\s+', ' ', text).strip()  # Clean up extra spaces

        logger.debug("Ukrainian text preprocessing completed")
        return text

    def _split_into_optimal_chunks(self, text, lang):
        """
        Split text into natural chunks for better TTS quality.

        Args:
            text (str): The text to split
            lang (str): Language code

        Returns:
            list: List of text chunks
        """
        # For Ukrainian, try to split on sentence boundaries
        if lang == 'uk':
            # Split on sentence boundaries
            chunks = re.split(r'(?<=[.!?])\s+', text)
            # Further split very long sentences
            result = []
            for chunk in chunks:
                if len(chunk) > 300:
                    # Try to split on commas or other logical breaks
                    subchunks = re.split(r'(?<=[:;,])\s+', chunk)
                    result.extend(subchunks)
                else:
                    result.append(chunk)
            return [chunk for chunk in result if chunk.strip()]
        else:
            # Default chunking for other languages
            return [text]

    # In app/tts_service.py, update the generate_audio_stream method:

    def generate_audio_stream(self, text, lang=None, chunk_size=4096, voice_speed=1.0, voice_pitch=1.0):
        """
        Generate an audio stream from the provided text using a local TTS model,
        with enhanced support for Ukrainian language.

        Args:
            text (str): The text to convert to speech.
            lang (str, optional): The language code (e.g., 'en', 'uk'). Defaults to self.default_lang.
            chunk_size (int, optional): The size of data chunks to yield. Defaults to 4096 bytes.
            voice_speed (float, optional): Speed multiplier for voice (1.0 is normal).
            voice_pitch (float, optional): Pitch adjustment for voice (1.0 is normal).

        Yields:
            bytes: Chunks of audio data.
        """
        start_time = time.time()
        lang = lang or self.default_lang

        # Default to Ukrainian if not specified or not supported
        if lang not in self.supported_langs:
            logger.warning(
                f"Language '{lang}' not specifically supported. Defaulting to Ukrainian.")
            lang = 'uk'

        # Ensure the synthesizer for this language is initialized
        if lang not in self.synthesizers:
            self._init_synthesizer(lang)

        try:
            logger.info(f"Starting local TTS generation for {len(text)} characters in language '{lang}'")

            # Apply Ukrainian-specific preprocessing if needed
            if lang == 'uk':
                text = self._preprocess_ukrainian_text(text)
                logger.info("Applied Ukrainian-specific text preprocessing")

            # Split into optimal chunks for better speech synthesis
            text_chunks = self._split_into_optimal_chunks(text, lang)
            logger.debug(f"Split text into {len(text_chunks)} optimal chunks")

            # Process each chunk and combine into a single audio stream
            all_audio = io.BytesIO()

            for i, chunk in enumerate(text_chunks):
                if not chunk.strip():
                    continue

                logger.debug(f"Processing chunk {i + 1}/{len(text_chunks)}")

                # Generate audio using the appropriate synthesizer
                synthesizer = self.synthesizers[lang]

                # Generate speech
                outputs = synthesizer.tts(chunk)

                # Ensure outputs is a numpy array with correct dimensionality
                if isinstance(outputs, list):
                    outputs = np.array(outputs)

                # Make sure the data type is float32 for librosa processing
                outputs = outputs.astype(np.float32)

                # Apply voice speed adjustment if needed (safely)
                if voice_speed != 1.0 and 0.5 <= voice_speed <= 2.0:
                    try:
                        import librosa
                        # librosa time_stretch expects a 1D array
                        if len(outputs.shape) == 1:
                            outputs = librosa.effects.time_stretch(outputs, rate=1.0 / voice_speed)
                        else:
                            logger.warning(f"Skipping time stretch - unexpected shape: {outputs.shape}")
                    except Exception as e:
                        logger.warning(f"Voice speed adjustment failed: {str(e)}")

                # Apply voice pitch adjustment if needed (safely)
                if voice_pitch != 1.0 and 0.5 <= voice_pitch <= 2.0:
                    try:
                        import librosa
                        # librosa pitch_shift expects a 1D array
                        if len(outputs.shape) == 1:
                            outputs = librosa.effects.pitch_shift(
                                outputs,
                                sr=synthesizer.output_sample_rate,
                                n_steps=2 * (voice_pitch - 1.0)  # More conservative pitch shift
                            )
                        else:
                            logger.warning(f"Skipping pitch shift - unexpected shape: {outputs.shape}")
                    except Exception as e:
                        logger.warning(f"Voice pitch adjustment failed: {str(e)}")

                # Normalize audio to avoid clipping
                max_val = np.max(np.abs(outputs))
                if max_val > 0:
                    outputs = outputs / max_val * 0.9

                # Make sure outputs is in the expected format for write_wav
                # scipy.io.wavfile.write expects 16-bit PCM
                if outputs.dtype != np.int16:
                    outputs = np.int16(outputs * 32767)

                # Convert to WAV in memory
                wav_io = io.BytesIO()
                write_wav(wav_io, synthesizer.output_sample_rate, outputs)
                wav_io.seek(0)

                # Append to the combined audio
                all_audio.write(wav_io.read())

            # Reset the pointer for reading
            all_audio.seek(0)

            # Stream the combined audio data
            bytes_sent = 0
            while True:
                chunk = all_audio.read(chunk_size)
                if not chunk:
                    break
                bytes_sent += len(chunk)
                yield chunk

            processing_time = time.time() - start_time
            logger.info(
                f"Local {self.supported_langs[lang]['name']} TTS streaming completed. "
                f"Total bytes: {bytes_sent}, Processing time: {processing_time:.2f}s")

        except Exception as e:
            logger.exception(f"Error generating local TTS audio stream: {str(e)}")
            raise e

    def generate_wav_file(self, text, output_path, lang=None, voice_speed=1.0, voice_pitch=1.0):
        """
        Generate a WAV file from the provided text.

        Args:
            text (str): The text to convert to speech
            output_path (str): Path to save the WAV file
            lang (str, optional): Language code. Defaults to default_lang.
            voice_speed (float): Speed multiplier (1.0 is normal)
            voice_pitch (float): Pitch adjustment (1.0 is normal)

        Returns:
            str: Path to the generated file
        """
        # Collect all audio chunks into a single file
        with open(output_path, 'wb') as f:
            for chunk in self.generate_audio_stream(
                    text, lang=lang, voice_speed=voice_speed, voice_pitch=voice_pitch
            ):
                f.write(chunk)

        return output_path

    def get_available_languages(self):
        """
        Get list of available languages

        Returns:
            dict: Dictionary of supported languages and their properties
        """
        return {k: v['name'] for k, v in self.supported_langs.items()}
from flask import current_app
import os
import torch
import torchaudio
import logging
import uuid
from pathlib import Path
try:
    import omegaconf
except ImportError:
    omegaconf = None

class TTSService:
    """
    Text-to-Speech service using Silero TTS models.
    Silero TTS is chosen because it's lightweight and can run completely locally without internet connection.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.current_language = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.models_dir = os.path.join(os.getcwd(), 'tts_models')
        self.output_dir = os.path.join(os.getcwd(), 'static', 'audio')

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Available voices for supported languages with their Silero speaker IDs
        self.voices = {
            'ua': {
                'mykyta': 'mykyta_v2',  # Ukrainian male voice
                'olena': 'v4_ua'        # Ukrainian female voice
            },
            'en': {
                'en_0': 'v3_en',        # English voice
            }
        }

        # Model configurations for different languages
        self.model_configs = {
            'ua': {'repo_id': 'snakers4/silero-models', 'model': 'silero_tts'},
            'en': {'repo_id': 'snakers4/silero-models', 'model': 'silero_tts_en'}
        }

        self.logger.info(f"TTSService initialized. Using device: {self.device}")

    def load_model(self, language='ua'):
        """Load the Silero TTS model for the specified language if not already loaded."""
        # If model is already loaded for the requested language, return True
        if self.model is not None and self.current_language == language:
            self.logger.info(f"Model already loaded for language: {language}")
            return True

        # Reset model to ensure we don't use a partially loaded model
        self.model = None
        self.current_language = None

        try:
            self.logger.info(f"Loading Silero TTS model for language: {language}")

            # Check if omegaconf is available
            if omegaconf is None:
                self.logger.error("Failed to load Silero TTS model: 'omegaconf' module is missing. Please install it with 'pip install omegaconf'")
                return False

            # Validate language
            if language not in self.voices:
                self.logger.error(f"Language {language} not in the supported list: {list(self.voices.keys())}")
                return False

            try:
                # Get model configuration for the language
                config = self.model_configs[language]

                # Load model based on language
                if language == 'ua':
                    # For Ukrainian, use the default model with speaker
                    model = torch.hub.load(
                        repo_or_dir=config['repo_id'],
                        model=config['model'],
                        language='ua',
                        speaker='mykyta_v2'
                    )
                else:  # English
                    # For English, use the English-specific model
                    model = torch.hub.load(
                        repo_or_dir=config['repo_id'],
                        model=config['model'],
                        language='en'
                    )

            except Exception as e:
                self.logger.error(f"Failed to load model from torch hub: {str(e)}")
                # Try loading from local cache
                cache_dir = os.path.expanduser("~/.cache/torch/hub/snakers4_silero-models_master")
                if os.path.exists(cache_dir):
                    try:
                        if language == 'ua':
                            model = torch.hub.load(
                                repo_or_dir=cache_dir,
                                model=config['model'],
                                language='ua',
                                speaker='mykyta_v2',
                                source='local'
                            )
                        else:  # English
                            model = torch.hub.load(
                                repo_or_dir=cache_dir,
                                model=config['model'],
                                language='en',
                                source='local'
                            )
                    except Exception as e:
                        self.logger.error(f"Failed to load model from local cache: {str(e)}")
                        return False
                else:
                    self.logger.error("Local cache directory not found")
                    return False

            if model is None:
                self.logger.error("Model loading returned None")
                return False

            # Handle the case where torch.hub.load returns a tuple
            if isinstance(model, tuple):
                self.logger.info("Model returned as tuple, extracting model object")
                # Typically, the first element in the tuple is the model
                model_obj = model[0]
            else:
                model_obj = model

            self.model = model_obj.to(self.device)
            self.current_language = language
            self.logger.info(f"Silero TTS model loaded successfully for language: {language}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load Silero TTS model: {str(e)}")
            self.model = None  # Reset model on error
            return False

    def text_to_speech(self, text, language='ua', voice=None):
        """
        Convert text to speech and return the path to the generated audio file.

        Args:
            text (str): The text to convert to speech
            language (str): The language code ('ua' for Ukrainian, 'en' for English)
            voice (str, optional): The voice ID to use. If None, uses the first available voice for the language.

        Returns:
            str: Path to the generated audio file
        """
        # Validate language
        if language not in self.voices:
            self.logger.error(f"Language {language} not in the supported list: {list(self.voices.keys())}")
            raise Exception(f"Language not in the supported list {list(self.voices.keys())}")

        # Try to load the model
        if not self.load_model(language):
            raise Exception("Failed to load TTS model")

        # Double-check that the model is actually loaded
        if self.model is None:
            self.logger.error("Model is None after successful load_model call")
            raise Exception("TTS model is not loaded properly")

        # Get the actual Silero speaker ID
        if voice is None:
            speaker = list(self.voices[language].values())[0]
        else:
            if voice not in self.voices[language]:
                self.logger.warning(f"Voice {voice} not found for language {language}, using default voice")
                speaker = list(self.voices[language].values())[0]
            else:
                speaker = self.voices[language][voice]

        try:
            # Generate a unique filename
            filename = f"{uuid.uuid4()}.mp3"
            output_path = os.path.join(self.output_dir, filename)

            self.logger.info(f"Generating speech for text: {text[:50]}... using speaker {speaker}")

            # Generate speech
            sample_rate = 48000

            # Ensure model is loaded
            if self.model is None:
                self.logger.error("Model is None, cannot generate speech")
                raise Exception("TTS model is not loaded properly")

            # Generate speech using the model
            with torch.no_grad():
                if language == 'ua':
                    audio = self.model.apply_tts(
                        text=text,
                        speaker=speaker,
                        sample_rate=sample_rate
                    )
                else:  # English
                    audio = self.model.apply_tts(
                        text=text,
                        speaker='en_0',  # Use default English speaker
                        sample_rate=sample_rate
                    )

            # Ensure audio is 2D tensor (1, samples)
            if len(audio.shape) == 1:
                audio = audio.unsqueeze(0)

            # Save as MP3
            torchaudio.save(
                output_path,
                audio,
                sample_rate=sample_rate,
                format="mp3"
            )

            self.logger.info(f"Speech generated successfully. Saved to {output_path}")

            # Return the relative path for the frontend
            return os.path.join('audio', filename)

        except Exception as e:
            self.logger.error(f"Error generating speech: {str(e)}")
            raise Exception(f"Failed to generate speech: {str(e)}")

# Singleton instance
tts_service = TTSService()

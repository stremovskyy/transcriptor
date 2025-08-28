import os
import logging
from dotenv import load_dotenv
from app.managers import ConfigManager
from typing import Any

logger = logging.getLogger(__name__)

Version = '1.2.2'

log_handlers = [logging.StreamHandler()]

# Load environment from .env early so logging picks it up
load_dotenv()

LOG_TO_FILE = os.getenv('LOG_TO_FILE', 'false').lower() == 'true'

# Determine environment and desired log level
env = (os.getenv('FLASK_ENV') or os.getenv('APP_ENV') or os.getenv('ENV') or '').lower()
is_prod = env == 'production'

def _parse_level(value: str, default: int) -> int:
    if not value:
        return default
    mapping = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'warn': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
        'notset': logging.NOTSET,
    }
    return mapping.get(value.lower(), default)

if LOG_TO_FILE:
    # Try to create logs directory and file handler when explicitly enabled
    try:
        os.makedirs('logs', exist_ok=True)
        log_handlers.insert(0, logging.FileHandler(
            'logs/transcription_app.log', mode='a', encoding='utf-8', errors='ignore'
        ))
    except Exception as e:
        # Fallback to stdout-only if we cannot write logs to file
        logger.warning(f"File logging disabled due to error: {e}")

# Configure logging with more detailed format.
# In production default to WARNING to reduce console noise.
default_level = logging.WARNING if is_prod else logging.INFO
configured_level = _parse_level(os.getenv('LOG_LEVEL', ''), default_level)

logging.basicConfig(
    level=configured_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers,
)

# logging.getLogger('app.preprocessing').setLevel(logging.DEBUG)
# logging.getLogger('app.transcription').setLevel(logging.DEBUG)
# logging.getLogger('app.models').setLevel(logging.DEBUG)

def str_to_bool(value: str) -> bool:
    return value.lower() in ('true', '1', 't', 'yes', 'y')


def configure_app(app):
    load_dotenv()

    logger.info(f"FLASK_ENV: {os.getenv('FLASK_ENV')}")

    app.config.update(
        UPLOAD_FOLDER=ConfigManager.get_env('UPLOAD_FOLDER', '/tmp'),
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50 MB upload limit
        ALLOWED_EXTENSIONS=set(
            ConfigManager.get_env('ALLOWED_EXTENSIONS', 'mp3').split(',')
        )
    )

    app.config.update(
        APP_VERSION=Version,
        API_KEY_ENABLED=ConfigManager.get_env('API_KEY_ENABLED', 'true').lower() == 'true',
        API_KEY=ConfigManager.get_env('API_KEY', 'default-api-key-change-me'),
        UI_ENABLED=ConfigManager.get_env('UI_ENABLED', 'true').lower() == 'true',
        AUDIO_ENABLE_PREPROCESSING=ConfigManager.get_env('AUDIO_ENABLE_PREPROCESSING', 'true').lower() == 'true'
    )

    # Log configuration (but don't log the API key)
    logger.info(f"API_KEY_ENABLED: {app.config['API_KEY_ENABLED']}")
    logger.info(f"UI_ENABLED: {app.config['UI_ENABLED']}")
    logger.info(f"UPLOAD_FOLDER: {app.config['UPLOAD_FOLDER']}")
    logger.info(f"AUDIO_ENABLE_PREPROCESSING: {app.config['AUDIO_ENABLE_PREPROCESSING']}")

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


class AudioConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        self.settings = {
            'enable_dc_offset': str_to_bool(os.getenv('AUDIO_ENABLE_DC_OFFSET', 'true')),
            'enable_normalization': str_to_bool(os.getenv('AUDIO_ENABLE_NORMALIZATION', 'true')),
            'enable_pre_emphasis': str_to_bool(os.getenv('AUDIO_ENABLE_PRE_EMPHASIS', 'true')),
            'enable_noise_reduction': str_to_bool(os.getenv('AUDIO_ENABLE_NOISE_REDUCTION', 'true')),
            'enable_compression': str_to_bool(os.getenv('AUDIO_ENABLE_COMPRESSION', 'true')),
            'enable_trim_silence': str_to_bool(os.getenv('AUDIO_ENABLE_TRIM_SILENCE', 'true')),
            'pre_emphasis': float(os.getenv('AUDIO_PRE_EMPHASIS', '0.97')),
            'frame_length': int(os.getenv('AUDIO_FRAME_LENGTH', '2048')),
            'hop_length': int(os.getenv('AUDIO_HOP_LENGTH', '512')),
            'noise_threshold': float(os.getenv('AUDIO_NOISE_THRESHOLD', '2.0')),
            'trim_db': float(os.getenv('AUDIO_TRIM_DB', '20.0')),
            'silence_threshold': float(os.getenv('AUDIO_SILENCE_THRESHOLD', '0.01')),
            'sample_rate': int(os.getenv('AUDIO_SAMPLE_RATE', '16000'))
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)



class TranscriptionConfig:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        self.settings = {
            'helper_prompt': str(os.getenv('TRANSCRIPTION_HELPER_PROMPT', '')),
            'add_keywords': str_to_bool(os.getenv('TRANSCRIPTION_ADD_KEYWORDS', '')),
        }

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

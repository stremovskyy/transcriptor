import os
import logging
from dotenv import load_dotenv
from app.managers import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/transcription_app.log', mode='a', encoding='utf-8', errors='ignore'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

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
        API_KEY_ENABLED=ConfigManager.get_env('API_KEY_ENABLED', 'true').lower() == 'true',
        API_KEY=ConfigManager.get_env('API_KEY', 'default-api-key-change-me'),
        UI_ENABLED=ConfigManager.get_env('UI_ENABLED', 'true').lower() == 'true'
    )

    # Log configuration (but don't log the API key)
    logger.info(f"API_KEY_ENABLED: {app.config['API_KEY_ENABLED']}")
    logger.info(f"UI_ENABLED: {app.config['UI_ENABLED']}")

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
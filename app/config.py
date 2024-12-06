import os
import logging
from dotenv import load_dotenv
from app.managers import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/transcription_app.log'),
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

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

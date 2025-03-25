from flask import Flask
from app.config import configure_app
from app.routes import register_routes
from app.models import ModelCache
import warnings
import logging
warnings.simplefilter("ignore", category=FutureWarning)

def create_app():
    app = Flask(__name__)
    configure_app(app)
    register_routes(app)

    # Preload TTS model in a separate thread to avoid blocking app startup
    import threading
    from app.tts import tts_service

    def preload_tts_model():
        logger = logging.getLogger(__name__)
        logger.info("Preloading TTS model...")
        success = tts_service.load_model()
        if success:
            logger.info("TTS model preloaded successfully")
        else:
            logger.warning("Failed to preload TTS model. It will be loaded on first request.")

    # Start preloading in a separate thread
    threading.Thread(target=preload_tts_model, daemon=True).start()

    return app

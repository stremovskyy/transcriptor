from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
import os
import logging
import traceback
import time
from flask import current_app
from app.models import ModelCache
from app.services import TranscriptionService
from app.utils import allowed_file

logger = logging.getLogger(__name__)
routes = Blueprint('routes', __name__)

model_cache = ModelCache()


@routes.route('/')
def index():
    return render_template('index.html')


@routes.route('/preload_model', methods=['POST'])
def preload_model():
    model_type = request.json.get('model', 'base')
    try:
        model_cache.load_model(model_type)
        return jsonify({"status": "Model preloaded successfully"}), 200
    except Exception as e:
        logger.error(f"Model preload error: {e}")
        return jsonify({"error": str(e)}), 500


@routes.route('/transcribe', methods=['POST'])
def transcribe():
    logger.info(f"Transcription request received")
    try:
        if 'file' not in request.files:
            logger.error("No file part in request")
            raise BadRequest("No file uploaded")

        file = request.files['file']

        if file.filename == '':
            logger.error("No filename provided")
            raise BadRequest("No selected file")

        if not allowed_file(file.filename, allowed_extensions=current_app.config['ALLOWED_EXTENSIONS']):
            logger.error("File extension not allowed")
            raise BadRequest("Invalid file type")

        filename = secure_filename(file.filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"Saving file to: {file_path}")

        file.save(file_path)
        logger.info(f"File saved successfully: {file_path}")

        if not os.path.exists(file_path):
            raise RuntimeError("File was not saved correctly")

        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")

        languages = request.form.get('lang', 'Ukrainian,Russian').split(',')
        model_type = request.form.get('model', 'base')
        keywords = request.form.get('keywords', '').split(',') if request.form.get('keywords') else []
        confidence_threshold = int(request.form.get('confidence_threshold', 80))

        if model_type not in model_cache._models:
            model_cache.load_model(model_type)

        logger.info(f"Transcription parameters: "
                    f"languages={languages}, "
                    f"model={model_type}, "
                    f"keywords={keywords}, "
                    f"confidence_threshold={confidence_threshold}")

        start_time = time.time()
        model = model_cache.get_model(model_type)

        if not model:
            logger.error(f"Failed to load {model_type} model")
            raise RuntimeError(f"Failed to load {model_type} model")

        logger.info("Starting audio transcription")
        result = TranscriptionService.transcribe_audio(
            file_path,
            model,
            languages,
            keywords,
            confidence_threshold
        )

        end_time = time.time()
        result['processing_time'] = round(end_time - start_time, 2)

        logger.info(f"Transcription completed in {result['processing_time']} seconds")
        return jsonify(result)

    except RequestEntityTooLarge:
        logger.error("File too large")
        return jsonify({"error": "File too large. Max 50MB."}), 413
    except BadRequest as e:
        logger.error(f"Bad request: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception(f"Transcription error: {e}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500
    finally:
        try:
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file {file_path} removed")
        except Exception as cleanup_error:
            logger.error(f"Error removing file: {cleanup_error}")


def register_routes(app):
    app.register_blueprint(routes)

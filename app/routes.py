from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest, RequestEntityTooLarge
import os
import logging
import traceback
import time
from flask import current_app
from app.models import ModelCache, GemmaModelCache
from app.services import TranscriptionService, TextReconstructionService
from app.utils import allowed_file
from urllib.parse import urlparse
import uuid
import requests

logger = logging.getLogger(__name__)
routes = Blueprint('routes', __name__)

model_cache = ModelCache()
gemma_model_cache = GemmaModelCache()


@routes.route('/')
def index():
    # render template and styles.css
    return render_template('index.html')


@routes.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "Healthy"}), 200


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


@routes.route('/pull', methods=['POST'])
def transcribe_json():
    logger.info("JSON transcription request received")
    try:
        # Parse JSON data
        data = request.get_json()

        if not data:
            logger.error("No JSON data in request")
            raise BadRequest("No JSON data provided")

        # Get required file URL
        file_url = data.get('file_url')
        if not file_url:
            logger.error("No file_url provided in JSON")
            raise BadRequest("Missing file_url parameter")

        # Get optional parameters with defaults
        languages = data.get('languages', ['Ukrainian', 'Russian'])
        if isinstance(languages, str):
            languages = languages.split(',')

        model_type = data.get('model', 'base')
        keywords = data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = keywords.split(',') if keywords else []

        confidence_threshold = int(data.get('confidence_threshold', 80))

        # Download file from URL
        logger.info(f"Attempting to download file from: {file_url}")

        # Generate unique filename
        parsed_url = urlparse(file_url)
        path_parts = parsed_url.path.split('/')
        original_filename = path_parts[-1] if path_parts[-1] else f"audio_{uuid.uuid4().hex}"

        if not original_filename.lower().endswith('.mp3'):
            original_filename += '.mp3'

        filename = secure_filename(original_filename)
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

        # Download the file
        response = requests.get(file_url, stream=True, timeout=30)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses

        # Save the downloaded file
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"File downloaded and saved to: {file_path}")

        # Check if file exists and is valid
        if not os.path.exists(file_path):
            raise RuntimeError("File was not saved correctly")

        file_size = os.path.getsize(file_path)
        logger.info(f"File size: {file_size} bytes")

        if file_size == 0:
            raise BadRequest("Downloaded file is empty")

        # Check if file extension is allowed
        if not allowed_file(filename, allowed_extensions=current_app.config['ALLOWED_EXTENSIONS']):
            logger.error("File extension not allowed")
            os.remove(file_path)
            raise BadRequest("Invalid file type, only MP3 files are supported")

        # Load the model if not already loaded
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
        result['original_url'] = file_url

        logger.info(f"Transcription completed in {result['processing_time']} seconds")
        return jsonify(result)

    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({"error": f"Error downloading file: {str(e)}"}), 400

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


@routes.route('/preload_gemma', methods=['POST'])
def preload_gemma():
    try:
        # Parse JSON data
        data = request.get_json()

        success = gemma_model_cache.load_model(model_id=data.get('model_id', 'google/gemma-2b-it'))
        if success:
            return jsonify({"status": "Gemma2 model preloaded successfully"}), 200
        else:
            return jsonify({"error": "Failed to preload Gemma2 model"}), 500
    except Exception as e:
        logger.error(f"Gemma2 model preload error: {e}")
        return jsonify({"error": str(e)}), 500


@routes.route('/reconstruct', methods=['POST'])
def reconstruct_text():
    logger.info("Text reconstruction request received")
    try:
        # Parse JSON data
        data = request.get_json()

        if not data:
            logger.error("No JSON data in request")
            raise BadRequest("No JSON data provided")

        # Get required parameters
        transcription = data.get('transcription')
        template = data.get('template')
        model_id = data.get('model_id', 'google/gemma-2b-it')

        if not transcription:
            logger.error("No transcription provided in JSON")
            raise BadRequest("Missing transcription parameter")

        if not template:
            logger.error("No template provided in JSON")
            raise BadRequest("Missing template parameter")

        # Load the model if not already loaded
        model, tokenizer = gemma_model_cache.get_model_and_tokenizer(model_id)

        if not model or not tokenizer:
            logger.error("Failed to load Gemma2 model")
            raise RuntimeError("Failed to load Gemma2 model")

        logger.info("Starting text reconstruction")
        start_time = time.time()

        result = TextReconstructionService.reconstruct_text(
            transcription,
            template,
            model,
            tokenizer,
            max_length=int(data.get('max_length', 1500))
        )

        end_time = time.time()
        result['processing_time'] = round(end_time - start_time, 2)

        logger.info(f"Text reconstruction completed in {result['processing_time']} seconds")
        return jsonify(result)

    except BadRequest as e:
        logger.error(f"Bad request: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception(f"Text reconstruction error: {e}")
        return jsonify({"error": str(e), "details": traceback.format_exc()}), 500


def register_routes(app):
    app.register_blueprint(routes)

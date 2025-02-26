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
from app.pre_process import AudioPreprocessor

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
        audio_path = file_path

        file.save(file_path)
        logger.info(f"File saved successfully: {file_path}")

        # Get preprocessing parameters
        pre_process = request.form.get('pre_process', 'false').lower() == 'true'

        if pre_process:
            # Get preprocessing parameters from request
            noise_reduction_strength = float(request.form.get('noise_reduction_strength', 0.5))
            voice_enhancement_strength = float(request.form.get('voice_enhancement_strength', 1.0))
            volume_factor = float(request.form.get('volume_factor', 1.5))
            high_pass_freq = float(request.form.get('high_pass_freq', 50.0))
            low_pass_freq = float(request.form.get('low_pass_freq', 8000.0))
            voice_freq_min = float(request.form.get('voice_freq_min', 300.0))
            voice_freq_max = float(request.form.get('voice_freq_max', 3400.0))
            agc_target_db = float(request.form.get('agc_target_db', -20.0))

            # Initialize preprocessor with custom parameters
            preprocessor = AudioPreprocessor(
                noise_reduction_strength=noise_reduction_strength,
                voice_enhancement_strength=voice_enhancement_strength,
                volume_factor=volume_factor,
                high_pass_freq=high_pass_freq,
                low_pass_freq=low_pass_freq,
                voice_freq_min=voice_freq_min,
                voice_freq_max=voice_freq_max,
                agc_target_db=agc_target_db
            )

            processed_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"processed_{filename}")
            preprocessor.preprocess_audio(file_path, processed_path)
            logger.info(f"File preprocessed successfully: {processed_path}")
            audio_path = processed_path

        if not os.path.exists(audio_path):
            raise RuntimeError("File was not processed correctly")

        file_size = os.path.getsize(audio_path)
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
            audio_path,
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
            # Clean up both original and processed files
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file {file_path} removed")
            if 'processed_path' in locals() and os.path.exists(processed_path):
                os.remove(processed_path)
                logger.info(f"Processed file {processed_path} removed")
        except Exception as cleanup_error:
            logger.error(f"Error removing files: {cleanup_error}")


def register_routes(app):
    app.register_blueprint(routes)

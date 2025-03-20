from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get('API_KEY_ENABLED', False):
            return f(*args, **kwargs)

        api_key = request.headers.get('X-API-Key')

        if not api_key:
            logger.warning("Request without API key detected")
            return jsonify({"error": "Authorization required"}), 401

        if api_key != current_app.config.get('API_KEY'):
            logger.warning(f"Invalid API key provided: {api_key[:5]}...")
            return jsonify({"error": "Invalid Authorization key"}), 403

        return f(*args, **kwargs)

    return decorated_function


def check_ui_enabled(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if UI is enabled
        if not current_app.config.get('UI_ENABLED', True):
            return jsonify({"error": "UI is disabled"}), 403

        return f(*args, **kwargs)

    return decorated_function


def version_header(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)

        if isinstance(response, tuple):
            response_body = response[0]
            status_code = response[1]
            headers = response[2] if len(response) > 2 else {}

            if hasattr(response_body, 'headers'):
                response_body.headers['X-API-Version'] = current_app.config.get('API_VERSION', '1.0')
                response_body.headers['X-App-Version'] = current_app.config.get('APP_VERSION', '1.0')
                return response
            else:
                new_response = jsonify(response_body) if isinstance(response_body, dict) else response_body
                new_response.headers['X-API-Version'] = current_app.config.get('API_VERSION', '1.0')
                new_response.headers['X-App-Version'] = current_app.config.get('APP_VERSION', '1.0')
                return new_response, status_code, headers

        response.headers['X-API-Version'] = current_app.config.get('API_VERSION', '1.0')
        response.headers['X-App-Version'] = current_app.config.get('APP_VERSION', '1.0')
        return response

    return decorated_function
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)


def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if API key validation is enabled
        if not current_app.config.get('API_KEY_ENABLED', False):
            return f(*args, **kwargs)

        # Get the API key from the request headers
        api_key = request.headers.get('X-API-Key')

        # Check if API key is provided and valid
        if not api_key:
            logger.warning("Request without API key detected")
            return jsonify({"error": "Authorization required"}), 401

        # Check if API key is valid
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
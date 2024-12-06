from typing import List, Dict, Optional, Any
import os
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    @staticmethod
    def get_env(key: str, default: Any = None) -> Any:
        value = os.getenv(key, default)

        if key in ['FLASK_PORT', 'CONFIDENCE_THRESHOLD']:
            try:
                return int(value)
            except (ValueError, TypeError):
                logger.warning(f"Invalid value for {key}. Using default: {default}")
                return default

        return value


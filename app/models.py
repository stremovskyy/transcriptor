import os
import time
from logging import getLogger
import traceback
from typing import List, Dict, Optional, Any
import threading
import torch
import whisper

logger = getLogger(__name__)

class ModelCache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._device = 'cuda' if torch.cuda.is_available() else 'cpu'
        return cls._instance

    def load_model(self, model_type: str = 'base') -> Optional[Any]:
        with self._lock:
            if model_type not in self._models:
                try:
                    if torch.cuda.is_available():
                        initial_memory_allocated = torch.cuda.memory_allocated()
                        initial_memory_cached = torch.cuda.memory_cached()
                        logger.info(
                            f"Initial GPU Memory - Allocated: {initial_memory_allocated / 1024 ** 2:.2f} MB, Cached: {initial_memory_cached / 1024 ** 2:.2f} MB")

                    start_time = time.time()

                    logger.info(f"Attempting to load Whisper model: {model_type}")

                    try:
                        model = whisper.load_model(
                            model_type,
                            device=self._device,
                            in_memory=True
                        )
                    except RuntimeError as mem_error:
                        if 'CUDA out of memory' in str(mem_error):
                            logger.error(f"CUDA out of memory when loading {model_type} model")

                            if torch.cuda.is_available():
                                torch.cuda.empty_cache()
                                torch.cuda.synchronize()

                            try:
                                logger.warning(f"Falling back to CPU for {model_type} model")
                                model = whisper.load_model(
                                    model_type,
                                    device='cpu',
                                    in_memory=True
                                )
                            except Exception as fallback_error:
                                logger.error(f"Fallback model loading failed: {fallback_error}")
                                return None
                        else:
                            logger.error(f"Model loading error: {mem_error}")
                            return None

                    load_time = time.time() - start_time
                    logger.info(f"Successfully loaded {model_type} model in {load_time:.2f} seconds")

                    if torch.cuda.is_available():
                        final_memory_allocated = torch.cuda.memory_allocated()
                        final_memory_cached = torch.cuda.memory_cached()
                        memory_used_allocated = (final_memory_allocated - initial_memory_allocated) / 1024 ** 2
                        memory_used_cached = (final_memory_cached - initial_memory_cached) / 1024 ** 2
                        logger.info(f"GPU Memory Usage for {model_type} model - "
                                    f"Allocated: {memory_used_allocated:.2f} MB, "
                                    f"Cached: {memory_used_cached:.2f} MB")

                    self._models[model_type] = model
                    return model

                except Exception as e:
                    logger.error(f"Unexpected error loading {model_type} model: {e}")
                    logger.error(traceback.format_exc())

                    if torch.cuda.is_available():
                        logger.info(f"CUDA Device: {torch.cuda.get_device_name(0)}")
                        logger.info(f"CUDA Device Count: {torch.cuda.device_count()}")
                        logger.info(f"Current CUDA Device: {torch.cuda.current_device()}")

                    return None

            return self._models[model_type]

    def get_model(self, model_type: str = 'base') -> Optional[Any]:
        with self._lock:
            return self._models.get(model_type) or self.load_model(model_type)

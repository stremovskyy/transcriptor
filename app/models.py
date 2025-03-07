from logging import getLogger
from typing import Optional, Any, Tuple
import whisper
import threading
import time
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

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
                    if self._device.startswith('cuda'):
                        initial_allocated = torch.cuda.memory_allocated()
                        initial_reserved = torch.cuda.memory_reserved()
                        logger.info(
                            "Initial GPU Memory - Allocated: {:.2f} MB, Reserved: {:.2f} MB".format(
                                initial_allocated / 1024 ** 2, initial_reserved / 1024 ** 2)
                        )

                    start_time = time.time()
                    logger.info(f"Attempting to load Whisper model: {model_type}")

                    try:
                        model = whisper.load_model(
                            model_type,
                            device=self._device,
                            in_memory=True
                        )
                    except RuntimeError as mem_error:
                        # Обробка помилки переповнення пам'яті GPU
                        if 'CUDA out of memory' in str(mem_error):
                            logger.exception(f"CUDA out of memory when loading {model_type} model")
                            if self._device.startswith('cuda'):
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
                                logger.exception("Fallback model loading failed")
                                return None
                        else:
                            logger.exception("Runtime error during model loading")
                            return None

                    load_time = time.time() - start_time
                    logger.info(f"Successfully loaded {model_type} model in {load_time:.2f} seconds")

                    if self._device.startswith('cuda'):
                        final_allocated = torch.cuda.memory_allocated()
                        final_reserved = torch.cuda.memory_reserved()
                        allocated_diff = (final_allocated - initial_allocated) / 1024 ** 2
                        reserved_diff = (final_reserved - initial_reserved) / 1024 ** 2
                        logger.info(
                            "GPU Memory Usage for {} model - Allocated Increase: {:.2f} MB, Reserved Increase: {:.2f} MB".format(
                                model_type, allocated_diff, reserved_diff)
                        )

                    self._models[model_type] = model
                    return model

                except Exception:
                    logger.exception(f"Unexpected error loading {model_type} model")
                    if self._device.startswith('cuda'):
                        logger.info(f"CUDA Device: {torch.cuda.get_device_name(0)}")
                        logger.info(f"CUDA Device Count: {torch.cuda.device_count()}")
                        logger.info(f"Current CUDA Device: {torch.cuda.current_device()}")
                    return None

            return self._models[model_type]

    def get_model(self, model_type: str = 'base') -> Optional[Any]:
        with self._lock:
            return self._models.get(model_type) or self.load_model(model_type)


class GemmaModelCache:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._model = None
                    cls._instance._tokenizer = None
                    cls._instance._device = 'cuda' if torch.cuda.is_available() else 'cpu'
        return cls._instance

    def load_model(self, model_id: str = "google/gemma-2b-it") -> bool:
        with self._lock:
            if not self._model or not self._tokenizer:
                logger.info("Loading Gemma2 model and tokenizer")
                start_time = time.time()

                try:
                    self._tokenizer = AutoTokenizer.from_pretrained(model_id)

                    if self._device.startswith("cuda"):
                        torch_dtype = torch.float16
                    elif self._device == "mps":
                        torch_dtype = torch.float32
                    else:
                        torch_dtype = torch.float32

                    self._model = AutoModelForCausalLM.from_pretrained(
                        model_id,
                        device_map=None,
                        torch_dtype=torch_dtype
                    )
                    self._model.to(self._device)
                    logger.info(f"Model loaded on {self._device}")
                    return True

                except Exception:
                    logger.exception("Error loading Gemma2 model")
                    return False

                finally:
                    load_time = time.time() - start_time
                    logger.info(f"Model loading time: {load_time:.2f} seconds")

    def get_model_and_tokenizer(self, model_id: str = "google/gemma-2b-it") -> Tuple[Optional[Any], Optional[Any]]:
        if not self._model or not self._tokenizer:
            success = self.load_model(model_id)
            if not success:
                return None, None
        return self._model, self._tokenizer

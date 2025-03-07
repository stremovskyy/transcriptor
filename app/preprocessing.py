import traceback
from functools import lru_cache
from logging import getLogger
from pathlib import Path
from typing import Tuple, Optional

import librosa
import numpy as np
import soundfile as sf
from scipy import ndimage

from app.config import AudioConfig

logger = getLogger(__name__)
config = AudioConfig()


class PreprocessingService:
    """Service for preprocessing audio files with various enhancement techniques."""

    @staticmethod
    def preprocess_audio(file_path: str) -> str:
        """
        Processes an audio file according to the configuration:
        removes DC offset, normalizes, applies pre-emphasis, noise reduction,
        dynamic range compression, and trims silence.

        Args:
            file_path: Path to the audio file to process.

        Returns:
            str: Path to the processed audio file (WAV format).

        Raises:
            RuntimeError: If audio preprocessing fails.
        """
        try:
            logger.info(f"Starting audio processing: {file_path}")

            audio, sr = PreprocessingService._load_audio(file_path)

            audio = PreprocessingService._apply_processing_pipeline(audio)

            max_val = np.max(np.abs(audio))
            if max_val > 1.0:
                logger.info(f"Audio amplitude is too high (max {max_val:.2f}); normalizing.")
                audio = audio / max_val

            output_path = Path(file_path).with_suffix('').as_posix() + '_preprocessed.wav'
            sf.write(output_path, audio, sr)
            logger.info(f"Audio processing completed. File saved at: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Audio preprocessing failed: {e}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"Audio preprocessing failed: {e}")

    @staticmethod
    @lru_cache(maxsize=8)
    def _load_audio(file_path: str) -> Tuple[np.ndarray, int]:
        """
        Loads an audio file with caching. Converts audio to mono and resamples to the target sample rate.

        Args:
            file_path: Path to the audio file.

        Returns:
            Tuple[np.ndarray, int]: The audio signal and sample rate.
        """
        target_sr = config.get('sample_rate', 16000)
        logger.info(f"Loading audio file {file_path} with target sample rate {target_sr}")
        return librosa.load(file_path, sr=target_sr, mono=True)

    @staticmethod
    def _apply_processing_pipeline(audio: np.ndarray) -> np.ndarray:
        """
        Applies a series of processing steps based on the configuration:
        DC offset removal, normalization, pre-emphasis, noise reduction,
        dynamic range compression, and silence trimming.
        """
        # Remove DC offset
        if config.get('enable_dc_offset', True):
            mean_val = np.mean(audio)
            logger.info(f"Removing DC offset (mean value: {mean_val:.6f})")
            audio = audio - mean_val

        # Normalize audio
        if config.get('enable_normalization', True):
            logger.info("Normalizing audio")
            audio = librosa.util.normalize(audio)

        # Apply pre-emphasis filter
        if config.get('enable_pre_emphasis', True):
            pre_emphasis = config.get('pre_emphasis', 0.97)
            logger.info(f"Applying pre-emphasis with coefficient {pre_emphasis}")
            audio = np.append(audio[0], audio[1:] - pre_emphasis * audio[:-1])

        # Apply noise reduction
        if config.get('enable_noise_reduction', True):
            logger.info("Applying noise reduction")
            audio = PreprocessingService._reduce_noise(audio)

        # Apply dynamic range compression
        if config.get('enable_compression', False):
            logger.info("Applying dynamic range compression")
            audio = np.sign(audio) * np.log1p(np.abs(audio))

        # Trim silence
        if config.get('enable_trim_silence', True):
            trim_db = config.get('trim_db', 60)
            logger.info(f"Trimming silence with top_db = {trim_db}")
            audio, _ = librosa.effects.trim(audio, top_db=trim_db)

        return audio

    @staticmethod
    def _reduce_noise(audio: np.ndarray) -> np.ndarray:
        """
        Applies spectral gating for noise reduction using STFT.
        Uses a soft mask with Gaussian smoothing.

        Args:
            audio: The audio signal.

        Returns:
            np.ndarray: The audio signal after noise reduction.
        """
        frame_length = config.get('frame_length', 2048)
        hop_length = config.get('hop_length', 512)
        noise_threshold = config.get('noise_threshold', 1.5)

        logger.info(f"Noise reduction parameters: frame_length={frame_length}, hop_length={hop_length}, noise_threshold={noise_threshold}")

        D = librosa.stft(audio, n_fft=frame_length, hop_length=hop_length)
        D_mag = np.abs(D)

        noise_frames = min(10, D_mag.shape[1])
        noise_estimate = np.mean(D_mag[:, :noise_frames], axis=1, keepdims=True)

        mask = (D_mag > noise_threshold * noise_estimate).astype(float)
        smoothed_mask = ndimage.gaussian_filter(mask, sigma=2)

        D_cleaned = D * smoothed_mask
        audio_clean = librosa.istft(D_cleaned, hop_length=hop_length)
        return audio_clean

    @staticmethod
    def detect_silence(audio: np.ndarray, threshold: Optional[float] = None) -> bool:
        """
        Determines whether the audio is silent by evaluating its RMS amplitude.

        Args:
            audio: The audio signal (numpy array).
            threshold: Optional threshold. If None, uses the configured value.

        Returns:
            bool: True if the audio is considered silent, False otherwise.
        """
        if threshold is None:
            threshold = config.get('silence_threshold', 0.01)
        rms = np.sqrt(np.mean(np.square(audio)))
        is_silent = rms < threshold
        logger.info(
            f"Audio RMS: {rms:.4f} - {'silent' if is_silent else 'contains sound'} (threshold: {threshold})"
        )
        return is_silent

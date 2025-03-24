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
        silence trimming, DC offset removal, normalization, pre-emphasis, noise reduction,
        and dynamic range compression.
        """
        # Trim silence first
        if config.get('enable_trim_silence', True):
            trim_db = config.get('trim_db', 60)
            logger.info(f"Trimming silence with top_db = {trim_db}")
            
            # Log audio statistics before trimming
            rms_before = np.sqrt(np.mean(np.square(audio)))
            max_before = np.max(np.abs(audio))
            min_before = np.min(np.abs(audio))
            mean_before = np.mean(np.abs(audio))
            logger.info(f"Pre-trim audio stats - RMS: {rms_before:.6f}, Max: {max_before:.6f}, Min: {min_before:.6f}, Mean: {mean_before:.6f}")
            
            # Get trim indices for debugging
            audio_trimmed, (start_idx, end_idx) = librosa.effects.trim(audio, top_db=trim_db)
            
            # Log trim results
            duration_before = len(audio)
            duration_after = len(audio_trimmed)
            trimmed_samples = duration_before - duration_after
            logger.info(f"Trim results - Original duration: {duration_before}, Trimmed duration: {duration_after}, "
                       f"Trimmed samples: {trimmed_samples}, Trim indices: [{start_idx}, {end_idx}]")
            
            # Log audio statistics after trimming
            rms_after = np.sqrt(np.mean(np.square(audio_trimmed)))
            max_after = np.max(np.abs(audio_trimmed))
            min_after = np.min(np.abs(audio_trimmed))
            mean_after = np.mean(np.abs(audio_trimmed))
            logger.info(f"Post-trim audio stats - RMS: {rms_after:.6f}, Max: {max_after:.6f}, Min: {min_after:.6f}, Mean: {mean_after:.6f}")
            
            # Check for potential false positives
            if trimmed_samples > duration_before * 0.5:  # If more than 50% was trimmed
                logger.warning(f"Large amount of audio trimmed: {trimmed_samples/duration_before*100:.1f}% of original audio")
            
            audio = audio_trimmed

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
        Determines whether the audio is silent by evaluating its RMS amplitude and energy distribution.
        Uses a more lenient approach that considers both overall RMS and local energy peaks.

        Args:
            audio: The audio signal (numpy array).
            threshold: Optional threshold. If None, uses the configured value.

        Returns:
            bool: True if the audio is considered silent, False otherwise.
        """
        if threshold is None:
            threshold = config.get('silence_threshold', 0.01)
            
        # Calculate various audio statistics for debugging
        rms = np.sqrt(np.mean(np.square(audio)))
        max_val = np.max(np.abs(audio))
        min_val = np.min(np.abs(audio))
        mean_val = np.mean(np.abs(audio))
        std_val = np.std(audio)
        
        # Calculate energy distribution
        energy = np.square(audio)
        energy_above_threshold = np.mean(energy > threshold)
        
        # Calculate local energy peaks
        frame_length = 2048  # About 128ms at 16kHz
        hop_length = 512
        D = librosa.stft(audio, n_fft=frame_length, hop_length=hop_length)
        D_mag = np.abs(D)
        local_energy = np.mean(D_mag, axis=0)
        peak_energy = np.max(local_energy)
        
        # Log detailed audio statistics
        logger.info(f"Silence detection stats:")
        logger.info(f"- RMS: {rms:.6f}")
        logger.info(f"- Max amplitude: {max_val:.6f}")
        logger.info(f"- Min amplitude: {min_val:.6f}")
        logger.info(f"- Mean amplitude: {mean_val:.6f}")
        logger.info(f"- Standard deviation: {std_val:.6f}")
        logger.info(f"- Energy above threshold ratio: {energy_above_threshold:.6f}")
        logger.info(f"- Peak local energy: {peak_energy:.6f}")
        logger.info(f"- Silence threshold: {threshold}")
        
        # More lenient silence detection
        # Consider audio non-silent if:
        # 1. It has significant local energy peaks (indicating speech or sound)
        # 2. The maximum amplitude is above a minimum threshold
        # 3. The standard deviation indicates some variation in the signal
        is_silent = (
            peak_energy < threshold * 2 and  # No significant local energy peaks
            max_val < threshold * 4 and      # No significant amplitude peaks
            std_val < threshold * 2          # Low variation in the signal
        )
        
        logger.info(f"Audio {'silent' if is_silent else 'contains sound'} "
                   f"(Peak energy: {peak_energy:.6f}, Max: {max_val:.6f}, Std: {std_val:.6f})")
        return is_silent

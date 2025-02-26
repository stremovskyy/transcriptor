import librosa
import numpy as np
import soundfile as sf
from scipy import signal
from typing import Tuple, Optional
from pathlib import Path
from logging import getLogger
import noisereduce as nr

logger = getLogger(__name__)


class AudioPreprocessor:
    def __init__(self, 
                 noise_reduction_strength: float = 0.5,
                 voice_enhancement_strength: float = 0.5,
                 volume_factor: float = 1.2,
                 high_pass_freq: float = 100.0,
                 low_pass_freq: float = 8000.0,
                 voice_freq_min: float = 300.0,
                 voice_freq_max: float = 3400.0,
                 agc_target_db: float = -20.0):
        """
        Initialize AudioPreprocessor with advanced parameters.
        
        Args:
            noise_reduction_strength: Strength of noise reduction (0.0 to 1.0)
            voice_enhancement_strength: Voice enhancement multiplier (> 0.0)
            volume_factor: Volume adjustment factor (0.0 to 1.5)
            high_pass_freq: High-pass filter frequency in Hz
            low_pass_freq: Low-pass filter frequency in Hz
            voice_freq_min: Minimum voice frequency to enhance
            voice_freq_max: Maximum voice frequency to enhance
            agc_target_db: Target dB level for automatic gain control
        """
        if not 0.0 <= noise_reduction_strength <= 1.0:
            raise ValueError("noise_reduction_strength must be between 0.0 and 1.0")
        if voice_enhancement_strength <= 0.0:
            raise ValueError("voice_enhancement_strength must be greater than 0.0")
        if not 0.0 <= volume_factor <= 1.5:
            raise ValueError("volume_factor must be between 0.0 and 1.5")

        self.noise_reduction_strength = noise_reduction_strength
        self.voice_enhancement_strength = voice_enhancement_strength
        self.volume_factor = volume_factor
        self.high_pass_freq = high_pass_freq
        self.low_pass_freq = low_pass_freq
        self.voice_freq_min = voice_freq_min
        self.voice_freq_max = voice_freq_max
        self.agc_target_db = agc_target_db

    def _spectral_gate(self, y: np.ndarray, sr: int, noise_profile: float) -> np.ndarray:
        """Enhanced spectral gating with advanced noise reduction."""
        # Apply noise reduction using advanced spectral subtraction
        y_reduced = nr.reduce_noise(
            y=y,
            sr=sr,
            prop_decrease=self.noise_reduction_strength,
            stationary=False,
            n_jobs=-1
        )
        
        # Additional spectral gating for residual noise
        S = librosa.stft(y_reduced)
        mag = np.abs(S)
        phase = np.angle(S)

        # Dynamic threshold based on local statistics
        thresh = noise_profile * self.noise_reduction_strength
        local_energy = librosa.feature.rms(S=mag, frame_length=2048)
        dynamic_thresh = np.maximum(thresh, np.mean(local_energy) * 0.5)
        
        # Create and smooth mask
        mask = (mag > dynamic_thresh).astype(float)
        mask = signal.medfilt2d(mask, kernel_size=(3, 3))
        
        # Apply mask with soft transition
        transition = 0.1
        soft_mask = np.clip((mag - dynamic_thresh) / (transition * dynamic_thresh), 0, 1)
        mag_cleaned = mag * soft_mask
        
        # Reconstruct signal
        S_cleaned = mag_cleaned * np.exp(1j * phase)
        y_cleaned = librosa.istft(S_cleaned)
        
        return y_cleaned

    def _remove_clicks_and_pops(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Remove clicks and pops from audio signal."""
        # Detect sudden amplitude changes
        diff = np.diff(y)
        threshold = np.std(diff) * 4
        clicks = np.where(np.abs(diff) > threshold)[0]
        
        # Interpolate over detected clicks
        y_clean = y.copy()
        for click in clicks:
            if click > 0 and click < len(y) - 1:
                y_clean[click] = (y_clean[click - 1] + y_clean[click + 1]) / 2
                
        return y_clean

    def _adaptive_voice_enhancement(self, y: np.ndarray, sr: int) -> np.ndarray:
        """Enhance voice frequencies adaptively."""
        # Apply pre-emphasis
        y_enhanced = librosa.effects.preemphasis(y)
        
        # Enhance voice frequencies
        freqs = librosa.fft_frequencies(sr=sr)
        voice_mask = (freqs >= self.voice_freq_min) & (freqs <= self.voice_freq_max)
        
        # Compute STFT
        D = librosa.stft(y_enhanced)
        mag, phase = librosa.magphase(D)
        
        # Apply frequency-dependent gain
        freq_gain = np.ones_like(freqs)
        freq_gain[voice_mask] *= self.voice_enhancement_strength
        
        # Apply gain to magnitude
        mag_enhanced = mag * freq_gain[:, np.newaxis]
        
        # Reconstruct signal
        y_enhanced = librosa.istft(mag_enhanced * phase)
        
        return y_enhanced

    def _automatic_gain_control(self, y: np.ndarray) -> np.ndarray:
        """Apply automatic gain control to maintain consistent volume."""
        # Calculate current dB level
        current_db = 20 * np.log10(np.sqrt(np.mean(y**2)) + 1e-10)
        
        # Calculate required gain
        gain = 10**((self.agc_target_db - current_db) / 20)
        
        # Apply gain with limiting
        y_agc = y * min(gain, 2.0)  # Limit maximum gain to 2.0
        
        # Apply soft knee limiting
        threshold = 0.95
        y_agc = np.where(
            np.abs(y_agc) > threshold,
            threshold * np.sign(y_agc) + (np.abs(y_agc) - threshold) * 0.1,
            y_agc
        )
        
        return y_agc

    def preprocess_audio(self, file_path: str,
                        output_path: Optional[str] = None) -> Tuple[np.ndarray, int]:
        """
        Process audio file with enhanced filtering and voice cleaning.
        
        Args:
            file_path: Path to input audio file
            output_path: Optional path to save processed audio
            
        Returns:
            Tuple of processed audio array and sample rate
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"Input file not found: {file_path}")

            # Load audio
            y, sr = librosa.load(file_path, sr=None, mono=True)
            logger.info(f"Audio loaded: {y.shape}, {sr} Hz")

            # Remove clicks and pops
            y = self._remove_clicks_and_pops(y, sr)
            logger.info("Clicks and pops removed")

            # Calculate noise profile from silence segments
            noise_mask = librosa.effects.split(y, top_db=30)
            if len(noise_mask) > 0:
                noise_segments = []
                for start, end in noise_mask:
                    noise_segments.append(y[start:end])
                noise_profile = np.mean([
                    librosa.feature.rms(y=segment).mean()
                    for segment in noise_segments
                ])
            else:
                noise_profile = np.percentile(np.abs(y), 5)

            # Apply noise reduction
            y = self._spectral_gate(y, sr, noise_profile)
            logger.info("Noise reduction applied")

            # Apply bandpass filtering
            nyquist = sr / 2
            high_pass = min(self.high_pass_freq, nyquist * 0.95)
            low_pass = min(self.low_pass_freq, nyquist * 0.95)
            
            sos_high = signal.butter(4, high_pass, btype='high', fs=sr, output='sos')
            sos_low = signal.butter(4, low_pass, btype='low', fs=sr, output='sos')
            y = signal.sosfilt(sos_high, y)
            y = signal.sosfilt(sos_low, y)
            logger.info(f"Bandpass filtering applied with high-pass: {high_pass:.1f}Hz, low-pass: {low_pass:.1f}Hz")

            # Enhance voice frequencies
            y = self._adaptive_voice_enhancement(y, sr)
            logger.info("Voice frequencies enhanced")

            # Apply automatic gain control
            y = self._automatic_gain_control(y)
            logger.info("Automatic gain control applied")

            # Final volume adjustment
            y = y * self.volume_factor
            
            # Normalize to prevent clipping
            y = np.clip(y, -1.0, 1.0)
            logger.info("Final processing and normalization complete")

            if output_path:
                output_path = Path(output_path)
                sf.write(str(output_path), y, sr)
                logger.info(f"Enhanced audio saved to: {output_path}")

            return y, sr

        except Exception as e:
            logger.error(f"Audio processing failed: {str(e)}")
            raise RuntimeError(f"Audio processing failed: {str(e)}") from e
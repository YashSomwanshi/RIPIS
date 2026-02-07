"""
Audio utility functions for RIPIS
"""
import numpy as np
from typing import Optional


def calculate_rms(audio_data: bytes, dtype=np.int16) -> float:
    """Calculate the RMS (volume) of audio data."""
    audio_array = np.frombuffer(audio_data, dtype=dtype)
    if len(audio_array) == 0:
        return 0.0
    return np.sqrt(np.mean(audio_array.astype(np.float32) ** 2))


def is_silent(audio_data: bytes, threshold: float = 500.0) -> bool:
    """Check if audio data is silent (below threshold)."""
    rms = calculate_rms(audio_data)
    return rms < threshold


def normalize_audio(audio_data: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
    """Normalize audio to a target RMS level."""
    current_rms = np.sqrt(np.mean(audio_data ** 2))
    if current_rms > 0:
        return audio_data * (target_rms / current_rms)
    return audio_data


def bytes_to_seconds(byte_count: int, sample_rate: int = 16000, 
                     channels: int = 1, sample_width: int = 2) -> float:
    """Convert byte count to duration in seconds."""
    return byte_count / (sample_rate * channels * sample_width)


def seconds_to_bytes(seconds: float, sample_rate: int = 16000,
                     channels: int = 1, sample_width: int = 2) -> int:
    """Convert duration in seconds to byte count."""
    return int(seconds * sample_rate * channels * sample_width)

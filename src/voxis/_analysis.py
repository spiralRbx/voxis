from __future__ import annotations

import numpy as np

from ._spectral import linear_resample
from ._util import ensure_float32_frames


def resample_audio(samples: np.ndarray, source_rate: int, target_rate: int) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_source = max(1, int(source_rate))
    safe_target = max(1, int(target_rate))
    if safe_source == safe_target:
        return frames.copy()
    target_frames = max(1, int(round(frames.shape[0] * safe_target / safe_source)))
    return linear_resample(frames, target_frames)


def bit_depth_convert_audio(
    samples: np.ndarray,
    *,
    bit_depth: int = 16,
    dither: bool = True,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_depth = int(np.clip(bit_depth, 2, 24))
    step = float(1.0 / ((1 << (safe_depth - 1)) - 1))
    rng = np.random.default_rng(991)
    working = frames.copy()
    if dither:
        noise = (rng.random(size=working.shape, dtype=np.float32) - rng.random(size=working.shape, dtype=np.float32)) * step
        working += noise.astype(np.float32)
    quantized = np.round(np.clip(working, -1.0, 1.0) / step) * step
    return np.ascontiguousarray(np.clip(quantized, -1.0, 1.0).astype(np.float32), dtype=np.float32)


def dither_audio(
    samples: np.ndarray,
    *,
    bit_depth: int = 16,
) -> np.ndarray:
    return bit_depth_convert_audio(samples, bit_depth=bit_depth, dither=True)


def peak_dbfs(samples: np.ndarray) -> float:
    frames = ensure_float32_frames(samples)
    peak = float(np.max(np.abs(frames)))
    if peak <= 1e-12:
        return float("-inf")
    return float(20.0 * np.log10(peak))


def rms_dbfs(samples: np.ndarray) -> float:
    frames = ensure_float32_frames(samples)
    rms = float(np.sqrt(np.mean(np.square(frames), dtype=np.float64)))
    if rms <= 1e-12:
        return float("-inf")
    return float(20.0 * np.log10(rms))


def envelope_follower(
    samples: np.ndarray,
    sample_rate: int,
    *,
    attack_ms: float = 10.0,
    release_ms: float = 80.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    mono = np.mean(np.abs(frames), axis=1, dtype=np.float32)
    attack_coeff = float(np.exp(-1.0 / max(sample_rate * max(float(attack_ms), 0.1) / 1000.0, 1.0)))
    release_coeff = float(np.exp(-1.0 / max(sample_rate * max(float(release_ms), 0.1) / 1000.0, 1.0)))
    output = np.empty_like(mono, dtype=np.float32)
    state = 0.0
    for index, value in enumerate(mono):
        coeff = attack_coeff if value > state else release_coeff
        state = value + coeff * (state - value)
        output[index] = state
    return np.ascontiguousarray(output, dtype=np.float32)


def integrated_lufs(samples: np.ndarray, sample_rate: int) -> float:
    frames = ensure_float32_frames(samples)
    mono = np.mean(frames, axis=1, dtype=np.float32)
    highpassed = np.empty_like(mono, dtype=np.float32)
    cutoff_hz = 90.0
    rc = 1.0 / (2.0 * np.pi * cutoff_hz)
    dt = 1.0 / max(sample_rate, 1)
    alpha = float(rc / (rc + dt))
    previous_input = 0.0
    previous_output = 0.0
    for index, value in enumerate(mono):
        current = alpha * (previous_output + value - previous_input)
        highpassed[index] = current
        previous_input = float(value)
        previous_output = float(current)
    emphasized = highpassed + np.concatenate([[0.0], np.diff(highpassed)]).astype(np.float32) * 0.12
    gate = np.abs(emphasized) > 10.0 ** (-70.0 / 20.0)
    if not np.any(gate):
        return float("-inf")
    mean_square = float(np.mean(np.square(emphasized[gate]), dtype=np.float64))
    return float(-0.691 + 10.0 * np.log10(mean_square + 1e-12))


def loudness_normalize_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    target_lufs: float = -16.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    current_lufs = integrated_lufs(frames, sample_rate)
    if not np.isfinite(current_lufs):
        return frames.copy()
    gain_db = float(target_lufs) - float(current_lufs)
    gain = float(10.0 ** (gain_db / 20.0))
    output = frames * gain
    peak = float(np.max(np.abs(output)))
    if peak > 1.0:
        output /= peak
    return np.ascontiguousarray(output.astype(np.float32), dtype=np.float32)

from __future__ import annotations

import math

import numpy as np

from ._util import ensure_float32_frames


def _mix_wet_dry(frames: np.ndarray, wet: np.ndarray, mix: float) -> np.ndarray:
    clamped_mix = float(np.clip(mix, 0.0, 1.0))
    return np.ascontiguousarray(frames * (1.0 - clamped_mix) + wet * clamped_mix, dtype=np.float32)


def _db_to_linear(value_db: float) -> float:
    return float(10.0 ** (float(value_db) / 20.0))


def _moving_average(signal: np.ndarray, window: int) -> np.ndarray:
    samples = np.asarray(signal, dtype=np.float32)
    safe_window = max(1, int(window))
    if safe_window <= 1 or samples.shape[0] <= 2:
        return samples.copy()
    if safe_window >= samples.shape[0]:
        mean_value = float(np.mean(samples, dtype=np.float64))
        return np.full_like(samples, mean_value, dtype=np.float32)

    pad_left = safe_window // 2
    pad_right = safe_window - 1 - pad_left
    padded = np.pad(samples, (pad_left, pad_right), mode="edge")
    cumsum = np.empty(padded.shape[0] + 1, dtype=np.float64)
    cumsum[0] = 0.0
    np.cumsum(padded, dtype=np.float64, out=cumsum[1:])
    smoothed = (cumsum[safe_window:] - cumsum[:-safe_window]) / float(safe_window)
    return np.ascontiguousarray(smoothed.astype(np.float32), dtype=np.float32)


def _lowpass(signal: np.ndarray, sample_rate: int, cutoff_hz: float) -> np.ndarray:
    safe_cutoff = float(max(cutoff_hz, 10.0))
    samples = np.asarray(signal, dtype=np.float32)
    window = int(np.clip(round(max(sample_rate, 1) / safe_cutoff), 1, 1024))
    filtered = _moving_average(samples, window)
    if window > 3:
        filtered = _moving_average(filtered, max(1, window // 2))
    return np.ascontiguousarray(filtered, dtype=np.float32)


def _highpass(signal: np.ndarray, sample_rate: int, cutoff_hz: float) -> np.ndarray:
    low = _lowpass(signal, sample_rate, cutoff_hz)
    return np.ascontiguousarray(signal - low, dtype=np.float32)


def _fractional_delay(signal: np.ndarray, delay_samples: float) -> np.ndarray:
    if abs(float(delay_samples)) < 1e-4:
        return np.asarray(signal, dtype=np.float32).copy()
    positions = np.arange(signal.shape[0], dtype=np.float32)
    read_positions = positions - float(delay_samples)
    delayed = np.interp(read_positions, positions, signal, left=0.0, right=0.0).astype(np.float32)
    return np.ascontiguousarray(delayed, dtype=np.float32)


def _stereoize_mono(mono: np.ndarray) -> np.ndarray:
    signal = np.asarray(mono, dtype=np.float32)[:, None]
    return np.ascontiguousarray(np.repeat(signal, 2, axis=1), dtype=np.float32)


def stereo_widening_audio(
    samples: np.ndarray,
    *,
    amount: float = 1.25,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if frames.shape[1] < 2:
        return _stereoize_mono(frames[:, 0])
    mid = 0.5 * (frames[:, 0] + frames[:, 1])
    side = 0.5 * (frames[:, 0] - frames[:, 1]) * float(max(amount, 0.0))
    output = np.column_stack([mid + side, mid - side]).astype(np.float32)
    return np.ascontiguousarray(output, dtype=np.float32)


def mid_side_processing_audio(
    samples: np.ndarray,
    *,
    mid_gain_db: float = 0.0,
    side_gain_db: float = 0.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if frames.shape[1] < 2:
        return frames.copy()
    mid = 0.5 * (frames[:, 0] + frames[:, 1]) * _db_to_linear(mid_gain_db)
    side = 0.5 * (frames[:, 0] - frames[:, 1]) * _db_to_linear(side_gain_db)
    output = np.column_stack([mid + side, mid - side]).astype(np.float32)
    return np.ascontiguousarray(output, dtype=np.float32)


def stereo_imager_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    low_width: float = 0.9,
    high_width: float = 1.35,
    crossover_hz: float = 280.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if frames.shape[1] < 2:
        return _stereoize_mono(frames[:, 0])
    mid = 0.5 * (frames[:, 0] + frames[:, 1]).astype(np.float32)
    side = 0.5 * (frames[:, 0] - frames[:, 1]).astype(np.float32)
    low_mid = _lowpass(mid, sample_rate, crossover_hz)
    low_side = _lowpass(side, sample_rate, crossover_hz)
    high_mid = mid - low_mid
    high_side = side - low_side
    shaped_side = low_side * float(max(low_width, 0.0)) + high_side * float(max(high_width, 0.0))
    output = np.column_stack([low_mid + high_mid + shaped_side, low_mid + high_mid - shaped_side]).astype(np.float32)
    return np.ascontiguousarray(output, dtype=np.float32)


def binaural_effect_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    azimuth_deg: float = 25.0,
    distance: float = 1.0,
    room_mix: float = 0.08,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    mono = np.mean(frames, axis=1, dtype=np.float32)
    azimuth = float(np.clip(azimuth_deg, -90.0, 90.0))
    azimuth_norm = math.sin(math.radians(abs(azimuth)))
    delay_samples = azimuth_norm * 0.00068 * sample_rate
    near_gain = 1.0 / max(float(distance), 0.3)
    far_gain = (0.52 + 0.38 * (1.0 - azimuth_norm)) / max(float(distance), 0.3)
    far_cutoff = 1_600.0 + (1.0 - azimuth_norm) * 5_600.0

    near = mono * near_gain
    far = _lowpass(_fractional_delay(mono, delay_samples), sample_rate, far_cutoff) * far_gain
    if azimuth >= 0.0:
        left = far
        right = near
    else:
        left = near
        right = far

    wet = np.column_stack([left, right]).astype(np.float32)
    if room_mix > 0.0:
        early = _fractional_delay(mono, 0.004 * sample_rate)[:, None] * float(np.clip(room_mix, 0.0, 0.5)) * 0.18
        wet += np.repeat(early, 2, axis=1)
    if frames.shape[1] >= 2:
        return _mix_wet_dry(frames[:, :2], wet, 0.88)
    return np.ascontiguousarray(wet, dtype=np.float32)


def spatial_positioning_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    azimuth_deg: float = 25.0,
    elevation_deg: float = 0.0,
    distance: float = 1.0,
) -> np.ndarray:
    wet = binaural_effect_audio(
        samples,
        sample_rate,
        azimuth_deg=azimuth_deg,
        distance=distance,
        room_mix=0.04 + 0.03 * min(max(distance - 1.0, 0.0), 1.0),
    )
    elevation = float(np.clip(elevation_deg, -60.0, 60.0)) / 60.0
    if elevation > 0.0:
        high = np.column_stack([
            _highpass(wet[:, 0], sample_rate, 2_400.0),
            _highpass(wet[:, 1], sample_rate, 2_400.0),
        ]).astype(np.float32)
        wet = wet + high * (0.12 * elevation)
    elif elevation < 0.0:
        wet = np.column_stack([
            _lowpass(wet[:, 0], sample_rate, 4_800.0 + elevation * 1_800.0),
            _lowpass(wet[:, 1], sample_rate, 4_800.0 + elevation * 1_800.0),
        ]).astype(np.float32)
    distance_gain = 1.0 / max(float(distance), 0.35)
    return np.ascontiguousarray(wet * distance_gain, dtype=np.float32)


def hrtf_simulation_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    azimuth_deg: float = 30.0,
    elevation_deg: float = 0.0,
    distance: float = 1.0,
) -> np.ndarray:
    wet = spatial_positioning_audio(
        samples,
        sample_rate,
        azimuth_deg=azimuth_deg,
        elevation_deg=elevation_deg,
        distance=distance,
    )
    notch_delay = (0.00022 + abs(float(elevation_deg)) / 60.0 * 0.00018) * sample_rate
    left_reflection = _fractional_delay(wet[:, 0], notch_delay)
    right_reflection = _fractional_delay(wet[:, 1], notch_delay)
    wet[:, 0] = wet[:, 0] - left_reflection * 0.18
    wet[:, 1] = wet[:, 1] - right_reflection * 0.18
    return np.ascontiguousarray(wet, dtype=np.float32)

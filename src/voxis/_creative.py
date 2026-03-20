from __future__ import annotations

import math

import numpy as np

from ._spectral import (
    fft_filter_audio,
    formant_shift_audio,
    linear_resample,
    pitch_shift_audio,
    time_stretch_audio,
)
from ._util import ensure_float32_frames


def _mix_wet_dry(frames: np.ndarray, wet: np.ndarray, mix: float) -> np.ndarray:
    clamped_mix = float(np.clip(mix, 0.0, 1.0))
    return np.ascontiguousarray(frames * (1.0 - clamped_mix) + wet * clamped_mix, dtype=np.float32)


def _fft_convolve_same(signal: np.ndarray, impulse: np.ndarray) -> np.ndarray:
    length = signal.shape[0]
    fft_size = 1 << int(np.ceil(np.log2(max(2, signal.shape[0] + impulse.shape[0] - 1))))
    wet = np.fft.irfft(
        np.fft.rfft(signal, fft_size) * np.fft.rfft(impulse, fft_size),
        fft_size,
    )[:length]
    return np.ascontiguousarray(wet.astype(np.float32), dtype=np.float32)


def glitch_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    slice_ms: float = 70.0,
    repeat_probability: float = 0.22,
    dropout_probability: float = 0.12,
    reverse_probability: float = 0.10,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    rng = np.random.default_rng(1337)
    slice_frames = max(16, int(round(float(slice_ms) * sample_rate / 1000.0)))
    wet = frames.copy()
    for start in range(0, frames.shape[0], slice_frames):
        end = min(frames.shape[0], start + slice_frames)
        chance = float(rng.random())
        if chance < dropout_probability:
            wet[start:end] = 0.0
        elif chance < dropout_probability + reverse_probability:
            wet[start:end] = wet[start:end][::-1]
        elif chance < dropout_probability + reverse_probability + repeat_probability and start >= slice_frames:
            wet[start:end] = wet[start - slice_frames : start - slice_frames + (end - start)]
    return _mix_wet_dry(frames, wet, mix)


def stutter_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    slice_ms: float = 90.0,
    repeats: int = 3,
    interval_ms: float = 480.0,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    wet = frames.copy()
    slice_frames = max(16, int(round(float(slice_ms) * sample_rate / 1000.0)))
    interval_frames = max(slice_frames, int(round(float(interval_ms) * sample_rate / 1000.0)))
    for start in range(0, frames.shape[0] - slice_frames, interval_frames):
        grain = frames[start : start + slice_frames]
        for repeat_index in range(max(1, int(repeats))):
            dst = start + repeat_index * slice_frames
            if dst >= wet.shape[0]:
                break
            dst_end = min(wet.shape[0], dst + slice_frames)
            wet[dst:dst_end] = grain[: dst_end - dst]
    return _mix_wet_dry(frames, wet, mix)


def tape_stop_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    stop_time_ms: float = 900.0,
    curve: float = 2.0,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    stop_frames = min(frames.shape[0], max(64, int(round(float(stop_time_ms) * sample_rate / 1000.0))))
    if stop_frames >= frames.shape[0]:
        prefix = np.zeros((0, frames.shape[1]), dtype=np.float32)
        tail = frames
    else:
        prefix = frames[:-stop_frames]
        tail = frames[-stop_frames:]

    timeline = np.linspace(0.0, 1.0, num=tail.shape[0], dtype=np.float32)
    speed = np.maximum(0.01, (1.0 - timeline) ** max(float(curve), 0.1))
    positions = np.cumsum(speed, dtype=np.float32)
    positions = positions / max(float(positions[-1]), 1e-6) * max(0.0, tail.shape[0] - 1)

    slowed = np.empty_like(tail)
    source_index = np.arange(tail.shape[0], dtype=np.float32)
    for channel in range(tail.shape[1]):
        slowed[:, channel] = np.interp(positions, source_index, tail[:, channel]).astype(np.float32)

    output = np.concatenate([prefix, slowed], axis=0) if prefix.size else slowed
    return _mix_wet_dry(frames, output[: frames.shape[0]], mix)


def reverse_reverb_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    decay_seconds: float = 1.2,
    mix: float = 0.45,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    reverse = frames[::-1].copy()
    length = max(64, int(sample_rate * max(float(decay_seconds), 0.05) * 0.5))
    time_axis = np.arange(length, dtype=np.float32) / sample_rate
    impulse = np.exp(-time_axis / max(float(decay_seconds), 0.05)).astype(np.float32)
    impulse[0] = 1.0
    wet = np.empty_like(reverse)
    for channel in range(reverse.shape[1]):
        wet[:, channel] = _fft_convolve_same(reverse[:, channel], impulse)
    restored = wet[::-1].copy()
    peak = float(np.max(np.abs(restored)))
    if peak > 1.0:
        restored /= peak
    return _mix_wet_dry(frames, restored, mix)


def granular_synthesis_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    grain_ms: float = 80.0,
    overlap: float = 0.5,
    jitter_ms: float = 25.0,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    rng = np.random.default_rng(2025)
    grain_frames = max(32, int(round(float(grain_ms) * sample_rate / 1000.0)))
    hop_frames = max(1, int(round(grain_frames * (1.0 - float(np.clip(overlap, 0.0, 0.95))))))
    jitter_frames = max(0, int(round(float(jitter_ms) * sample_rate / 1000.0)))
    window = np.hanning(grain_frames).astype(np.float32)[:, None]
    wet = np.zeros_like(frames)
    norm = np.zeros((frames.shape[0], 1), dtype=np.float32)

    for dst in range(0, frames.shape[0], hop_frames):
        src = int(np.clip(dst + rng.integers(-jitter_frames, jitter_frames + 1), 0, max(0, frames.shape[0] - grain_frames)))
        grain = frames[src : src + grain_frames]
        if grain.shape[0] < grain_frames:
            grain = np.pad(grain, ((0, grain_frames - grain.shape[0]), (0, 0)))
        dst_end = min(frames.shape[0], dst + grain_frames)
        windowed = grain[: dst_end - dst] * window[: dst_end - dst]
        wet[dst:dst_end] += windowed
        norm[dst:dst_end] += window[: dst_end - dst]

    wet /= np.maximum(norm, 1e-6)
    return _mix_wet_dry(frames, wet, mix)


def time_slicing_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    slice_ms: float = 120.0,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    slice_frames = max(16, int(round(float(slice_ms) * sample_rate / 1000.0)))
    wet = frames.copy()
    for index, start in enumerate(range(0, frames.shape[0], slice_frames)):
        end = min(frames.shape[0], start + slice_frames)
        if index % 2 == 1:
            wet[start:end] = wet[start:end][::-1]
        elif end + slice_frames <= frames.shape[0]:
            wet[start:end], wet[end : end + slice_frames] = wet[end : end + slice_frames].copy(), wet[start:end].copy()
    return _mix_wet_dry(frames, wet, mix)


def random_pitch_mod_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    depth_semitones: float = 2.0,
    segment_ms: float = 180.0,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    rng = np.random.default_rng(404)
    segment_frames = max(64, int(round(float(segment_ms) * sample_rate / 1000.0)))
    control_points = np.arange(0, frames.shape[0] + segment_frames, segment_frames, dtype=np.int32)
    if control_points[-1] != frames.shape[0] - 1:
        control_points[-1] = frames.shape[0] - 1
    random_semitones = rng.uniform(-float(depth_semitones), float(depth_semitones), size=control_points.shape[0]).astype(np.float32)
    positions = np.arange(frames.shape[0], dtype=np.float32)
    semitone_curve = np.interp(positions, control_points.astype(np.float32), random_semitones).astype(np.float32)
    rate_curve = np.power(2.0, semitone_curve / 12.0, dtype=np.float32)
    read_positions = np.cumsum(rate_curve, dtype=np.float32)
    read_positions = read_positions / max(float(read_positions[-1]), 1e-6) * max(0.0, frames.shape[0] - 1)
    wet = np.empty_like(frames)
    source_index = np.arange(frames.shape[0], dtype=np.float32)
    for channel in range(frames.shape[1]):
        wet[:, channel] = np.interp(read_positions, source_index, frames[:, channel]).astype(np.float32)
    return _mix_wet_dry(frames, wet, mix)


def vinyl_effect_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    noise: float = 0.08,
    wow: float = 0.15,
    crackle: float = 0.12,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    timeline = np.arange(frames.shape[0], dtype=np.float32) / sample_rate
    wow_curve = (
        0.0025 * float(np.clip(wow, 0.0, 1.0)) * np.sin(2.0 * np.pi * 0.35 * timeline)
        + 0.0012 * float(np.clip(wow, 0.0, 1.0)) * np.sin(2.0 * np.pi * 1.7 * timeline)
    ).astype(np.float32)
    read_positions = np.cumsum(1.0 + wow_curve, dtype=np.float32)
    read_positions = read_positions / max(float(read_positions[-1]), 1e-6) * max(0.0, frames.shape[0] - 1)

    wet = np.empty_like(frames)
    source_index = np.arange(frames.shape[0], dtype=np.float32)
    for channel in range(frames.shape[1]):
        wet[:, channel] = np.interp(read_positions, source_index, frames[:, channel]).astype(np.float32)

    rng = np.random.default_rng(77)
    hiss = rng.normal(0.0, float(np.clip(noise, 0.0, 1.0)) * 0.02, size=wet.shape).astype(np.float32)
    clicks = np.zeros_like(wet)
    click_count = max(1, int(frames.shape[0] / max(sample_rate // 6, 1) * float(np.clip(crackle, 0.0, 1.0)) * 8))
    if click_count > 0:
        positions_click = rng.integers(0, frames.shape[0], size=click_count)
        amplitudes = rng.uniform(0.1, 0.6, size=click_count).astype(np.float32)
        for position, amplitude in zip(positions_click, amplitudes, strict=False):
            clicks[position : min(frames.shape[0], position + 2)] += amplitude
    wet = wet + hiss + clicks
    wet = fft_filter_audio(wet, sample_rate, low_hz=60.0, high_hz=8_500.0, mix=1.0)
    return _mix_wet_dry(frames, wet, mix)


def radio_effect_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    noise_level: float = 0.04,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    wet = fft_filter_audio(frames, sample_rate, low_hz=180.0, high_hz=3_800.0, mix=1.0)
    wet = np.tanh(wet * 1.7).astype(np.float32)
    rng = np.random.default_rng(808)
    wet += rng.normal(0.0, float(np.clip(noise_level, 0.0, 1.0)) * 0.01, size=wet.shape).astype(np.float32)
    return _mix_wet_dry(frames, wet, mix)


def telephone_effect_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    mono = np.mean(frames, axis=1, keepdims=True, dtype=np.float32)
    wet = np.repeat(mono, frames.shape[1], axis=1)
    wet = fft_filter_audio(wet, sample_rate, low_hz=300.0, high_hz=3_200.0, mix=1.0)
    return _mix_wet_dry(frames, wet, mix)


def retro_8bit_audio(
    samples: np.ndarray,
    *,
    bit_depth: int = 6,
    sample_rate_reduction: int = 8,
    mix: float = 1.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_bits = max(2, int(bit_depth))
    safe_hold = max(1, int(sample_rate_reduction))
    levels = float((1 << safe_bits) - 1)
    wet = np.round(((frames + 1.0) * 0.5) * levels) / levels
    wet = (wet * 2.0 - 1.0).astype(np.float32)
    if safe_hold > 1:
        held = np.repeat(wet[::safe_hold], safe_hold, axis=0)
        wet = held[: frames.shape[0]]
    return _mix_wet_dry(frames, wet.astype(np.float32), mix)


def slow_motion_extreme_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    rate: float = 0.45,
    tone_hz: float = 4_800.0,
) -> np.ndarray:
    stretched = time_stretch_audio(samples, rate=max(float(rate), 0.1), fft_size=1024, hop_size=768)
    return fft_filter_audio(stretched, sample_rate, low_hz=40.0, high_hz=tone_hz, mix=1.0)


def robot_voice_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    carrier_hz: float = 70.0,
    mix: float = 0.85,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    mono = np.mean(frames, axis=1, keepdims=True, dtype=np.float32)
    timeline = np.arange(frames.shape[0], dtype=np.float32) / sample_rate
    carrier = np.sign(np.sin(2.0 * np.pi * float(carrier_hz) * timeline)).astype(np.float32)[:, None]
    wet = mono * carrier
    wet = np.repeat(wet, frames.shape[1], axis=1)
    wet = fft_filter_audio(wet, sample_rate, low_hz=120.0, high_hz=4_500.0, mix=1.0)
    return _mix_wet_dry(frames, wet, mix)


def alien_voice_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    shift_semitones: float = 5.0,
    formant_shift: float = 1.18,
    mix: float = 0.8,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    shifted = pitch_shift_audio(frames, sample_rate, shift_semitones, fft_size=1024, hop_size=768)
    shifted = formant_shift_audio(shifted, sample_rate, formant_shift, mix=1.0, fft_size=1024, hop_size=768)
    shifted = random_pitch_mod_audio(shifted, sample_rate, depth_semitones=0.28, segment_ms=520.0, mix=1.0)
    return _mix_wet_dry(frames, shifted, mix)

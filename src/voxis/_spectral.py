from __future__ import annotations

from typing import Iterable

import numpy as np

from ._util import ensure_float32_frames

_NOTE_TO_SEMITONE = {
    "C": 0,
    "C#": 1,
    "DB": 1,
    "D": 2,
    "D#": 3,
    "EB": 3,
    "E": 4,
    "F": 5,
    "F#": 6,
    "GB": 6,
    "G": 7,
    "G#": 8,
    "AB": 8,
    "A": 9,
    "A#": 10,
    "BB": 10,
    "B": 11,
}

_SCALE_INTERVALS = {
    "chromatic": tuple(range(12)),
    "major": (0, 2, 4, 5, 7, 9, 11),
    "minor": (0, 2, 3, 5, 7, 8, 10),
}


def _mix_wet_dry(frames: np.ndarray, wet: np.ndarray, mix: float) -> np.ndarray:
    clamped_mix = float(np.clip(mix, 0.0, 1.0))
    return np.ascontiguousarray(frames * (1.0 - clamped_mix) + wet * clamped_mix, dtype=np.float32)


def linear_resample(samples: np.ndarray, target_frames: int) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    target = max(1, int(target_frames))
    if frames.shape[0] == target:
        return frames.copy()

    source_positions = np.linspace(0.0, frames.shape[0] - 1, num=target, dtype=np.float32)
    indices = np.arange(frames.shape[0], dtype=np.float32)
    output = np.empty((target, frames.shape[1]), dtype=np.float32)
    for channel in range(frames.shape[1]):
        output[:, channel] = np.interp(source_positions, indices, frames[:, channel]).astype(np.float32)
    return np.ascontiguousarray(output, dtype=np.float32)


def _stft_channel(signal: np.ndarray, fft_size: int, hop_size: int) -> np.ndarray:
    safe_fft = max(256, int(fft_size))
    safe_hop = max(32, int(hop_size))
    pad = safe_fft // 2
    padded = np.pad(np.asarray(signal, dtype=np.float32), (pad, pad))
    if padded.shape[0] < safe_fft:
        padded = np.pad(padded, (0, safe_fft - padded.shape[0]))
    frame_count = int(np.ceil((padded.shape[0] - safe_fft) / safe_hop)) + 1
    target_length = (frame_count - 1) * safe_hop + safe_fft
    if padded.shape[0] < target_length:
        padded = np.pad(padded, (0, target_length - padded.shape[0]))
    window = np.hanning(safe_fft).astype(np.float32)
    frames = np.lib.stride_tricks.sliding_window_view(padded, safe_fft)[::safe_hop][:frame_count]
    return np.fft.rfft(frames * window[None, :], axis=-1).astype(np.complex64)


def _istft_channel(
    spectrogram: np.ndarray,
    fft_size: int,
    hop_size: int,
    *,
    length: int,
) -> np.ndarray:
    safe_fft = max(256, int(fft_size))
    safe_hop = max(32, int(hop_size))
    window = np.hanning(safe_fft).astype(np.float32)
    time_frames = np.fft.irfft(spectrogram, n=safe_fft, axis=-1).astype(np.float32)
    output_length = safe_hop * max(0, spectrogram.shape[0] - 1) + safe_fft
    output = np.zeros(output_length, dtype=np.float32)
    norm = np.zeros(output_length, dtype=np.float32)
    for frame_index, frame in enumerate(time_frames):
        start = frame_index * safe_hop
        output[start : start + safe_fft] += frame * window
        norm[start : start + safe_fft] += window ** 2
    output /= np.maximum(norm, 1e-6)
    pad = safe_fft // 2
    trimmed = output[pad : pad + max(1, int(length))]
    if trimmed.shape[0] < max(1, int(length)):
        trimmed = np.pad(trimmed, (0, max(1, int(length)) - trimmed.shape[0]))
    return np.ascontiguousarray(trimmed[: max(1, int(length))], dtype=np.float32)


def _phase_vocoder(spectrogram: np.ndarray, rate: float, hop_size: int, fft_size: int) -> np.ndarray:
    safe_rate = max(float(rate), 0.05)
    if spectrogram.shape[0] <= 1:
        return spectrogram.copy()

    time_steps = np.arange(0, spectrogram.shape[0] - 1, safe_rate, dtype=np.float32)
    phase_acc = np.angle(spectrogram[0]).astype(np.float32)
    phase_advance = (2.0 * np.pi * hop_size * np.arange(spectrogram.shape[1], dtype=np.float32) / fft_size)
    output = np.empty((time_steps.shape[0], spectrogram.shape[1]), dtype=np.complex64)

    for index, step in enumerate(time_steps):
        base = int(np.floor(step))
        alpha = float(step - base)
        left = spectrogram[base]
        right = spectrogram[min(base + 1, spectrogram.shape[0] - 1)]
        magnitude = (1.0 - alpha) * np.abs(left) + alpha * np.abs(right)
        delta = np.angle(right) - np.angle(left) - phase_advance
        delta -= 2.0 * np.pi * np.round(delta / (2.0 * np.pi))
        phase_acc += phase_advance + delta
        output[index] = magnitude.astype(np.float32) * np.exp(1j * phase_acc).astype(np.complex64)

    return output


def time_stretch_audio(
    samples: np.ndarray,
    rate: float,
    *,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_rate = max(float(rate), 0.05)
    target_length = max(1, int(round(frames.shape[0] / safe_rate)))
    output = np.empty((target_length, frames.shape[1]), dtype=np.float32)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        stretched = _phase_vocoder(spectrogram, safe_rate, hop_size, fft_size)
        output[:, channel] = _istft_channel(stretched, fft_size, hop_size, length=target_length)
    return np.ascontiguousarray(output, dtype=np.float32)


def pitch_shift_audio(
    samples: np.ndarray,
    sample_rate: int,
    semitones: float,
    *,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if abs(float(semitones)) < 1e-4:
        return frames.copy()
    ratio = float(2.0 ** (float(semitones) / 12.0))
    stretched = time_stretch_audio(frames, 1.0 / ratio, fft_size=fft_size, hop_size=hop_size)
    _ = sample_rate
    return linear_resample(stretched, frames.shape[0])


def harmonizer_audio(
    samples: np.ndarray,
    sample_rate: int,
    intervals_semitones: Iterable[float],
    *,
    mix: float = 0.35,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    intervals = [float(value) for value in intervals_semitones]
    if not intervals:
        return frames.copy()
    wet = frames.astype(np.float32)
    for semitones in intervals:
        wet += pitch_shift_audio(frames, sample_rate, semitones, fft_size=fft_size, hop_size=hop_size)
    wet /= float(len(intervals) + 1)
    return _mix_wet_dry(frames, wet.astype(np.float32), mix)


def octaver_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    octaves_down: int = 1,
    octaves_up: int = 0,
    down_mix: float = 0.45,
    up_mix: float = 0.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    wet = frames.copy()
    if octaves_down > 0:
        wet += pitch_shift_audio(
            frames,
            sample_rate,
            -12.0 * max(1, int(octaves_down)),
            fft_size=fft_size,
            hop_size=hop_size,
        ) * float(np.clip(down_mix, 0.0, 1.0))
    if octaves_up > 0:
        wet += pitch_shift_audio(
            frames,
            sample_rate,
            12.0 * max(1, int(octaves_up)),
            fft_size=fft_size,
            hop_size=hop_size,
        ) * float(np.clip(up_mix, 0.0, 1.0))
    wet /= 1.0 + float(np.clip(down_mix, 0.0, 1.0)) + float(np.clip(up_mix, 0.0, 1.0))
    return np.ascontiguousarray(wet, dtype=np.float32)


def formant_shift_audio(
    samples: np.ndarray,
    sample_rate: int,
    shift: float,
    *,
    mix: float = 1.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_shift = float(np.clip(shift, 0.5, 2.0))
    if abs(safe_shift - 1.0) < 1e-4:
        return frames.copy()
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram)
        phase = np.angle(spectrogram)
        bins = np.arange(magnitude.shape[1], dtype=np.float32)
        shifted_magnitude = np.empty_like(magnitude, dtype=np.float32)
        source_bins = bins / safe_shift
        for frame_index in range(magnitude.shape[0]):
            shifted_magnitude[frame_index] = np.interp(
                bins,
                bins,
                np.interp(source_bins, bins, magnitude[frame_index], left=0.0, right=0.0),
            ).astype(np.float32)
        shifted = shifted_magnitude * np.exp(1j * phase).astype(np.complex64)
        reconstructed = _istft_channel(shifted, fft_size, hop_size, length=frames.shape[0])
        output[:, channel] = reconstructed
    return _mix_wet_dry(frames, output.astype(np.float32), mix)


def _make_soft_band_mask(
    sample_rate: int,
    bin_count: int,
    low_hz: float,
    high_hz: float,
    *,
    transition_hz: float = 220.0,
) -> np.ndarray:
    freqs = np.linspace(0.0, sample_rate * 0.5, num=bin_count, dtype=np.float32)
    safe_transition = max(float(transition_hz), 1.0)
    low_ramp = np.clip((freqs - (float(low_hz) - safe_transition)) / safe_transition, 0.0, 1.0)
    high_ramp = np.clip(((float(high_hz) + safe_transition) - freqs) / safe_transition, 0.0, 1.0)
    return np.ascontiguousarray(low_ramp * high_ramp, dtype=np.float32)


def _smooth_time_iir(magnitude: np.ndarray, alpha: float) -> np.ndarray:
    frames = np.asarray(magnitude, dtype=np.float32)
    if frames.shape[0] == 0:
        return frames.copy()
    safe_alpha = float(np.clip(alpha, 0.0, 0.9999))
    output = np.empty_like(frames)
    state = frames[0].copy()
    output[0] = state
    for index in range(1, frames.shape[0]):
        state = safe_alpha * state + (1.0 - safe_alpha) * frames[index]
        output[index] = state
    return output


def _smooth_bidirectional(magnitude: np.ndarray, alpha: float) -> np.ndarray:
    forward = _smooth_time_iir(magnitude, alpha)
    backward = _smooth_time_iir(magnitude[::-1], alpha)[::-1]
    return np.ascontiguousarray((forward + backward) * 0.5, dtype=np.float32)


def _smooth_over_frequency(magnitude: np.ndarray, width: int = 5) -> np.ndarray:
    frames = np.asarray(magnitude, dtype=np.float32)
    safe_width = max(3, int(width) | 1)
    radius = safe_width // 2
    weights = np.arange(1, radius + 2, dtype=np.float32)
    kernel = np.concatenate([weights, weights[-2::-1]])
    kernel /= float(np.sum(kernel))
    padded = np.pad(frames, ((0, 0), (radius, radius)), mode="edge")
    output = np.zeros_like(frames)
    for offset, weight in enumerate(kernel):
        output += padded[:, offset : offset + frames.shape[1]] * float(weight)
    return np.ascontiguousarray(output, dtype=np.float32)


def _harmonic_percussive_masks(
    magnitude: np.ndarray,
    *,
    harmonic_alpha: float = 0.92,
    percussive_width: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    harmonic = _smooth_bidirectional(magnitude, harmonic_alpha)
    percussive = _smooth_over_frequency(magnitude, width=percussive_width)
    denominator = harmonic + percussive + 1e-6
    harmonic_mask = harmonic / denominator
    percussive_mask = percussive / denominator
    return (
        np.ascontiguousarray(harmonic_mask.astype(np.float32), dtype=np.float32),
        np.ascontiguousarray(percussive_mask.astype(np.float32), dtype=np.float32),
    )


def _center_mono(samples: np.ndarray) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if frames.shape[1] >= 2:
        return np.mean(frames[:, :2], axis=1, dtype=np.float32)
    return frames[:, 0].astype(np.float32, copy=True)


def _expand_mono(mono: np.ndarray, channels: int) -> np.ndarray:
    signal = np.asarray(mono, dtype=np.float32)[:, None]
    return np.ascontiguousarray(np.repeat(signal, max(1, int(channels)), axis=1), dtype=np.float32)


def _estimate_pitch_track(
    signal: np.ndarray,
    sample_rate: int,
    *,
    frame_length: int,
    hop_length: int,
    min_hz: float,
    max_hz: float,
) -> np.ndarray:
    safe_frame = max(1024, int(frame_length))
    safe_hop = max(128, int(hop_length))
    spectrogram = _stft_channel(np.asarray(signal, dtype=np.float32), safe_frame, safe_hop)
    magnitude = np.abs(spectrogram).astype(np.float32)
    if magnitude.shape[0] == 0:
        return np.zeros(0, dtype=np.float32)

    freqs = np.fft.rfftfreq(safe_frame, d=1.0 / float(sample_rate)).astype(np.float32)
    low_bin = max(1, int(np.searchsorted(freqs, float(min_hz), side="left")))
    high_bin = min(magnitude.shape[1] - 1, int(np.searchsorted(freqs, float(max_hz), side="right")) - 1)
    max_base = min(high_bin, (magnitude.shape[1] - 1) // 3)
    if max_base <= low_bin:
        return np.zeros(magnitude.shape[0], dtype=np.float32)

    candidate_bins = np.arange(low_bin, max_base + 1, dtype=np.int32)
    score = magnitude[:, candidate_bins].astype(np.float32)
    score += magnitude[:, np.minimum(candidate_bins * 2, magnitude.shape[1] - 1)] * 0.65
    score += magnitude[:, np.minimum(candidate_bins * 3, magnitude.shape[1] - 1)] * 0.35
    score /= np.maximum(np.sqrt(freqs[candidate_bins]).astype(np.float32)[None, :], 1.0)

    energy = np.mean(magnitude[:, candidate_bins], axis=1)
    voiced_threshold = float(np.percentile(energy, 45.0))
    best_indices = np.argmax(score, axis=1)
    pitches = np.zeros(magnitude.shape[0], dtype=np.float32)
    voiced = energy > voiced_threshold
    if np.any(voiced):
        pitches[voiced] = freqs[candidate_bins[best_indices[voiced]]]
    return np.ascontiguousarray(pitches, dtype=np.float32)


def _nearest_scale_midi(midi_value: float, key: str, scale: str) -> float:
    key_pc = _NOTE_TO_SEMITONE.get(key.strip().upper(), 0)
    intervals = _SCALE_INTERVALS.get(scale.strip().lower(), _SCALE_INTERVALS["chromatic"])
    allowed = {(key_pc + interval) % 12 for interval in intervals}
    base_octave = int(np.floor(float(midi_value) / 12.0))
    candidates: list[float] = []
    for octave in range(base_octave - 1, base_octave + 2):
        for pitch_class in allowed:
            candidates.append(float(octave * 12 + pitch_class))
    return min(candidates, key=lambda value: abs(value - midi_value))


def auto_tune_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    strength: float = 0.7,
    key: str = "C",
    scale: str = "chromatic",
    min_hz: float = 80.0,
    max_hz: float = 1_000.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    mono = _center_mono(frames)
    track = _estimate_pitch_track(
        mono,
        sample_rate,
        frame_length=1024,
        hop_length=max(256, hop_size),
        min_hz=min_hz,
        max_hz=max_hz,
    )
    voiced = track[track > 0.0]
    if voiced.size == 0:
        return frames.copy()
    midi = 69.0 + 12.0 * np.log2(voiced / 440.0)
    source_midi = float(np.median(midi))
    target_midi = _nearest_scale_midi(source_midi, key, scale)
    semitone_shift = (target_midi - source_midi) * float(np.clip(strength, 0.0, 1.0))
    return pitch_shift_audio(frames, sample_rate, semitone_shift, fft_size=fft_size, hop_size=hop_size)

def _extract_vocal_mono(
    samples: np.ndarray,
    sample_rate: int,
    *,
    strength: float,
    low_hz: float,
    high_hz: float,
    noise_strength: float,
    dereverb_amount: float,
    repair_strength: float,
    presence_boost: float,
    center_bias: float,
    percussion_suppression: float,
    fft_size: int,
    hop_size: int,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    mono = _center_mono(frames)
    safe_strength = float(np.clip(strength, 0.0, 1.0))
    safe_noise = float(np.clip(noise_strength, 0.0, 1.0))
    safe_dereverb = float(np.clip(dereverb_amount, 0.0, 1.0))
    safe_repair = float(np.clip(repair_strength, 0.0, 1.0))
    safe_presence = float(np.clip(presence_boost, 0.0, 1.0))
    safe_center = float(np.clip(center_bias, 0.0, 1.0))
    safe_percussion = float(np.clip(percussion_suppression, 0.0, 1.0))

    if frames.shape[1] >= 2:
        left_spec = _stft_channel(frames[:, 0], fft_size, hop_size)
        right_spec = _stft_channel(frames[:, 1], fft_size, hop_size)
        center_spec = (left_spec + right_spec) * 0.5
        side_spec = (left_spec - right_spec) * 0.5
        spectrogram = center_spec
        side_magnitude = np.abs(side_spec).astype(np.float32)
    else:
        spectrogram = _stft_channel(mono, fft_size, hop_size)
        side_magnitude = np.zeros_like(spectrogram.real, dtype=np.float32)

    magnitude = np.abs(spectrogram).astype(np.float32)
    phase = np.angle(spectrogram)
    band_mask = _make_soft_band_mask(sample_rate, magnitude.shape[1], low_hz, high_hz, transition_hz=320.0)
    speech_mask = _make_soft_band_mask(sample_rate, magnitude.shape[1], 180.0, 4_200.0, transition_hz=450.0)
    harmonic_mask, percussive_mask = _harmonic_percussive_masks(
        magnitude,
        harmonic_alpha=0.90 + 0.05 * safe_strength,
        percussive_width=7,
    )
    center_ratio = magnitude / (magnitude + side_magnitude * (0.65 - 0.22 * safe_strength) + 1e-6)
    center_ratio = np.power(np.clip(center_ratio, 0.0, 1.0), 0.65 + 0.95 * safe_center).astype(np.float32)

    noise_floor = np.percentile(magnitude, 10.0, axis=0).astype(np.float32)
    noise_mask = np.clip(
        (magnitude - noise_floor[None, :] * (0.55 + 0.95 * safe_noise)) / (magnitude + 1e-6),
        0.0,
        1.0,
    ).astype(np.float32)
    speech_focus = np.sqrt(np.maximum(speech_mask[None, :] * harmonic_mask, 1e-5)).astype(np.float32)
    percussive_reject = np.clip(1.0 - percussive_mask * (0.20 + 0.70 * safe_percussion), 0.04, 1.0).astype(np.float32)
    band_focus = np.power(np.maximum(band_mask[None, :], 1e-4), 0.35 + 0.55 * safe_strength).astype(np.float32)
    harmonic_focus = np.clip(harmonic_mask * (0.88 + 0.26 * safe_strength), 0.0, 1.0).astype(np.float32)

    mask = (
        band_focus
        * (0.12 + 0.88 * center_ratio)
        * (0.10 + 0.90 * speech_focus)
        * (0.10 + 0.90 * harmonic_focus)
        * percussive_reject
        * (0.16 + 0.84 * noise_mask)
    ).astype(np.float32)

    if safe_repair > 0.0:
        mask = mask * (1.0 - 0.55 * safe_repair) + _smooth_over_frequency(mask, width=5) * (0.55 * safe_repair)
    if safe_dereverb > 0.0:
        mask = np.minimum(mask, _smooth_time_iir(mask, 0.93) * (0.90 - 0.22 * safe_dereverb) + mask * (0.10 + 0.22 * safe_dereverb))

    mask = np.clip(mask, 0.0, 1.0).astype(np.float32)
    restored_magnitude = magnitude * mask
    if safe_presence > 0.0:
        restored_magnitude *= 1.0 + speech_mask[None, :] * (0.05 + 0.22 * safe_presence)
        restored_magnitude = np.minimum(restored_magnitude, magnitude * (0.92 + 0.18 * safe_presence))

    restored = restored_magnitude * np.exp(1j * phase).astype(np.complex64)
    return _istft_channel(restored, fft_size, hop_size, length=len(mono))


def noise_reduction_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    strength: float = 0.5,
    noise_percentile: float = 10.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_strength = float(np.clip(strength, 0.0, 1.0))
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram)
        phase = np.angle(spectrogram)
        noise_profile = np.percentile(magnitude, np.clip(noise_percentile, 1.0, 50.0), axis=0).astype(np.float32)
        attenuation = np.clip(1.0 - safe_strength * noise_profile[None, :] / (magnitude + 1e-6), 0.08, 1.0)
        cleaned = magnitude * attenuation
        restored = cleaned * np.exp(1j * phase).astype(np.complex64)
        output[:, channel] = _istft_channel(restored, fft_size, hop_size, length=frames.shape[0])
    _ = sample_rate
    return np.ascontiguousarray(output, dtype=np.float32)


def voice_isolation_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    strength: float = 0.75,
    low_hz: float = 120.0,
    high_hz: float = 5_200.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    isolated_mono = _extract_vocal_mono(
        frames,
        sample_rate,
        strength=float(np.clip(strength, 0.0, 1.0)),
        low_hz=low_hz,
        high_hz=high_hz,
        noise_strength=0.20 + 0.28 * float(np.clip(strength, 0.0, 1.0)),
        dereverb_amount=0.10 + 0.20 * float(np.clip(strength, 0.0, 1.0)),
        repair_strength=0.04 + 0.10 * float(np.clip(strength, 0.0, 1.0)),
        presence_boost=0.10 + 0.16 * float(np.clip(strength, 0.0, 1.0)),
        center_bias=0.70 + 0.18 * float(np.clip(strength, 0.0, 1.0)),
        percussion_suppression=0.55 + 0.25 * float(np.clip(strength, 0.0, 1.0)),
        fft_size=fft_size,
        hop_size=hop_size,
    )
    return _expand_mono(isolated_mono, frames.shape[1])


def source_separation_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    target: str = "vocals",
    strength: float = 0.8,
    low_hz: float = 120.0,
    high_hz: float = 5_200.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_strength = float(np.clip(strength, 0.0, 1.0))
    isolated_mono = _extract_vocal_mono(
        frames,
        sample_rate,
        strength=min(1.0, safe_strength + 0.08),
        low_hz=low_hz,
        high_hz=high_hz,
        noise_strength=0.25 + safe_strength * 0.30,
        dereverb_amount=0.16 + safe_strength * 0.22,
        repair_strength=0.05 + safe_strength * 0.12,
        presence_boost=0.14 + safe_strength * 0.18,
        center_bias=0.82 + safe_strength * 0.16,
        percussion_suppression=0.72 + safe_strength * 0.22,
        fft_size=fft_size,
        hop_size=hop_size,
    )
    vocals = _expand_mono(isolated_mono, frames.shape[1])
    if target.strip().lower() in {"instrumental", "accompaniment", "music"}:
        return np.ascontiguousarray(frames - vocals * safe_strength, dtype=np.float32)
    return np.ascontiguousarray(vocals, dtype=np.float32)


def de_reverb_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    amount: float = 0.45,
    tail_ms: float = 240.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    decay = float(np.exp(-hop_size / max(1.0, sample_rate * max(tail_ms, 10.0) / 1000.0)))
    safe_amount = float(np.clip(amount, 0.0, 1.0))
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram).astype(np.float32)
        phase = np.angle(spectrogram)
        late = np.zeros_like(magnitude)
        state = magnitude[0].copy()
        late[0] = state
        for frame_index in range(1, magnitude.shape[0]):
            state = np.maximum(state * decay, magnitude[frame_index] * 0.82)
            late[frame_index] = state
        cleaned = np.maximum(magnitude - late * safe_amount * 0.35, 0.0)
        restored = cleaned * np.exp(1j * phase).astype(np.complex64)
        output[:, channel] = _istft_channel(restored, fft_size, hop_size, length=frames.shape[0])
    return np.ascontiguousarray(output, dtype=np.float32)


def de_echo_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    amount: float = 0.45,
    min_delay_ms: float = 60.0,
    max_delay_ms: float = 800.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    mono = np.mean(frames, axis=1, dtype=np.float32)
    downsample = max(1, sample_rate // 8_000)
    reduced = mono[::downsample]
    correlation_size = 1 << int(np.ceil(np.log2(max(2, reduced.shape[0] * 2 - 1))))
    spectrum = np.fft.rfft(reduced, correlation_size)
    autocorr = np.fft.irfft(spectrum * np.conj(spectrum), correlation_size)[: reduced.shape[0]]
    lag_min = max(1, int(min_delay_ms * sample_rate / 1000.0 / downsample))
    lag_max = min(reduced.shape[0] - 1, int(max_delay_ms * sample_rate / 1000.0 / downsample))
    if lag_max <= lag_min:
        return frames.copy()
    best = int(np.argmax(autocorr[lag_min : lag_max + 1])) + lag_min
    delay_samples = best * downsample
    if delay_samples <= 0 or delay_samples >= frames.shape[0]:
        return frames.copy()
    echo_ratio = float(np.clip(autocorr[best] / max(float(autocorr[0]), 1e-6), 0.0, 0.95))
    cancellation = float(np.clip(amount, 0.0, 1.0)) * echo_ratio * 0.75
    output = frames.copy()
    output[delay_samples:] -= frames[:-delay_samples] * cancellation
    return np.ascontiguousarray(output, dtype=np.float32)


def spectral_repair_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    strength: float = 0.35,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_strength = float(np.clip(strength, 0.0, 1.0))
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram).astype(np.float32)
        phase = np.angle(spectrogram)
        repaired = magnitude * (1.0 - safe_strength) + (
            0.55 * _smooth_bidirectional(magnitude, 0.78)
            + 0.45 * _smooth_over_frequency(magnitude, width=5)
        ) * safe_strength
        restored = repaired * np.exp(1j * phase).astype(np.complex64)
        output[:, channel] = _istft_channel(restored, fft_size, hop_size, length=frames.shape[0])
    _ = sample_rate
    return np.ascontiguousarray(output, dtype=np.float32)


def speech_enhancement_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    amount: float = 0.7,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_amount = float(np.clip(amount, 0.0, 1.0))
    speech_mono = _extract_vocal_mono(
        frames,
        sample_rate,
        strength=0.55 + safe_amount * 0.35,
        low_hz=110.0,
        high_hz=5_600.0,
        noise_strength=0.3 + safe_amount * 0.28,
        dereverb_amount=0.18 + safe_amount * 0.28,
        repair_strength=0.12 + safe_amount * 0.18,
        presence_boost=0.2 + safe_amount * 0.25,
        center_bias=0.45 + safe_amount * 0.22,
        percussion_suppression=0.38 + safe_amount * 0.20,
        fft_size=fft_size,
        hop_size=hop_size,
    )
    speech = _expand_mono(speech_mono, frames.shape[1])
    return _mix_wet_dry(frames, speech, 0.4 + safe_amount * 0.45)


def ai_enhancer_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    amount: float = 0.6,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_amount = float(np.clip(amount, 0.0, 1.0))
    vocal_mono = _extract_vocal_mono(
        frames,
        sample_rate,
        strength=0.42 + safe_amount * 0.3,
        low_hz=100.0,
        high_hz=6_800.0,
        noise_strength=0.22 + safe_amount * 0.22,
        dereverb_amount=0.12 + safe_amount * 0.2,
        repair_strength=0.1 + safe_amount * 0.2,
        presence_boost=0.12 + safe_amount * 0.18,
        center_bias=0.32 + safe_amount * 0.18,
        percussion_suppression=0.26 + safe_amount * 0.14,
        fft_size=fft_size,
        hop_size=hop_size,
    )
    enhanced = frames * (0.88 - safe_amount * 0.12) + _expand_mono(vocal_mono, frames.shape[1]) * (0.12 + safe_amount * 0.28)
    return _mix_wet_dry(frames, enhanced, 0.45 + safe_amount * 0.35)


def fft_filter_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    low_hz: float = 80.0,
    high_hz: float = 12_000.0,
    mix: float = 1.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        band = _make_soft_band_mask(sample_rate, spectrogram.shape[1], low_hz, high_hz, transition_hz=280.0)
        filtered = spectrogram * band[None, :].astype(np.complex64)
        output[:, channel] = _istft_channel(filtered, fft_size, hop_size, length=frames.shape[0])
    return _mix_wet_dry(frames, output, mix)


def spectral_gating_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    threshold_db: float = -42.0,
    floor: float = 0.08,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    threshold_linear = float(10.0 ** (float(threshold_db) / 20.0))
    safe_floor = float(np.clip(floor, 0.0, 1.0))
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram).astype(np.float32)
        phase = np.angle(spectrogram)
        gate = np.where(magnitude >= threshold_linear, 1.0, safe_floor).astype(np.float32)
        restored = (magnitude * gate) * np.exp(1j * phase).astype(np.complex64)
        output[:, channel] = _istft_channel(restored, fft_size, hop_size, length=frames.shape[0])
    _ = sample_rate
    return np.ascontiguousarray(output, dtype=np.float32)


def spectral_blur_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    amount: float = 0.45,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_amount = float(np.clip(amount, 0.0, 1.0))
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram).astype(np.float32)
        phase = np.angle(spectrogram)
        blurred = (_smooth_bidirectional(magnitude, 0.82) + _smooth_over_frequency(magnitude, width=7)) * 0.5
        morphed = magnitude * (1.0 - safe_amount) + blurred * safe_amount
        restored = morphed * np.exp(1j * phase).astype(np.complex64)
        output[:, channel] = _istft_channel(restored, fft_size, hop_size, length=frames.shape[0])
    _ = sample_rate
    return np.ascontiguousarray(output, dtype=np.float32)


def spectral_freeze_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    start_ms: float = 120.0,
    mix: float = 0.7,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    freeze_index = max(0, int(round(float(start_ms) * sample_rate / 1000.0 / max(hop_size, 1))))
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram).astype(np.float32)
        phase = np.angle(spectrogram)
        reference = magnitude[min(freeze_index, magnitude.shape[0] - 1)]
        frozen = magnitude.copy()
        frozen[min(freeze_index, magnitude.shape[0] - 1) :] = (
            magnitude[min(freeze_index, magnitude.shape[0] - 1) :] * (1.0 - mix)
            + reference[None, :] * mix
        )
        restored = frozen * np.exp(1j * phase).astype(np.complex64)
        output[:, channel] = _istft_channel(restored, fft_size, hop_size, length=frames.shape[0])
    return np.ascontiguousarray(output, dtype=np.float32)


def spectral_morphing_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    amount: float = 0.5,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_amount = float(np.clip(amount, 0.0, 1.0))
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram).astype(np.float32)
        phase = np.angle(spectrogram)
        target = np.mean(magnitude, axis=0, dtype=np.float32)
        morphed = magnitude * (1.0 - safe_amount) + target[None, :] * safe_amount
        restored = morphed * np.exp(1j * phase).astype(np.complex64)
        output[:, channel] = _istft_channel(restored, fft_size, hop_size, length=frames.shape[0])
    _ = sample_rate
    return np.ascontiguousarray(output, dtype=np.float32)


def phase_vocoder_audio(
    samples: np.ndarray,
    *,
    rate: float = 0.85,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    return time_stretch_audio(samples, rate=rate, fft_size=fft_size, hop_size=hop_size)


def harmonic_percussive_separation_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    target: str = "harmonic",
    mix: float = 1.0,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    use_harmonic = target.strip().lower() not in {"percussive", "drums", "transient"}
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        magnitude = np.abs(spectrogram).astype(np.float32)
        phase = np.angle(spectrogram)
        harmonic_mask, percussive_mask = _harmonic_percussive_masks(magnitude)
        mask = harmonic_mask if use_harmonic else percussive_mask
        restored = (magnitude * mask) * np.exp(1j * phase).astype(np.complex64)
        output[:, channel] = _istft_channel(restored, fft_size, hop_size, length=frames.shape[0])
    _ = sample_rate
    return _mix_wet_dry(frames, output, mix)


def spectral_delay_audio(
    samples: np.ndarray,
    sample_rate: int,
    *,
    max_delay_ms: float = 240.0,
    feedback: float = 0.15,
    mix: float = 0.35,
    fft_size: int = 2048,
    hop_size: int = 512,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    band_groups = 32
    max_delay_frames = max(1, int(round(float(max_delay_ms) * sample_rate / 1000.0 / max(hop_size, 1))))
    output = np.empty_like(frames)
    for channel in range(frames.shape[1]):
        spectrogram = _stft_channel(frames[:, channel], fft_size, hop_size)
        wet = np.array(spectrogram, copy=True)
        bins_per_group = max(1, int(np.ceil(spectrogram.shape[1] / band_groups)))
        for group in range(band_groups):
            start = group * bins_per_group
            end = min(spectrogram.shape[1], start + bins_per_group)
            if start >= end:
                break
            delay_frames = int(round(max_delay_frames * (group / max(1, band_groups - 1))))
            if delay_frames <= 0 or delay_frames >= spectrogram.shape[0]:
                continue
            wet[delay_frames:, start:end] += spectrogram[:-delay_frames, start:end] * float(np.clip(feedback, 0.0, 0.95))
        output[:, channel] = _istft_channel(wet, fft_size, hop_size, length=frames.shape[0])
    return _mix_wet_dry(frames, output, mix)

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from ._creative import (
    alien_voice_audio,
    glitch_audio,
    granular_synthesis_audio,
    radio_effect_audio,
    random_pitch_mod_audio,
    retro_8bit_audio,
    reverse_reverb_audio,
    robot_voice_audio,
    slow_motion_extreme_audio,
    stutter_audio,
    tape_stop_audio,
    telephone_effect_audio,
    time_slicing_audio,
    vinyl_effect_audio,
)
from ._spatial import (
    binaural_effect_audio,
    hrtf_simulation_audio,
    mid_side_processing_audio,
    spatial_positioning_audio,
    stereo_imager_audio,
    stereo_widening_audio,
)
from ._spectral import (
    ai_enhancer_audio,
    auto_tune_audio,
    de_echo_audio,
    de_reverb_audio,
    fft_filter_audio,
    formant_shift_audio,
    harmonic_percussive_separation_audio,
    harmonizer_audio,
    noise_reduction_audio,
    octaver_audio,
    phase_vocoder_audio,
    pitch_shift_audio,
    spectral_blur_audio,
    spectral_delay_audio,
    spectral_freeze_audio,
    spectral_gating_audio,
    spectral_morphing_audio,
    source_separation_audio,
    spectral_repair_audio,
    speech_enhancement_audio,
    time_stretch_audio,
    voice_isolation_audio,
)
from ._util import ensure_float32_frames
from .effects import Automation, Effect

PYTHON_ONLY_EFFECT_TYPES = {
    "multi_tap_delay",
    "early_reflections",
    "room_reverb",
    "hall_reverb",
    "plate_reverb",
    "convolution_reverb",
    "ring_modulation",
    "frequency_shifter",
    "overdrive",
    "fuzz",
    "bitcrusher",
    "waveshaper",
    "tube_saturation",
    "tape_saturation",
    "soft_clipping",
    "pitch_shift",
    "time_stretch",
    "auto_tune",
    "harmonizer",
    "octaver",
    "formant_shifting",
    "noise_reduction",
    "voice_isolation",
    "source_separation",
    "de_reverb",
    "de_echo",
    "spectral_repair",
    "ai_enhancer",
    "speech_enhancement",
    "glitch_effect",
    "stutter",
    "tape_stop",
    "reverse_reverb",
    "granular_synthesis",
    "time_slicing",
    "random_pitch_mod",
    "vinyl_effect",
    "radio_effect",
    "telephone_effect",
    "retro_8bit",
    "slow_motion_extreme",
    "robot_voice",
    "alien_voice",
    "fft_filter",
    "spectral_gating",
    "spectral_blur",
    "spectral_freeze",
    "spectral_morphing",
    "phase_vocoder",
    "harmonic_percussive_separation",
    "spectral_delay",
    "stereo_widening",
    "mid_side_processing",
    "stereo_imager",
    "binaural_effect",
    "spatial_positioning",
    "hrtf_simulation",
}


def requires_python_processing(effect: Effect) -> bool:
    return effect.type in PYTHON_ONLY_EFFECT_TYPES or effect.has_dynamic_params()


def evaluate_param(value: Any, time_seconds: float) -> float:
    if isinstance(value, Automation):
        return value.evaluate(time_seconds)
    return float(value)


def _estimate_max_param_ms(value: Any, duration_seconds: float) -> float:
    if isinstance(value, Automation):
        points = np.linspace(0.0, duration_seconds, num=33, dtype=np.float32)
        return max(0.001, max(float(value.evaluate(float(point))) for point in points))
    return max(0.001, float(value))


def _linear_read(buffer: np.ndarray, channel: int, write_index: int, delay_samples: float) -> float:
    length = buffer.shape[0]
    read_position = write_index - delay_samples
    base_index = int(np.floor(read_position))
    fraction = read_position - base_index
    newer = buffer[base_index % length, channel]
    older = buffer[(base_index - 1) % length, channel]
    return float(newer * (1.0 - fraction) + older * fraction)


def _variable_delay(
    samples: np.ndarray,
    sample_rate: int,
    delay_ms: float | Automation,
    *,
    mix: float,
    feedback: float = 0.0,
    cross_feedback: bool = False,
    wet_only: bool = False,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    frame_count, channels = frames.shape
    duration_seconds = frame_count / float(sample_rate)
    max_delay_ms = _estimate_max_param_ms(delay_ms, duration_seconds) + 20.0
    max_delay_samples = max(4, int(np.ceil(max_delay_ms * sample_rate / 1000.0)) + 4)

    delay_buffer = np.zeros((max_delay_samples, channels), dtype=np.float32)
    output = np.empty_like(frames)
    write_index = 0

    for frame_index in range(frame_count):
        time_seconds = frame_index / float(sample_rate)
        current_delay_ms = max(0.001, evaluate_param(delay_ms, time_seconds))
        current_delay_samples = max(1.0, current_delay_ms * sample_rate / 1000.0)

        delayed = np.empty(channels, dtype=np.float32)
        for channel in range(channels):
            delayed[channel] = _linear_read(delay_buffer, channel, write_index, current_delay_samples)

        wet = delayed.copy()
        if cross_feedback and channels >= 2:
            wet[0] = delayed[1]
            wet[1] = delayed[0]

        if wet_only:
            output[frame_index] = wet
        else:
            output[frame_index] = frames[frame_index] * (1.0 - mix) + wet * mix

        for channel in range(channels):
            if cross_feedback and channels >= 2:
                feedback_source = delayed[1 - channel] if channel < 2 else delayed[channel]
            else:
                feedback_source = delayed[channel]
            delay_buffer[write_index, channel] = frames[frame_index, channel] + feedback_source * feedback

        write_index = (write_index + 1) % max_delay_samples

    return np.ascontiguousarray(output, dtype=np.float32)


def _multi_tap_impulse(
    sample_rate: int,
    *,
    channels: int,
    base_delay_ms: float,
    taps: int,
    spacing_ms: float,
    decay: float,
) -> np.ndarray:
    tap_count = max(1, int(taps))
    max_delay_ms = base_delay_ms + max(0, tap_count - 1) * spacing_ms + 5.0
    length = max(2, int(np.ceil(max_delay_ms * sample_rate / 1000.0)) + 1)
    impulse = np.zeros((length, channels), dtype=np.float32)

    for tap_index in range(tap_count):
        delay_ms = max(0.001, base_delay_ms + tap_index * spacing_ms)
        frame = min(length - 1, int(round(delay_ms * sample_rate / 1000.0)))
        amplitude = float(decay ** tap_index)
        impulse[frame, :] += amplitude

    return impulse


def _early_reflections_impulse(
    sample_rate: int,
    *,
    channels: int,
    pre_delay_ms: float,
    spread_ms: float,
    taps: int,
    decay: float,
) -> np.ndarray:
    tap_count = max(1, int(taps))
    max_delay_ms = pre_delay_ms + tap_count * spread_ms + 4.0
    length = max(4, int(np.ceil(max_delay_ms * sample_rate / 1000.0)) + 1)
    impulse = np.zeros((length, channels), dtype=np.float32)

    for tap_index in range(tap_count):
        delay_ms = pre_delay_ms + tap_index * spread_ms
        frame = min(length - 1, int(round(delay_ms * sample_rate / 1000.0)))
        amplitude = float((decay ** tap_index) * (1.0 - 0.08 * tap_index))
        impulse[frame, :] += amplitude

    if channels >= 2:
        impulse[:, 1] = np.roll(impulse[:, 1], 2)

    return impulse


def _lowpass_noise(signal: np.ndarray, sample_rate: int, cutoff_hz: float) -> np.ndarray:
    if cutoff_hz <= 0.0:
        return signal

    alpha = min(0.999, 2.0 * np.pi * cutoff_hz / max(sample_rate, 1))
    alpha = float(alpha / (alpha + 1.0))
    output = np.empty_like(signal)
    output[0] = signal[0]
    for index in range(1, signal.shape[0]):
        output[index] = output[index - 1] + alpha * (signal[index] - output[index - 1])
    return output


def _synthetic_reverb_impulse(
    kind: str,
    sample_rate: int,
    *,
    channels: int,
    decay_seconds: float,
    tone_hz: float,
) -> np.ndarray:
    generator = np.random.default_rng(12345)
    length = max(64, int(sample_rate * max(decay_seconds, 0.05)))
    time_axis = np.arange(length, dtype=np.float32) / sample_rate
    decay_curve = np.exp(-time_axis / max(decay_seconds, 0.05)).astype(np.float32)

    noise = generator.normal(0.0, 1.0, size=(length, channels)).astype(np.float32)
    shaped = np.empty_like(noise)
    for channel in range(channels):
        shaped[:, channel] = _lowpass_noise(noise[:, channel], sample_rate, tone_hz)

    if kind == "room_reverb":
        early = _early_reflections_impulse(
            sample_rate,
            channels=channels,
            pre_delay_ms=8.0,
            spread_ms=7.0,
            taps=5,
            decay=0.72,
        )
        modulation = 1.1
    elif kind == "hall_reverb":
        early = _early_reflections_impulse(
            sample_rate,
            channels=channels,
            pre_delay_ms=18.0,
            spread_ms=11.0,
            taps=8,
            decay=0.82,
        )
        modulation = 1.35
    else:
        early = _early_reflections_impulse(
            sample_rate,
            channels=channels,
            pre_delay_ms=10.0,
            spread_ms=5.5,
            taps=7,
            decay=0.76,
        )
        modulation = 0.95

    impulse = shaped * decay_curve[:, None] * modulation
    impulse[0, :] += 1.0
    impulse[: early.shape[0], :] += early

    peak = float(np.max(np.abs(impulse)))
    if peak > 0.0:
        impulse /= peak

    return np.ascontiguousarray(impulse, dtype=np.float32)


def _prepare_impulse_response(
    impulse_response: Any,
    *,
    sample_rate: int,
    channels: int,
    normalize_ir: bool,
) -> np.ndarray:
    if isinstance(impulse_response, (str, Path)):
        from .ffmpeg import decode_audio

        ir, metadata = decode_audio(impulse_response, sample_rate=sample_rate, channels=channels)
        prepared = ir
        if metadata.channels != channels and metadata.channels == 1:
            prepared = np.repeat(prepared, channels, axis=1)
    else:
        prepared = ensure_float32_frames(np.asarray(impulse_response, dtype=np.float32))
        if prepared.shape[1] == 1 and channels > 1:
            prepared = np.repeat(prepared, channels, axis=1)
        elif prepared.shape[1] != channels:
            raise ValueError(
                f"Impulse response channels ({prepared.shape[1]}) do not match audio channels ({channels})."
            )

    if normalize_ir:
        peak = float(np.max(np.abs(prepared)))
        if peak > 0.0:
            prepared = prepared / peak

    return np.ascontiguousarray(prepared, dtype=np.float32)


def _fft_convolve_same(samples: np.ndarray, impulse_response: np.ndarray, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    ir = ensure_float32_frames(impulse_response)
    frame_count, channels = frames.shape
    ir_channels = ir.shape[1]
    output = np.empty_like(frames)

    for channel in range(channels):
        ir_channel = min(channel, ir_channels - 1)
        signal = frames[:, channel]
        kernel = ir[:, ir_channel]
        fft_size = 1 << (int(np.ceil(np.log2(signal.size + kernel.size - 1))))
        signal_fft = np.fft.rfft(signal, fft_size)
        kernel_fft = np.fft.rfft(kernel, fft_size)
        wet = np.fft.irfft(signal_fft * kernel_fft, fft_size)[:frame_count].astype(np.float32)
        output[:, channel] = signal * (1.0 - mix) + wet * mix

    return np.ascontiguousarray(output, dtype=np.float32)


def _normalize_biquad(
    b0: float,
    b1: float,
    b2: float,
    a0: float,
    a1: float,
    a2: float,
) -> tuple[float, float, float, float, float]:
    return (b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0)


def _make_biquad_coefficients(
    kind: str,
    sample_rate: int,
    frequency_hz: float,
    *,
    q: float = 0.70710678,
    gain_db: float = 0.0,
    slope: float = 1.0,
) -> tuple[float, float, float, float, float]:
    clamped_frequency = float(np.clip(frequency_hz, 5.0, max(5.0, sample_rate * 0.499)))
    omega = 2.0 * np.pi * clamped_frequency / sample_rate
    sin_omega = np.sin(omega)
    cos_omega = np.cos(omega)
    safe_q = max(float(q), 0.001)
    safe_slope = max(float(slope), 0.001)
    alpha = sin_omega / (2.0 * safe_q)
    a = 10.0 ** (gain_db / 40.0)
    sqrt_a = np.sqrt(a)
    shelf_alpha = sin_omega * 0.5 * np.sqrt((a + 1.0 / a) * (1.0 / safe_slope - 1.0) + 2.0)

    if kind == "bandpass":
        return _normalize_biquad(alpha, 0.0, -alpha, 1.0 + alpha, -2.0 * cos_omega, 1.0 - alpha)
    if kind == "highpass":
        return _normalize_biquad(
            (1.0 + cos_omega) * 0.5,
            -(1.0 + cos_omega),
            (1.0 + cos_omega) * 0.5,
            1.0 + alpha,
            -2.0 * cos_omega,
            1.0 - alpha,
        )
    if kind == "notch":
        return _normalize_biquad(
            1.0,
            -2.0 * cos_omega,
            1.0,
            1.0 + alpha,
            -2.0 * cos_omega,
            1.0 - alpha,
        )
    if kind == "peak":
        return _normalize_biquad(
            1.0 + alpha * a,
            -2.0 * cos_omega,
            1.0 - alpha * a,
            1.0 + alpha / a,
            -2.0 * cos_omega,
            1.0 - alpha / a,
        )
    if kind == "low_shelf":
        return _normalize_biquad(
            a * ((a + 1.0) - (a - 1.0) * cos_omega + 2.0 * sqrt_a * shelf_alpha),
            2.0 * a * ((a - 1.0) - (a + 1.0) * cos_omega),
            a * ((a + 1.0) - (a - 1.0) * cos_omega - 2.0 * sqrt_a * shelf_alpha),
            (a + 1.0) + (a - 1.0) * cos_omega + 2.0 * sqrt_a * shelf_alpha,
            -2.0 * ((a - 1.0) + (a + 1.0) * cos_omega),
            (a + 1.0) + (a - 1.0) * cos_omega - 2.0 * sqrt_a * shelf_alpha,
        )
    if kind == "high_shelf":
        return _normalize_biquad(
            a * ((a + 1.0) + (a - 1.0) * cos_omega + 2.0 * sqrt_a * shelf_alpha),
            -2.0 * a * ((a - 1.0) + (a + 1.0) * cos_omega),
            a * ((a + 1.0) + (a - 1.0) * cos_omega - 2.0 * sqrt_a * shelf_alpha),
            (a + 1.0) - (a - 1.0) * cos_omega + 2.0 * sqrt_a * shelf_alpha,
            2.0 * ((a - 1.0) - (a + 1.0) * cos_omega),
            (a + 1.0) - (a - 1.0) * cos_omega - 2.0 * sqrt_a * shelf_alpha,
        )
    if kind == "lowpass":
        return _normalize_biquad(
            (1.0 - cos_omega) * 0.5,
            1.0 - cos_omega,
            (1.0 - cos_omega) * 0.5,
            1.0 + alpha,
            -2.0 * cos_omega,
            1.0 - alpha,
        )
    raise ValueError(f"Unsupported biquad kind: {kind}")


def _biquad_process_block(
    block: np.ndarray,
    coeffs: tuple[float, float, float, float, float],
    state: list[float],
) -> np.ndarray:
    b0, b1, b2, a1, a2 = coeffs
    z1, z2 = state
    output = np.empty_like(block)
    for index, sample in enumerate(block):
        out = b0 * sample + z1
        z1 = b1 * sample - a1 * out + z2
        z2 = b2 * sample - a2 * out
        output[index] = out
    state[0] = z1
    state[1] = z2
    return output


def _filter_signal(
    samples: np.ndarray,
    sample_rate: int,
    *,
    kind: str,
    frequency_hz: float,
    q: float = 0.70710678,
    gain_db: float = 0.0,
    slope: float = 1.0,
    stages: int = 1,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    coeff = _make_biquad_coefficients(kind, sample_rate, frequency_hz, q=q, gain_db=gain_db, slope=slope)
    output = np.empty_like(frames)
    stage_count = max(1, int(stages))
    for channel in range(frames.shape[1]):
        processed = np.array(frames[:, channel], copy=True)
        for _ in range(stage_count):
            processed = _biquad_process_block(processed, coeff, [0.0, 0.0])
        output[:, channel] = processed
    return np.ascontiguousarray(output, dtype=np.float32)


def _lowpass_signal(samples: np.ndarray, sample_rate: int, cutoff_hz: float) -> np.ndarray:
    return _filter_signal(samples, sample_rate, kind="lowpass", frequency_hz=cutoff_hz)


def _dynamic_eq(
    samples: np.ndarray,
    sample_rate: int,
    *,
    frequency_hz: float,
    threshold_db: float,
    cut_db: float,
    q: float,
    attack_ms: float,
    release_ms: float,
    block_size: int,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    threshold = _db_to_linear(threshold_db)
    attack_coeff = np.exp(-1.0 / (0.001 * max(float(attack_ms), 0.001) * sample_rate))
    release_coeff = np.exp(-1.0 / (0.001 * max(float(release_ms), 0.001) * sample_rate))
    detector_coeffs = _make_biquad_coefficients("bandpass", sample_rate, frequency_hz, q=q)
    chunk_size = max(32, int(block_size))

    for channel in range(frames.shape[1]):
        detector_state = [0.0, 0.0]
        eq_state = [0.0, 0.0]
        envelope = 0.0
        for offset in range(0, frames.shape[0], chunk_size):
            block = frames[offset : offset + chunk_size, channel]
            detected = _biquad_process_block(block, detector_coeffs, detector_state)
            for sample in np.abs(detected):
                coeff = attack_coeff if sample > envelope else release_coeff
                envelope = coeff * envelope + (1.0 - coeff) * float(sample)
            intensity = 0.0 if envelope <= threshold else min(1.0, (envelope - threshold) / max(threshold, 1e-6))
            current_gain_db = cut_db * intensity
            eq_coeffs = _make_biquad_coefficients("peak", sample_rate, frequency_hz, q=q, gain_db=current_gain_db)
            output[offset : offset + chunk_size, channel] = _biquad_process_block(block, eq_coeffs, eq_state)

    return np.ascontiguousarray(output, dtype=np.float32)


def _ring_modulation(samples: np.ndarray, sample_rate: int, *, frequency_hz: float, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    timeline = np.arange(frames.shape[0], dtype=np.float32) / sample_rate
    carrier = np.sin(2.0 * np.pi * frequency_hz * timeline).astype(np.float32)
    wet = frames * carrier[:, None]
    output = frames * (1.0 - mix) + wet * mix
    return np.ascontiguousarray(output, dtype=np.float32)


def _analytic_signal(signal: np.ndarray) -> np.ndarray:
    length = signal.shape[0]
    spectrum = np.fft.fft(signal)
    h = np.zeros(length, dtype=np.float32)
    if length % 2 == 0:
        h[0] = 1.0
        h[length // 2] = 1.0
        h[1 : length // 2] = 2.0
    else:
        h[0] = 1.0
        h[1 : (length + 1) // 2] = 2.0
    return np.fft.ifft(spectrum * h)


def _frequency_shifter(samples: np.ndarray, sample_rate: int, *, shift_hz: float, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    timeline = np.arange(frames.shape[0], dtype=np.float32) / sample_rate
    oscillator = np.exp(1j * 2.0 * np.pi * shift_hz * timeline)
    for channel in range(frames.shape[1]):
        analytic = _analytic_signal(frames[:, channel])
        shifted = np.real(analytic * oscillator).astype(np.float32)
        output[:, channel] = frames[:, channel] * (1.0 - mix) + shifted * mix
    return np.ascontiguousarray(output, dtype=np.float32)


def _rotary_speaker(
    samples: np.ndarray,
    sample_rate: int,
    *,
    rate_hz: float,
    depth: float,
    mix: float,
    crossover_hz: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    stereo = frames if frames.shape[1] >= 2 else np.repeat(frames, 2, axis=1)
    low_band = _lowpass_signal(stereo, sample_rate, crossover_hz)
    high_band = stereo - low_band
    timeline = np.arange(stereo.shape[0], dtype=np.float32) / sample_rate

    horn_phase = 2.0 * np.pi * rate_hz * timeline
    bass_phase = 2.0 * np.pi * (rate_hz * 0.62) * timeline
    horn_pan = np.sin(horn_phase) * depth
    horn_angle = (horn_pan + 1.0) * (np.pi * 0.25)
    horn_left = np.cos(horn_angle).astype(np.float32)
    horn_right = np.sin(horn_angle).astype(np.float32)
    horn_gain = (0.78 + 0.22 * np.sin(horn_phase + np.pi * 0.5)).astype(np.float32)
    bass_gain = (0.9 + 0.1 * np.sin(bass_phase)).astype(np.float32)

    wet = np.empty_like(stereo)
    wet[:, 0] = low_band[:, 0] * bass_gain + high_band[:, 0] * horn_left * horn_gain
    wet[:, 1] = low_band[:, 1] * bass_gain + high_band[:, 1] * horn_right * horn_gain
    output = stereo * (1.0 - mix) + wet * mix

    if frames.shape[1] == 1:
        output = np.mean(output, axis=1, keepdims=True, dtype=np.float32)
    return np.ascontiguousarray(output, dtype=np.float32)


def _modulated_delay(
    samples: np.ndarray,
    sample_rate: int,
    *,
    base_delay_ms: float,
    depth_ms: float,
    rate_hz: float,
    mix: float,
    feedback: float,
    wet_only: bool = False,
    stereo_phase_offset: float = np.pi / 2.0,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    frame_count, channels = frames.shape
    max_delay_ms = base_delay_ms + abs(depth_ms) + 10.0
    max_delay_samples = max(8, int(np.ceil(max_delay_ms * sample_rate / 1000.0)) + 4)
    delay_buffer = np.zeros((max_delay_samples, channels), dtype=np.float32)
    output = np.empty_like(frames)
    write_index = 0
    phase_offsets = np.arange(channels, dtype=np.float32) * stereo_phase_offset

    for frame_index in range(frame_count):
        time_seconds = frame_index / float(sample_rate)
        lfo_base = 2.0 * np.pi * rate_hz * time_seconds
        wet = np.empty(channels, dtype=np.float32)

        for channel in range(channels):
            lfo = 0.5 * (1.0 + np.sin(lfo_base + phase_offsets[channel]))
            delay_samples = max(1.0, (base_delay_ms + depth_ms * lfo) * sample_rate / 1000.0)
            wet[channel] = _linear_read(delay_buffer, channel, write_index, delay_samples)

        if wet_only:
            output[frame_index] = wet
        else:
            output[frame_index] = frames[frame_index] * (1.0 - mix) + wet * mix

        delay_buffer[write_index] = frames[frame_index] + wet * feedback
        write_index = (write_index + 1) % max_delay_samples

    return np.ascontiguousarray(output, dtype=np.float32)


def _auto_pan(samples: np.ndarray, sample_rate: int, *, rate_hz: float, depth: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if frames.shape[1] < 2:
        return frames.copy()

    output = frames.copy()
    for frame_index in range(frames.shape[0]):
        time_seconds = frame_index / float(sample_rate)
        lfo = np.sin(2.0 * np.pi * rate_hz * time_seconds) * depth
        angle = (lfo + 1.0) * (np.pi * 0.25)
        left_gain = np.cos(angle)
        right_gain = np.sin(angle)
        output[frame_index, 0] *= left_gain
        output[frame_index, 1] *= right_gain

    return np.ascontiguousarray(output, dtype=np.float32)


def _dynamic_tremolo(samples: np.ndarray, sample_rate: int, *, rate_hz: float | Automation, depth: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = frames.copy()
    phase = 0.0
    for frame_index in range(frames.shape[0]):
        time_seconds = frame_index / float(sample_rate)
        current_rate_hz = max(0.01, evaluate_param(rate_hz, time_seconds))
        lfo = 0.5 * (1.0 + np.sin(phase))
        gain = (1.0 - depth) + depth * lfo
        output[frame_index] *= gain
        phase += 2.0 * np.pi * current_rate_hz / sample_rate
        if phase >= 2.0 * np.pi:
            phase -= 2.0 * np.pi
    return np.ascontiguousarray(output, dtype=np.float32)


def _phaser(samples: np.ndarray, sample_rate: int, *, rate_hz: float, depth: float, center_hz: float, feedback: float, mix: float, stages: int) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    frame_count, channels = frames.shape
    output = np.empty_like(frames)
    stage_count = max(1, int(stages))
    prev_x = np.zeros((channels, stage_count), dtype=np.float32)
    prev_y = np.zeros((channels, stage_count), dtype=np.float32)
    feedback_state = np.zeros(channels, dtype=np.float32)

    for frame_index in range(frame_count):
        time_seconds = frame_index / float(sample_rate)
        lfo = 0.5 * (1.0 + np.sin(2.0 * np.pi * rate_hz * time_seconds))
        sweep_hz = max(80.0, center_hz * (0.35 + depth * 1.65 * lfo))
        omega = np.pi * sweep_hz / sample_rate
        tangent = np.tan(omega)
        coefficient = (1.0 - tangent) / max(1.0 + tangent, 1e-6)

        for channel in range(channels):
            x = frames[frame_index, channel] + feedback_state[channel] * feedback
            y = x
            for stage in range(stage_count):
                stage_out = -coefficient * y + prev_x[channel, stage] + coefficient * prev_y[channel, stage]
                prev_x[channel, stage] = y
                prev_y[channel, stage] = stage_out
                y = stage_out

            feedback_state[channel] = y
            output[frame_index, channel] = frames[frame_index, channel] * (1.0 - mix) + y * mix

    return np.ascontiguousarray(output, dtype=np.float32)


def _db_to_linear(value_db: float) -> float:
    return float(10.0 ** (float(value_db) / 20.0))


def _gain(samples: np.ndarray, *, db: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    return np.ascontiguousarray(frames * _db_to_linear(db), dtype=np.float32)


def _clip(samples: np.ndarray, *, threshold: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_threshold = max(abs(float(threshold)), 0.0001)
    return np.ascontiguousarray(np.clip(frames, -safe_threshold, safe_threshold), dtype=np.float32)


def _mix_wet_dry(frames: np.ndarray, wet: np.ndarray, mix: float) -> np.ndarray:
    clamped_mix = float(np.clip(mix, 0.0, 1.0))
    return np.ascontiguousarray(frames * (1.0 - clamped_mix) + wet * clamped_mix, dtype=np.float32)


def _distortion(samples: np.ndarray, *, drive: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    shaped_drive = max(float(drive), 0.01)
    normalizer = max(float(np.tanh(max(shaped_drive, 1.0))), 1e-6)
    wet = np.tanh(frames * shaped_drive).astype(np.float32) / normalizer
    return np.ascontiguousarray(wet, dtype=np.float32)


def _overdrive(samples: np.ndarray, *, drive: float, tone: float, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    shaped_drive = max(float(drive), 0.01)
    shaped_tone = float(np.clip(tone, 0.0, 1.0))
    pre_gain = 1.0 + shaped_drive * (1.3 + shaped_tone * 1.7)
    wet = ((2.0 / np.pi) * np.arctan(frames * pre_gain)).astype(np.float32)
    wet = wet * (0.82 + shaped_tone * 0.18) + frames * (0.18 - shaped_tone * 0.08)
    return _mix_wet_dry(frames, wet.astype(np.float32), mix)


def _fuzz(samples: np.ndarray, *, drive: float, bias: float, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    shaped_drive = max(float(drive), 0.01)
    shaped_bias = float(np.clip(bias, -0.45, 0.45))
    pre = frames * (2.5 + shaped_drive * 3.0) + shaped_bias * np.sign(frames)
    saturated = np.tanh(pre).astype(np.float32)
    wet = np.sign(saturated) * np.sqrt(np.abs(saturated) + 1e-8, dtype=np.float32)
    return _mix_wet_dry(frames, wet.astype(np.float32), mix)


def _bitcrusher(samples: np.ndarray, *, bit_depth: int, sample_rate_reduction: int, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_bits = max(2, int(bit_depth))
    safe_reduction = max(1, int(sample_rate_reduction))
    levels = float((1 << safe_bits) - 1)
    quantized = np.round(((frames + 1.0) * 0.5) * levels) / levels
    quantized = (quantized * 2.0 - 1.0).astype(np.float32)
    if safe_reduction > 1:
        held = np.repeat(quantized[::safe_reduction], safe_reduction, axis=0)
        quantized = held[: frames.shape[0]]
    return _mix_wet_dry(frames, quantized.astype(np.float32), mix)


def _waveshaper(samples: np.ndarray, *, amount: float, symmetry: float, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    shaped_amount = max(float(amount), 0.01)
    shaped_symmetry = float(np.clip(symmetry, -0.95, 0.95))
    shifted = np.clip(frames + shaped_symmetry * 0.25, -1.0, 1.0)
    strength = 1.0 + shaped_amount * 4.0
    denominator = max(1e-6, float(1.0 - np.exp(-strength)))
    wet = np.sign(shifted) * (1.0 - np.exp(-np.abs(shifted) * strength)) / denominator
    return _mix_wet_dry(frames, wet.astype(np.float32), mix)


def _tube_saturation(samples: np.ndarray, *, drive: float, bias: float, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    shaped_drive = max(float(drive), 0.01)
    shaped_bias = float(np.clip(bias, -0.4, 0.4))
    dc_shift = shaped_bias * 0.35
    wet = np.tanh(frames * (1.0 + shaped_drive * 2.4) + dc_shift).astype(np.float32)
    wet = wet - np.float32(np.tanh(dc_shift))
    peak = float(np.max(np.abs(wet)))
    if peak > 1.0:
        wet /= peak
    return _mix_wet_dry(frames, wet.astype(np.float32), mix)


def _tape_saturation(samples: np.ndarray, *, drive: float, softness: float, mix: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    shaped_drive = max(float(drive), 0.01)
    shaped_softness = float(np.clip(softness, 0.0, 1.0))
    pre = np.tanh(frames * (1.0 + shaped_drive * 1.8)).astype(np.float32)
    kernel = np.array(
        [0.18 * shaped_softness, 1.0 - 0.36 * shaped_softness, 0.18 * shaped_softness],
        dtype=np.float32,
    )
    kernel /= float(np.sum(kernel))
    wet = np.empty_like(pre)
    for channel in range(pre.shape[1]):
        wet[:, channel] = np.convolve(pre[:, channel], kernel, mode="same").astype(np.float32)
    wet = (wet * 0.82 + pre * 0.18).astype(np.float32)
    return _mix_wet_dry(frames, wet, mix)


def _soft_clipping(samples: np.ndarray, *, threshold: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    safe_threshold = max(float(threshold), 0.05)
    normalized = frames / safe_threshold
    abs_normalized = np.abs(normalized)
    wet = np.where(
        abs_normalized < 1.0,
        normalized - (normalized ** 3) / 3.0,
        np.sign(normalized) * (2.0 / 3.0),
    )
    wet = np.clip(wet * safe_threshold * 1.5, -1.0, 1.0).astype(np.float32)
    return np.ascontiguousarray(wet, dtype=np.float32)


def _upward_compression(
    samples: np.ndarray,
    sample_rate: int,
    *,
    threshold_db: float,
    ratio: float,
    attack_ms: float,
    release_ms: float,
    max_gain_db: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    threshold = _db_to_linear(threshold_db)
    max_gain = _db_to_linear(max_gain_db)
    safe_ratio = max(float(ratio), 1.0)
    attack_coeff = np.exp(-1.0 / (0.001 * max(float(attack_ms), 0.001) * sample_rate))
    release_coeff = np.exp(-1.0 / (0.001 * max(float(release_ms), 0.001) * sample_rate))
    envelopes = np.zeros(frames.shape[1], dtype=np.float32)

    for frame_index in range(frames.shape[0]):
        for channel in range(frames.shape[1]):
            sample = frames[frame_index, channel]
            detector = abs(sample)
            coeff = attack_coeff if detector > envelopes[channel] else release_coeff
            envelopes[channel] = coeff * envelopes[channel] + (1.0 - coeff) * detector

            gain = 1.0
            if 0.0 < envelopes[channel] < threshold:
                gain = min(
                    max_gain,
                    float((threshold / max(envelopes[channel], 1e-6)) ** ((safe_ratio - 1.0) / safe_ratio)),
                )

            output[frame_index, channel] = sample * gain

    return np.ascontiguousarray(output, dtype=np.float32)


def _transient_shaper(
    samples: np.ndarray,
    sample_rate: int,
    *,
    attack: float,
    sustain: float,
    attack_ms: float,
    release_ms: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    fast_attack_coeff = np.exp(-1.0 / (0.001 * 1.0 * sample_rate))
    fast_release_coeff = np.exp(-1.0 / (0.001 * 12.0 * sample_rate))
    slow_attack_coeff = np.exp(-1.0 / (0.001 * max(float(attack_ms), 0.001) * sample_rate))
    slow_release_coeff = np.exp(-1.0 / (0.001 * max(float(release_ms), 0.001) * sample_rate))
    fast_env = np.zeros(frames.shape[1], dtype=np.float32)
    slow_env = np.zeros(frames.shape[1], dtype=np.float32)

    for frame_index in range(frames.shape[0]):
        for channel in range(frames.shape[1]):
            sample = frames[frame_index, channel]
            detector = abs(sample)

            fast_coeff = fast_attack_coeff if detector > fast_env[channel] else fast_release_coeff
            slow_coeff = slow_attack_coeff if detector > slow_env[channel] else slow_release_coeff
            fast_env[channel] = fast_coeff * fast_env[channel] + (1.0 - fast_coeff) * detector
            slow_env[channel] = slow_coeff * slow_env[channel] + (1.0 - slow_coeff) * detector

            transient = fast_env[channel] - slow_env[channel]
            reference = max(fast_env[channel], 1e-6)
            transient_ratio = transient / reference
            gain = 1.0 + max(attack, -1.0) * max(transient_ratio, 0.0) - max(sustain, -1.0) * min(transient_ratio, 0.0)
            output[frame_index, channel] = sample * float(np.clip(gain, 0.15, 4.0))

    return np.ascontiguousarray(output, dtype=np.float32)


def _compressor(
    samples: np.ndarray,
    sample_rate: int,
    *,
    threshold_db: float,
    ratio: float,
    attack_ms: float,
    release_ms: float,
    makeup_db: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    threshold = _db_to_linear(threshold_db)
    safe_ratio = max(float(ratio), 1.0)
    attack_coeff = np.exp(-1.0 / (0.001 * max(float(attack_ms), 0.001) * sample_rate))
    release_coeff = np.exp(-1.0 / (0.001 * max(float(release_ms), 0.001) * sample_rate))
    makeup_gain = _db_to_linear(makeup_db)
    envelopes = np.zeros(frames.shape[1], dtype=np.float32)

    for frame_index in range(frames.shape[0]):
        for channel in range(frames.shape[1]):
            sample = frames[frame_index, channel]
            detector = abs(sample)
            coeff = attack_coeff if detector > envelopes[channel] else release_coeff
            envelopes[channel] = coeff * envelopes[channel] + (1.0 - coeff) * detector

            gain = 1.0
            if envelopes[channel] > threshold and envelopes[channel] > 0.0:
                gain = float((envelopes[channel] / threshold) ** (1.0 / safe_ratio - 1.0))

            output[frame_index, channel] = sample * gain * makeup_gain

    return np.ascontiguousarray(output, dtype=np.float32)


def _limiter(
    samples: np.ndarray,
    sample_rate: int,
    *,
    ceiling_db: float,
    attack_ms: float,
    release_ms: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    ceiling = _db_to_linear(ceiling_db)
    attack_coeff = np.exp(-1.0 / (0.001 * max(float(attack_ms), 0.001) * sample_rate))
    release_coeff = np.exp(-1.0 / (0.001 * max(float(release_ms), 0.001) * sample_rate))
    gain_states = np.ones(frames.shape[1], dtype=np.float32)

    for frame_index in range(frames.shape[0]):
        for channel in range(frames.shape[1]):
            sample = frames[frame_index, channel]
            level = abs(sample)
            desired_gain = ceiling / level if level > ceiling and level > 0.0 else 1.0
            coeff = attack_coeff if desired_gain < gain_states[channel] else release_coeff
            gain_states[channel] = coeff * gain_states[channel] + (1.0 - coeff) * desired_gain
            output[frame_index, channel] = float(np.clip(sample * gain_states[channel], -ceiling, ceiling))

    return np.ascontiguousarray(output, dtype=np.float32)


def _expander(
    samples: np.ndarray,
    sample_rate: int,
    *,
    threshold_db: float,
    ratio: float,
    attack_ms: float,
    release_ms: float,
    makeup_db: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    threshold = _db_to_linear(threshold_db)
    safe_ratio = max(float(ratio), 1.0)
    attack_coeff = np.exp(-1.0 / (0.001 * max(float(attack_ms), 0.001) * sample_rate))
    release_coeff = np.exp(-1.0 / (0.001 * max(float(release_ms), 0.001) * sample_rate))
    makeup_gain = _db_to_linear(makeup_db)
    envelopes = np.zeros(frames.shape[1], dtype=np.float32)

    for frame_index in range(frames.shape[0]):
        for channel in range(frames.shape[1]):
            sample = frames[frame_index, channel]
            detector = abs(sample)
            coeff = attack_coeff if detector > envelopes[channel] else release_coeff
            envelopes[channel] = coeff * envelopes[channel] + (1.0 - coeff) * detector

            gain = 1.0
            if 0.0 < envelopes[channel] < threshold:
                gain = float((envelopes[channel] / threshold) ** (safe_ratio - 1.0))

            output[frame_index, channel] = sample * gain * makeup_gain

    return np.ascontiguousarray(output, dtype=np.float32)


def _noise_gate(
    samples: np.ndarray,
    sample_rate: int,
    *,
    threshold_db: float,
    attack_ms: float,
    release_ms: float,
    floor_db: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.array(frames, copy=True)
    threshold = _db_to_linear(threshold_db)
    floor_gain = _db_to_linear(floor_db)
    attack_coeff = np.exp(-1.0 / (0.001 * max(float(attack_ms), 0.001) * sample_rate))
    release_coeff = np.exp(-1.0 / (0.001 * max(float(release_ms), 0.001) * sample_rate))
    envelopes = np.zeros(frames.shape[1], dtype=np.float32)
    gain_states = np.full(frames.shape[1], floor_gain, dtype=np.float32)

    for frame_index in range(frames.shape[0]):
        for channel in range(frames.shape[1]):
            detector = abs(output[frame_index, channel])
            env_coeff = attack_coeff if detector > envelopes[channel] else release_coeff
            envelopes[channel] = env_coeff * envelopes[channel] + (1.0 - env_coeff) * detector

            target_gain = 1.0 if envelopes[channel] >= threshold else floor_gain
            gain_coeff = attack_coeff if target_gain > gain_states[channel] else release_coeff
            gain_states[channel] = gain_coeff * gain_states[channel] + (1.0 - gain_coeff) * target_gain
            output[frame_index, channel] *= gain_states[channel]

    return np.ascontiguousarray(output, dtype=np.float32)


def _deesser(
    samples: np.ndarray,
    sample_rate: int,
    *,
    frequency_hz: float,
    threshold_db: float,
    ratio: float,
    attack_ms: float,
    release_ms: float,
    amount: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    output = np.empty_like(frames)
    detector_coeffs = _make_biquad_coefficients("highpass", sample_rate, frequency_hz)
    threshold = _db_to_linear(threshold_db)
    safe_ratio = max(float(ratio), 1.0)
    attack_coeff = np.exp(-1.0 / (0.001 * max(float(attack_ms), 0.001) * sample_rate))
    release_coeff = np.exp(-1.0 / (0.001 * max(float(release_ms), 0.001) * sample_rate))
    clamped_amount = float(np.clip(amount, 0.0, 1.0))

    for channel in range(frames.shape[1]):
        detector_state = [0.0, 0.0]
        envelope = 0.0
        detected = _biquad_process_block(frames[:, channel], detector_coeffs, detector_state)

        for frame_index, input_sample in enumerate(frames[:, channel]):
            detector = abs(detected[frame_index])
            coeff = attack_coeff if detector > envelope else release_coeff
            envelope = coeff * envelope + (1.0 - coeff) * detector

            gain = 1.0
            if envelope > threshold and envelope > 0.0:
                gain = float((envelope / threshold) ** (1.0 / safe_ratio - 1.0))

            shaped_gain = 1.0 - clamped_amount * (1.0 - gain)
            output[frame_index, channel] = input_sample * shaped_gain

    return np.ascontiguousarray(output, dtype=np.float32)


def _pan(samples: np.ndarray, *, position: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if frames.shape[1] < 2:
        return frames.copy()

    output = np.array(frames, copy=True)
    angle = (float(np.clip(position, -1.0, 1.0)) + 1.0) * (np.pi * 0.25)
    left_gain = np.cos(angle)
    right_gain = np.sin(angle)
    output[:, 0] *= left_gain
    output[:, 1] *= right_gain
    return np.ascontiguousarray(output, dtype=np.float32)


def _stereo_width(samples: np.ndarray, *, width: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if frames.shape[1] < 2:
        return frames.copy()

    output = np.array(frames, copy=True)
    safe_width = max(float(width), 0.0)
    left = frames[:, 0]
    right = frames[:, 1]
    mid = 0.5 * (left + right)
    side = 0.5 * (left - right) * safe_width
    output[:, 0] = mid + side
    output[:, 1] = mid - side
    return np.ascontiguousarray(output, dtype=np.float32)


def process_python_effect(
    effect: Effect,
    samples: np.ndarray,
    sample_rate: int,
    block_size: int,
) -> np.ndarray:
    _ = block_size
    frames = ensure_float32_frames(samples)
    params = effect.params
    effect_type = effect.type

    if effect_type == "gain":
        return _gain(frames, db=float(params.get("db", 0.0)))

    if effect_type == "clip":
        return _clip(frames, threshold=float(params.get("threshold", 0.98)))

    if effect_type == "distortion":
        return _distortion(frames, drive=float(params.get("drive", 2.0)))

    if effect_type == "lowpass":
        return _filter_signal(
            frames,
            sample_rate,
            kind="lowpass",
            frequency_hz=float(params.get("frequency_hz", 8_000.0)),
            q=float(params.get("q", 0.70710678)),
            stages=int(params.get("stages", 1)),
        )

    if effect_type == "highpass":
        return _filter_signal(
            frames,
            sample_rate,
            kind="highpass",
            frequency_hz=float(params.get("frequency_hz", 120.0)),
            q=float(params.get("q", 0.70710678)),
            stages=int(params.get("stages", 1)),
        )

    if effect_type == "bandpass":
        return _filter_signal(
            frames,
            sample_rate,
            kind="bandpass",
            frequency_hz=float(params.get("frequency_hz", 1_000.0)),
            q=float(params.get("q", 0.70710678)),
            stages=int(params.get("stages", 1)),
        )

    if effect_type == "notch":
        return _filter_signal(
            frames,
            sample_rate,
            kind="notch",
            frequency_hz=float(params.get("frequency_hz", 1_000.0)),
            q=float(params.get("q", 0.70710678)),
            stages=int(params.get("stages", 1)),
        )

    if effect_type == "peak_eq":
        return _filter_signal(
            frames,
            sample_rate,
            kind="peak",
            frequency_hz=float(params.get("frequency_hz", 1_000.0)),
            q=float(params.get("q", 1.0)),
            gain_db=float(params.get("gain_db", 0.0)),
            stages=int(params.get("stages", 1)),
        )

    if effect_type == "low_shelf":
        return _filter_signal(
            frames,
            sample_rate,
            kind="low_shelf",
            frequency_hz=float(params.get("frequency_hz", 120.0)),
            gain_db=float(params.get("gain_db", 0.0)),
            slope=float(params.get("slope", 1.0)),
            stages=int(params.get("stages", 1)),
        )

    if effect_type == "high_shelf":
        return _filter_signal(
            frames,
            sample_rate,
            kind="high_shelf",
            frequency_hz=float(params.get("frequency_hz", 9_000.0)),
            gain_db=float(params.get("gain_db", 0.0)),
            slope=float(params.get("slope", 1.0)),
            stages=int(params.get("stages", 1)),
        )

    if effect_type == "compressor":
        return _compressor(
            frames,
            sample_rate,
            threshold_db=float(params.get("threshold_db", -18.0)),
            ratio=float(params.get("ratio", 4.0)),
            attack_ms=float(params.get("attack_ms", 10.0)),
            release_ms=float(params.get("release_ms", 80.0)),
            makeup_db=float(params.get("makeup_db", 0.0)),
        )

    if effect_type == "limiter":
        return _limiter(
            frames,
            sample_rate,
            ceiling_db=float(params.get("ceiling_db", -1.0)),
            attack_ms=float(params.get("attack_ms", 1.0)),
            release_ms=float(params.get("release_ms", 60.0)),
        )

    if effect_type == "expander":
        return _expander(
            frames,
            sample_rate,
            threshold_db=float(params.get("threshold_db", -35.0)),
            ratio=float(params.get("ratio", 2.0)),
            attack_ms=float(params.get("attack_ms", 8.0)),
            release_ms=float(params.get("release_ms", 80.0)),
            makeup_db=float(params.get("makeup_db", 0.0)),
        )

    if effect_type == "noise_gate":
        return _noise_gate(
            frames,
            sample_rate,
            threshold_db=float(params.get("threshold_db", -45.0)),
            attack_ms=float(params.get("attack_ms", 3.0)),
            release_ms=float(params.get("release_ms", 60.0)),
            floor_db=float(params.get("floor_db", -80.0)),
        )

    if effect_type == "deesser":
        return _deesser(
            frames,
            sample_rate,
            frequency_hz=float(params.get("frequency_hz", 6_500.0)),
            threshold_db=float(params.get("threshold_db", -28.0)),
            ratio=float(params.get("ratio", 4.0)),
            attack_ms=float(params.get("attack_ms", 2.0)),
            release_ms=float(params.get("release_ms", 60.0)),
            amount=float(params.get("amount", 1.0)),
        )

    if effect_type == "pan":
        return _pan(frames, position=float(params.get("position", 0.0)))

    if effect_type == "stereo_width":
        return _stereo_width(frames, width=float(params.get("width", 1.0)))

    if effect_type == "delay":
        return _variable_delay(
            frames,
            sample_rate,
            params["delay_ms"],
            mix=float(params.get("mix", 0.2)),
            feedback=float(params.get("feedback", 0.35)),
        )

    if effect_type == "ping_pong_delay":
        return _variable_delay(
            frames,
            sample_rate,
            params["delay_ms"],
            mix=float(params.get("mix", 0.3)),
            feedback=float(params.get("feedback", 0.55)),
            cross_feedback=True,
        )

    if effect_type == "multi_tap_delay":
        impulse = _multi_tap_impulse(
            sample_rate,
            channels=frames.shape[1],
            base_delay_ms=float(params.get("delay_ms", 120.0)),
            taps=int(params.get("taps", 4)),
            spacing_ms=float(params.get("spacing_ms", 65.0)),
            decay=float(params.get("decay", 0.6)),
        )
        return _fft_convolve_same(frames, impulse, mix=float(params.get("mix", 0.32)))

    if effect_type == "early_reflections":
        impulse = _early_reflections_impulse(
            sample_rate,
            channels=frames.shape[1],
            pre_delay_ms=float(params.get("pre_delay_ms", 12.0)),
            spread_ms=float(params.get("spread_ms", 8.0)),
            taps=int(params.get("taps", 6)),
            decay=float(params.get("decay", 0.7)),
        )
        return _fft_convolve_same(frames, impulse, mix=float(params.get("mix", 0.22)))

    if effect_type in {"room_reverb", "hall_reverb", "plate_reverb"}:
        impulse = _synthetic_reverb_impulse(
            effect_type,
            sample_rate,
            channels=frames.shape[1],
            decay_seconds=float(params.get("decay_seconds", 1.0)),
            tone_hz=float(params.get("tone_hz", 8_000.0)),
        )
        return _fft_convolve_same(frames, impulse, mix=float(params.get("mix", 0.25)))

    if effect_type == "convolution_reverb":
        impulse = _prepare_impulse_response(
            params["impulse_response"],
            sample_rate=sample_rate,
            channels=frames.shape[1],
            normalize_ir=bool(params.get("normalize_ir", True)),
        )
        return _fft_convolve_same(frames, impulse, mix=float(params.get("mix", 0.28)))

    if effect_type == "chorus":
        return _modulated_delay(
            frames,
            sample_rate,
            base_delay_ms=float(params.get("delay_ms", 18.0)),
            depth_ms=float(params.get("depth_ms", 7.5)),
            rate_hz=float(params.get("rate_hz", 0.9)),
            mix=float(params.get("mix", 0.35)),
            feedback=float(params.get("feedback", 0.12)),
        )

    if effect_type == "flanger":
        return _modulated_delay(
            frames,
            sample_rate,
            base_delay_ms=float(params.get("delay_ms", 2.5)),
            depth_ms=float(params.get("depth_ms", 1.8)),
            rate_hz=float(params.get("rate_hz", 0.25)),
            mix=float(params.get("mix", 0.45)),
            feedback=float(params.get("feedback", 0.35)),
        )

    if effect_type == "vibrato":
        return _modulated_delay(
            frames,
            sample_rate,
            base_delay_ms=float(params.get("delay_ms", 5.5)),
            depth_ms=float(params.get("depth_ms", 3.5)),
            rate_hz=float(params.get("rate_hz", 5.0)),
            mix=float(params.get("mix", 1.0)),
            feedback=float(params.get("feedback", 0.0)),
            wet_only=True,
        )

    if effect_type == "auto_pan":
        return _auto_pan(
            frames,
            sample_rate,
            rate_hz=float(params.get("rate_hz", 0.35)),
            depth=float(params.get("depth", 1.0)),
        )

    if effect_type == "phaser":
        return _phaser(
            frames,
            sample_rate,
            rate_hz=float(params.get("rate_hz", 0.35)),
            depth=float(params.get("depth", 0.75)),
            center_hz=float(params.get("center_hz", 900.0)),
            feedback=float(params.get("feedback", 0.2)),
            mix=float(params.get("mix", 0.5)),
            stages=int(params.get("stages", 4)),
        )

    if effect_type == "dynamic_eq":
        return _dynamic_eq(
            frames,
            sample_rate,
            frequency_hz=float(params.get("frequency_hz", 2_500.0)),
            threshold_db=float(params.get("threshold_db", -24.0)),
            cut_db=float(params.get("cut_db", -6.0)),
            q=float(params.get("q", 1.2)),
            attack_ms=float(params.get("attack_ms", 10.0)),
            release_ms=float(params.get("release_ms", 120.0)),
            block_size=block_size,
        )

    if effect_type == "ring_modulation":
        return _ring_modulation(
            frames,
            sample_rate,
            frequency_hz=float(params.get("frequency_hz", 30.0)),
            mix=float(params.get("mix", 0.5)),
        )

    if effect_type == "frequency_shifter":
        return _frequency_shifter(
            frames,
            sample_rate,
            shift_hz=float(params.get("shift_hz", 120.0)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "rotary_speaker":
        return _rotary_speaker(
            frames,
            sample_rate,
            rate_hz=float(params.get("rate_hz", 0.8)),
            depth=float(params.get("depth", 0.7)),
            mix=float(params.get("mix", 0.65)),
            crossover_hz=float(params.get("crossover_hz", 900.0)),
        )

    if effect_type == "overdrive":
        return _overdrive(
            frames,
            drive=float(params.get("drive", 1.8)),
            tone=float(params.get("tone", 0.55)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "fuzz":
        return _fuzz(
            frames,
            drive=float(params.get("drive", 3.6)),
            bias=float(params.get("bias", 0.12)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "bitcrusher":
        return _bitcrusher(
            frames,
            bit_depth=int(params.get("bit_depth", 8)),
            sample_rate_reduction=int(params.get("sample_rate_reduction", 4)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "waveshaper":
        return _waveshaper(
            frames,
            amount=float(params.get("amount", 1.4)),
            symmetry=float(params.get("symmetry", 0.0)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "tube_saturation":
        return _tube_saturation(
            frames,
            drive=float(params.get("drive", 1.6)),
            bias=float(params.get("bias", 0.08)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "tape_saturation":
        return _tape_saturation(
            frames,
            drive=float(params.get("drive", 1.4)),
            softness=float(params.get("softness", 0.35)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "soft_clipping":
        return _soft_clipping(
            frames,
            threshold=float(params.get("threshold", 0.85)),
        )

    if effect_type == "pitch_shift":
        return pitch_shift_audio(
            frames,
            sample_rate,
            float(params.get("semitones", 0.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "time_stretch":
        return time_stretch_audio(
            frames,
            float(params.get("rate", 1.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "auto_tune":
        return auto_tune_audio(
            frames,
            sample_rate,
            strength=float(params.get("strength", 0.7)),
            key=str(params.get("key", "C")),
            scale=str(params.get("scale", "chromatic")),
            min_hz=float(params.get("min_hz", 80.0)),
            max_hz=float(params.get("max_hz", 1000.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "harmonizer":
        return harmonizer_audio(
            frames,
            sample_rate,
            params.get("intervals_semitones", (7.0,)),
            mix=float(params.get("mix", 0.35)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "octaver":
        return octaver_audio(
            frames,
            sample_rate,
            octaves_down=int(params.get("octaves_down", 1)),
            octaves_up=int(params.get("octaves_up", 0)),
            down_mix=float(params.get("down_mix", 0.45)),
            up_mix=float(params.get("up_mix", 0.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "formant_shifting":
        return formant_shift_audio(
            frames,
            sample_rate,
            float(params.get("shift", 1.0)),
            mix=float(params.get("mix", 1.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "noise_reduction":
        return noise_reduction_audio(
            frames,
            sample_rate,
            strength=float(params.get("strength", 0.5)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "voice_isolation":
        return voice_isolation_audio(
            frames,
            sample_rate,
            strength=float(params.get("strength", 0.75)),
            low_hz=float(params.get("low_hz", 120.0)),
            high_hz=float(params.get("high_hz", 5200.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "source_separation":
        return source_separation_audio(
            frames,
            sample_rate,
            target=str(params.get("target", "vocals")),
            strength=float(params.get("strength", 0.8)),
            low_hz=float(params.get("low_hz", 120.0)),
            high_hz=float(params.get("high_hz", 5200.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "de_reverb":
        return de_reverb_audio(
            frames,
            sample_rate,
            amount=float(params.get("amount", 0.45)),
            tail_ms=float(params.get("tail_ms", 240.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "de_echo":
        return de_echo_audio(
            frames,
            sample_rate,
            amount=float(params.get("amount", 0.45)),
            min_delay_ms=float(params.get("min_delay_ms", 60.0)),
            max_delay_ms=float(params.get("max_delay_ms", 800.0)),
        )

    if effect_type == "spectral_repair":
        return spectral_repair_audio(
            frames,
            sample_rate,
            strength=float(params.get("strength", 0.35)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "ai_enhancer":
        return ai_enhancer_audio(
            frames,
            sample_rate,
            amount=float(params.get("amount", 0.6)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "speech_enhancement":
        return speech_enhancement_audio(
            frames,
            sample_rate,
            amount=float(params.get("amount", 0.7)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "glitch_effect":
        return glitch_audio(
            frames,
            sample_rate,
            slice_ms=float(params.get("slice_ms", 70.0)),
            repeat_probability=float(params.get("repeat_probability", 0.22)),
            dropout_probability=float(params.get("dropout_probability", 0.12)),
            reverse_probability=float(params.get("reverse_probability", 0.10)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "stutter":
        return stutter_audio(
            frames,
            sample_rate,
            slice_ms=float(params.get("slice_ms", 90.0)),
            repeats=int(params.get("repeats", 3)),
            interval_ms=float(params.get("interval_ms", 480.0)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "tape_stop":
        return tape_stop_audio(
            frames,
            sample_rate,
            stop_time_ms=float(params.get("stop_time_ms", 900.0)),
            curve=float(params.get("curve", 2.0)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "reverse_reverb":
        return reverse_reverb_audio(
            frames,
            sample_rate,
            decay_seconds=float(params.get("decay_seconds", 1.2)),
            mix=float(params.get("mix", 0.45)),
        )

    if effect_type == "granular_synthesis":
        return granular_synthesis_audio(
            frames,
            sample_rate,
            grain_ms=float(params.get("grain_ms", 80.0)),
            overlap=float(params.get("overlap", 0.5)),
            jitter_ms=float(params.get("jitter_ms", 25.0)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "time_slicing":
        return time_slicing_audio(
            frames,
            sample_rate,
            slice_ms=float(params.get("slice_ms", 120.0)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "random_pitch_mod":
        return random_pitch_mod_audio(
            frames,
            sample_rate,
            depth_semitones=float(params.get("depth_semitones", 2.0)),
            segment_ms=float(params.get("segment_ms", 180.0)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "vinyl_effect":
        return vinyl_effect_audio(
            frames,
            sample_rate,
            noise=float(params.get("noise", 0.08)),
            wow=float(params.get("wow", 0.15)),
            crackle=float(params.get("crackle", 0.12)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "radio_effect":
        return radio_effect_audio(
            frames,
            sample_rate,
            noise_level=float(params.get("noise_level", 0.04)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "telephone_effect":
        return telephone_effect_audio(
            frames,
            sample_rate,
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "retro_8bit":
        return retro_8bit_audio(
            frames,
            bit_depth=int(params.get("bit_depth", 6)),
            sample_rate_reduction=int(params.get("sample_rate_reduction", 8)),
            mix=float(params.get("mix", 1.0)),
        )

    if effect_type == "slow_motion_extreme":
        return slow_motion_extreme_audio(
            frames,
            sample_rate,
            rate=float(params.get("rate", 0.45)),
            tone_hz=float(params.get("tone_hz", 4800.0)),
        )

    if effect_type == "robot_voice":
        return robot_voice_audio(
            frames,
            sample_rate,
            carrier_hz=float(params.get("carrier_hz", 70.0)),
            mix=float(params.get("mix", 0.85)),
        )

    if effect_type == "alien_voice":
        return alien_voice_audio(
            frames,
            sample_rate,
            shift_semitones=float(params.get("shift_semitones", 5.0)),
            formant_shift=float(params.get("formant_shift", 1.18)),
            mix=float(params.get("mix", 0.8)),
        )

    if effect_type == "fft_filter":
        return fft_filter_audio(
            frames,
            sample_rate,
            low_hz=float(params.get("low_hz", 80.0)),
            high_hz=float(params.get("high_hz", 12000.0)),
            mix=float(params.get("mix", 1.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "spectral_gating":
        return spectral_gating_audio(
            frames,
            sample_rate,
            threshold_db=float(params.get("threshold_db", -42.0)),
            floor=float(params.get("floor", 0.08)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "spectral_blur":
        return spectral_blur_audio(
            frames,
            sample_rate,
            amount=float(params.get("amount", 0.45)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "spectral_freeze":
        return spectral_freeze_audio(
            frames,
            sample_rate,
            start_ms=float(params.get("start_ms", 120.0)),
            mix=float(params.get("mix", 0.7)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "spectral_morphing":
        return spectral_morphing_audio(
            frames,
            sample_rate,
            amount=float(params.get("amount", 0.5)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "phase_vocoder":
        return phase_vocoder_audio(
            frames,
            rate=float(params.get("rate", 0.85)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "harmonic_percussive_separation":
        return harmonic_percussive_separation_audio(
            frames,
            sample_rate,
            target=str(params.get("target", "harmonic")),
            mix=float(params.get("mix", 1.0)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "spectral_delay":
        return spectral_delay_audio(
            frames,
            sample_rate,
            max_delay_ms=float(params.get("max_delay_ms", 240.0)),
            feedback=float(params.get("feedback", 0.15)),
            mix=float(params.get("mix", 0.35)),
            fft_size=int(params.get("fft_size", 2048)),
            hop_size=int(params.get("hop_size", 512)),
        )

    if effect_type == "stereo_widening":
        return stereo_widening_audio(
            frames,
            amount=float(params.get("amount", 1.25)),
        )

    if effect_type == "mid_side_processing":
        return mid_side_processing_audio(
            frames,
            mid_gain_db=float(params.get("mid_gain_db", 0.0)),
            side_gain_db=float(params.get("side_gain_db", 0.0)),
        )

    if effect_type == "stereo_imager":
        return stereo_imager_audio(
            frames,
            sample_rate,
            low_width=float(params.get("low_width", 0.9)),
            high_width=float(params.get("high_width", 1.35)),
            crossover_hz=float(params.get("crossover_hz", 280.0)),
        )

    if effect_type == "binaural_effect":
        return binaural_effect_audio(
            frames,
            sample_rate,
            azimuth_deg=float(params.get("azimuth_deg", 25.0)),
            distance=float(params.get("distance", 1.0)),
            room_mix=float(params.get("room_mix", 0.08)),
        )

    if effect_type == "spatial_positioning":
        return spatial_positioning_audio(
            frames,
            sample_rate,
            azimuth_deg=float(params.get("azimuth_deg", 25.0)),
            elevation_deg=float(params.get("elevation_deg", 0.0)),
            distance=float(params.get("distance", 1.0)),
        )

    if effect_type == "hrtf_simulation":
        return hrtf_simulation_audio(
            frames,
            sample_rate,
            azimuth_deg=float(params.get("azimuth_deg", 30.0)),
            elevation_deg=float(params.get("elevation_deg", 0.0)),
            distance=float(params.get("distance", 1.0)),
        )

    if effect_type == "tremolo":
        return _dynamic_tremolo(
            frames,
            sample_rate,
            rate_hz=params.get("rate_hz", 5.0),
            depth=float(params.get("depth", 0.5)),
        )

    if effect_type == "upward_compression":
        return _upward_compression(
            frames,
            sample_rate,
            threshold_db=float(params.get("threshold_db", -42.0)),
            ratio=float(params.get("ratio", 2.0)),
            attack_ms=float(params.get("attack_ms", 12.0)),
            release_ms=float(params.get("release_ms", 120.0)),
            max_gain_db=float(params.get("max_gain_db", 18.0)),
        )

    if effect_type == "transient_shaper":
        return _transient_shaper(
            frames,
            sample_rate,
            attack=float(params.get("attack", 0.7)),
            sustain=float(params.get("sustain", 0.2)),
            attack_ms=float(params.get("attack_ms", 18.0)),
            release_ms=float(params.get("release_ms", 120.0)),
        )

    raise ValueError(f"Unsupported Python DSP effect: {effect.display_name}")

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ._analysis import (
    bit_depth_convert_audio,
    dither_audio,
    envelope_follower as envelope_follower_analysis,
    integrated_lufs,
    loudness_normalize_audio,
    peak_dbfs as peak_dbfs_analysis,
    resample_audio,
    rms_dbfs as rms_dbfs_analysis,
)
from ._util import ensure_float32_frames
from .bands import MultibandPipeline, multiband_compressor as multiband_compressor_builder
from .effects import (
    ai_enhancer as ai_enhancer_effect,
    alien_voice as alien_voice_effect,
    auto_pan as auto_pan_effect,
    auto_tune as auto_tune_effect,
    bandpass as bandpass_effect,
    bitcrusher as bitcrusher_effect,
    chorus as chorus_effect,
    compressor as compressor_effect,
    convolution_reverb as convolution_reverb_effect,
    de_echo as de_echo_effect,
    deesser as deesser_effect,
    de_reverb as de_reverb_effect,
    delay as delay_effect,
    dynamic_eq as dynamic_eq_effect,
    distortion as distortion_effect,
    downward_compression as downward_compression_effect,
    early_reflections as early_reflections_effect,
    echo as echo_effect,
    expander as expander_effect,
    fft_filter as fft_filter_effect,
    feedback_delay as feedback_delay_effect,
    frequency_shifter as frequency_shifter_effect,
    flanger as flanger_effect,
    formant_filter as formant_filter_effect,
    fuzz as fuzz_effect,
    gain as gain_effect,
    graphic_eq as graphic_eq_effect,
    hard_clipping as hard_clipping_effect,
    hall_reverb as hall_reverb_effect,
    hrtf_simulation as hrtf_simulation_effect,
    harmonizer as harmonizer_effect,
    high_shelf as high_shelf_effect,
    highpass as highpass_effect,
    limiter as limiter_effect,
    low_shelf as low_shelf_effect,
    lowpass as lowpass_effect,
    mid_side_processing as mid_side_processing_effect,
    multi_tap_delay as multi_tap_delay_effect,
    noise_gate as noise_gate_effect,
    notch as notch_effect,
    noise_reduction as noise_reduction_effect,
    octaver as octaver_effect,
    overdrive as overdrive_effect,
    pan as pan_effect,
    phase_vocoder as phase_vocoder_effect,
    peak_eq as peak_eq_effect,
    phaser as phaser_effect,
    pitch_shift as pitch_shift_effect,
    ping_pong_delay as ping_pong_delay_effect,
    plate_reverb as plate_reverb_effect,
    resonant_filter as resonant_filter_effect,
    ring_modulation as ring_modulation_effect,
    rotary_speaker as rotary_speaker_effect,
    room_reverb as room_reverb_effect,
    slapback as slapback_effect,
    soft_clipping as soft_clipping_effect,
    source_separation as source_separation_effect,
    spectral_blur as spectral_blur_effect,
    spectral_delay as spectral_delay_effect,
    spectral_freeze as spectral_freeze_effect,
    spectral_gating as spectral_gating_effect,
    spectral_morphing as spectral_morphing_effect,
    spectral_repair as spectral_repair_effect,
    speech_enhancement as speech_enhancement_effect,
    spatial_positioning as spatial_positioning_effect,
    stereo_imager as stereo_imager_effect,
    stereo_widening as stereo_widening_effect,
    stutter as stutter_effect,
    stereo_width as stereo_width_effect,
    tape_saturation as tape_saturation_effect,
    tape_stop as tape_stop_effect,
    time_compression as time_compression_effect,
    time_stretch as time_stretch_effect,
    time_slicing as time_slicing_effect,
    transient_shaper as transient_shaper_effect,
    tremolo as tremolo_effect,
    tube_saturation as tube_saturation_effect,
    upward_compression as upward_compression_effect,
    vibrato as vibrato_effect,
    vinyl_effect as vinyl_effect_effect,
    voice_isolation as voice_isolation_effect,
    waveshaper as waveshaper_effect,
    glitch_effect as glitch_effect_builder,
    granular_synthesis as granular_synthesis_effect,
    harmonic_percussive_separation as harmonic_percussive_separation_effect,
    formant_shifting as formant_shifting_effect,
    radio_effect as radio_effect_effect,
    random_pitch_mod as random_pitch_mod_effect,
    retro_8bit as retro_8bit_effect,
    reverse_reverb as reverse_reverb_effect,
    robot_voice as robot_voice_effect,
    slow_motion_extreme as slow_motion_extreme_effect,
    binaural_effect as binaural_effect_effect,
    telephone_effect as telephone_effect_effect,
)
from .ffmpeg import encode_audio
from .ffmpeg import decode_audio
from .pipeline import Pipeline
from .presets import preset_names


def _format_pipeline_steps(steps: tuple[str, ...]) -> str:
    if not steps:
        return "(source clip)"
    return "\n".join(f"[{index}] {step}" for index, step in enumerate(steps))


def _linear_gain_from_db(value_db: float) -> float:
    return float(10.0 ** (float(value_db) / 20.0))


def _frames_from_ms(value_ms: float, sample_rate: int) -> int:
    return max(0, int(round(float(value_ms) * float(sample_rate) / 1000.0)))


def _resolve_slice_bounds(
    total_frames: int,
    sample_rate: int,
    *,
    start_ms: float | None = None,
    end_ms: float | None = None,
) -> tuple[int, int]:
    start = 0 if start_ms is None else _frames_from_ms(start_ms, sample_rate)
    end = total_frames if end_ms is None else _frames_from_ms(end_ms, sample_rate)
    start = max(0, min(total_frames, start))
    end = max(0, min(total_frames, end))
    if end < start:
        raise ValueError("end_ms must be greater than or equal to start_ms.")
    return start, end


def _ensure_non_empty(samples: np.ndarray) -> np.ndarray:
    if samples.shape[0] > 0:
        return samples
    return np.zeros((1, samples.shape[1]), dtype=np.float32)


def _apply_linear_fade(samples: np.ndarray, fade_frames: int, *, fade_in: bool) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if fade_frames <= 0:
        return frames.copy()

    output = frames.copy()
    count = min(output.shape[0], fade_frames)
    ramp = np.linspace(0.0, 1.0, num=count, dtype=np.float32)
    if fade_in:
        output[:count] *= ramp[:, None]
    else:
        output[-count:] *= ramp[::-1][:, None]
    return output


def _trim_samples(samples: np.ndarray, sample_rate: int, *, start_ms: float | None = None, end_ms: float | None = None) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    start, end = _resolve_slice_bounds(frames.shape[0], sample_rate, start_ms=start_ms, end_ms=end_ms)
    return _ensure_non_empty(np.ascontiguousarray(frames[start:end], dtype=np.float32))


def _cut_samples(samples: np.ndarray, sample_rate: int, *, start_ms: float, end_ms: float) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    start, end = _resolve_slice_bounds(frames.shape[0], sample_rate, start_ms=start_ms, end_ms=end_ms)
    kept = np.concatenate([frames[:start], frames[end:]], axis=0)
    return _ensure_non_empty(np.ascontiguousarray(kept, dtype=np.float32))


def _reverse_samples(samples: np.ndarray) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    return np.ascontiguousarray(frames[::-1], dtype=np.float32)


def _remix_channels(samples: np.ndarray, target_channels: int) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    target = int(target_channels)
    if target <= 0:
        raise ValueError("target_channels must be positive.")
    if frames.shape[1] == target:
        return frames.copy()
    if target == 1:
        return np.ascontiguousarray(np.mean(frames, axis=1, keepdims=True, dtype=np.float32), dtype=np.float32)
    mono = np.mean(frames, axis=1, keepdims=True, dtype=np.float32)
    if target == 2:
        if frames.shape[1] == 1:
            return np.ascontiguousarray(np.repeat(frames, 2, axis=1), dtype=np.float32)
        return np.ascontiguousarray(np.repeat(mono, 2, axis=1), dtype=np.float32)
    if frames.shape[1] == 1:
        return np.ascontiguousarray(np.repeat(frames, target, axis=1), dtype=np.float32)

    tiled = np.tile(mono, (1, target))
    return np.ascontiguousarray(tiled, dtype=np.float32)


def _remove_dc_offset_samples(samples: np.ndarray) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    centered = frames - np.mean(frames, axis=0, keepdims=True, dtype=np.float32)
    return np.ascontiguousarray(centered, dtype=np.float32)


def _remove_silence_samples(
    samples: np.ndarray,
    sample_rate: int,
    *,
    threshold_db: float,
    min_silence_ms: float,
    padding_ms: float,
) -> np.ndarray:
    frames = ensure_float32_frames(samples)
    if frames.shape[0] == 0:
        return frames.copy()

    threshold = _linear_gain_from_db(threshold_db)
    activity = np.max(np.abs(frames), axis=1) > threshold
    min_silence_frames = max(1, _frames_from_ms(min_silence_ms, sample_rate))
    padding_frames = _frames_from_ms(padding_ms, sample_rate)

    keep = activity.copy()
    silence = ~activity
    if silence.any():
        silence_edges = np.diff(np.pad(silence.astype(np.int8), (1, 1)))
        starts = np.flatnonzero(silence_edges == 1)
        ends = np.flatnonzero(silence_edges == -1)
        for start, end in zip(starts, ends, strict=False):
            if int(end - start) >= min_silence_frames:
                keep[start:end] = False

    total = keep.shape[0]
    if padding_frames > 0 and keep.any():
        keep_int = keep.astype(np.int32)
        prefix = np.concatenate([np.zeros(1, dtype=np.int32), np.cumsum(keep_int, dtype=np.int32)])
        indices = np.arange(total, dtype=np.int32)
        left = np.maximum(0, indices - padding_frames)
        right = np.minimum(total, indices + padding_frames + 1)
        keep = (prefix[right] - prefix[left]) > 0

    kept = frames[keep]
    if kept.shape[0] == 0:
        return np.zeros((1, frames.shape[1]), dtype=np.float32)
    return np.ascontiguousarray(kept, dtype=np.float32)


def _crossfade_samples(left: "AudioClip", right: "AudioClip", duration_ms: float) -> np.ndarray:
    if left.sample_rate != right.sample_rate:
        raise ValueError("crossfade requires clips with the same sample_rate.")

    left_samples = ensure_float32_frames(left.samples)
    right_samples = _remix_channels(right.samples, left.channels)
    fade_frames = min(
        _frames_from_ms(duration_ms, left.sample_rate),
        left_samples.shape[0],
        right_samples.shape[0],
    )

    if fade_frames <= 0:
        return np.ascontiguousarray(np.concatenate([left_samples, right_samples], axis=0), dtype=np.float32)

    fade_out = np.linspace(1.0, 0.0, num=fade_frames, dtype=np.float32)
    fade_in = np.linspace(0.0, 1.0, num=fade_frames, dtype=np.float32)
    overlap = (
        left_samples[-fade_frames:] * fade_out[:, None]
        + right_samples[:fade_frames] * fade_in[:, None]
    )
    combined = np.concatenate(
        [
            left_samples[:-fade_frames],
            overlap.astype(np.float32),
            right_samples[fade_frames:],
        ],
        axis=0,
    )
    return np.ascontiguousarray(combined, dtype=np.float32)


@dataclass(slots=True)
class AudioClip:
    samples: np.ndarray
    sample_rate: int
    _pipeline_steps: tuple[str, ...] = field(default_factory=tuple, repr=False)
    _render_cache: dict[str, "AudioClip"] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        self.samples = ensure_float32_frames(self.samples)
        self.sample_rate = int(self.sample_rate)

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        *,
        sample_rate: int | None = None,
        channels: int | None = None,
    ) -> "AudioClip":
        frames, metadata = decode_audio(path, sample_rate=sample_rate, channels=channels)
        return cls(frames, metadata.sample_rate)

    @classmethod
    def from_array(cls, samples: Any, sample_rate: int) -> "AudioClip":
        return cls(samples=samples, sample_rate=sample_rate)

    @property
    def channels(self) -> int:
        return int(self.samples.shape[1])

    @property
    def frames(self) -> int:
        return int(self.samples.shape[0])

    @property
    def duration_seconds(self) -> float:
        return self.frames / float(self.sample_rate)

    def copy(self) -> "AudioClip":
        return AudioClip(
            np.array(self.samples, copy=True),
            self.sample_rate,
            _pipeline_steps=self._pipeline_steps,
        )

    def numpy(self) -> np.ndarray:
        return np.array(self.samples, copy=True)

    def pipeline_info(self) -> str:
        return _format_pipeline_steps(self._pipeline_steps)

    def lazy(self) -> "DeferredClip":
        return DeferredClip(self)

    def _with_pipeline_steps(self, samples: np.ndarray, extra_steps: tuple[str, ...]) -> "AudioClip":
        return AudioClip(
            samples=samples,
            sample_rate=self.sample_rate,
            _pipeline_steps=self._pipeline_steps + extra_steps,
        )

    def apply(
        self,
        *effects: Any,
        block_size: int = 2048,
        workers: int = 1,
        lazy: bool = False,
    ) -> "AudioClip | DeferredClip":
        pipeline = Pipeline.from_effects(
            self.sample_rate,
            *effects,
            channels=self.channels,
            block_size=block_size,
            workers=workers,
        )
        return self.apply_pipeline(pipeline, lazy=lazy)

    def preset(
        self,
        name: str,
        *,
        block_size: int = 2048,
        workers: int = 1,
        lazy: bool = False,
    ) -> "AudioClip | DeferredClip":
        return self.apply(
            name,
            block_size=block_size,
            workers=workers,
            lazy=lazy,
        )

    def apply_pipeline(self, pipeline: Pipeline, *, lazy: bool = False) -> "AudioClip | DeferredClip":
        if lazy:
            return self.lazy().apply_pipeline(pipeline)
        processed = pipeline.process(self.samples)
        steps = tuple(effect.describe() for effect in pipeline.effects)
        return self._with_pipeline_steps(processed, steps)

    def process_bands(
        self,
        processor: MultibandPipeline,
        *,
        lazy: bool = False,
    ) -> "AudioClip | DeferredClip":
        if lazy:
            return self.lazy().process_bands(processor)
        processed = processor.process(self.samples)
        steps = (f"multiband_pipeline(bands={len(processor.bands)})",)
        return self._with_pipeline_steps(processed, steps)

    def normalize(self, headroom_db: float = 1.0, *, lazy: bool = False) -> "AudioClip | DeferredClip":
        if lazy:
            return self.lazy().normalize(headroom_db=headroom_db)

        peak = float(np.max(np.abs(self.samples)))
        if peak <= 0.0:
            return self.copy()

        target_peak = 10.0 ** (-abs(headroom_db) / 20.0)
        gain_db = 20.0 * np.log10(target_peak / peak)
        return self.gain(gain_db)

    def fade_in(self, duration_ms: float) -> "AudioClip":
        return self._with_pipeline_steps(
            _apply_linear_fade(self.samples, _frames_from_ms(duration_ms, self.sample_rate), fade_in=True),
            (f"fade_in(duration_ms={float(duration_ms):.2f}ms)",),
        )

    def fade_out(self, duration_ms: float) -> "AudioClip":
        return self._with_pipeline_steps(
            _apply_linear_fade(self.samples, _frames_from_ms(duration_ms, self.sample_rate), fade_in=False),
            (f"fade_out(duration_ms={float(duration_ms):.2f}ms)",),
        )

    def trim(self, *, start_ms: float | None = None, end_ms: float | None = None) -> "AudioClip":
        return self._with_pipeline_steps(
            _trim_samples(self.samples, self.sample_rate, start_ms=start_ms, end_ms=end_ms),
            (f"trim(start_ms={start_ms}, end_ms={end_ms})",),
        )

    def cut(self, *, start_ms: float, end_ms: float) -> "AudioClip":
        return self._with_pipeline_steps(
            _cut_samples(self.samples, self.sample_rate, start_ms=start_ms, end_ms=end_ms),
            (f"cut(start_ms={float(start_ms):.2f}ms, end_ms={float(end_ms):.2f}ms)",),
        )

    def remove_silence(
        self,
        *,
        threshold_db: float = -48.0,
        min_silence_ms: float = 80.0,
        padding_ms: float = 10.0,
    ) -> "AudioClip":
        description = (
            "remove_silence("
            f"threshold_db={float(threshold_db):.2f}dB, "
            f"min_silence_ms={float(min_silence_ms):.2f}ms, "
            f"padding_ms={float(padding_ms):.2f}ms)"
        )
        return self._with_pipeline_steps(
            _remove_silence_samples(
                self.samples,
                self.sample_rate,
                threshold_db=threshold_db,
                min_silence_ms=min_silence_ms,
                padding_ms=padding_ms,
            ),
            (description,),
        )

    def reverse(self) -> "AudioClip":
        return self._with_pipeline_steps(_reverse_samples(self.samples), ("reverse()",))

    def to_mono(self) -> "AudioClip":
        return self._with_pipeline_steps(_remix_channels(self.samples, 1), ("to_mono()",))

    def to_stereo(self) -> "AudioClip":
        return self._with_pipeline_steps(_remix_channels(self.samples, 2), ("to_stereo()",))

    def remove_dc_offset(self) -> "AudioClip":
        return self._with_pipeline_steps(_remove_dc_offset_samples(self.samples), ("remove_dc_offset()",))

    def crossfade(self, other: "AudioClip", duration_ms: float) -> "AudioClip":
        merged = _crossfade_samples(self, other, duration_ms)
        return self._with_pipeline_steps(
            merged,
            (f"crossfade(duration_ms={float(duration_ms):.2f}ms)",),
        )

    def export(
        self,
        path: str | Path,
        *,
        codec: str | None = None,
        bitrate: str | None = None,
        format: str | None = None,
        sample_rate: int | None = None,
        channels: int | None = None,
        overwrite: bool = True,
    ) -> Path:
        return encode_audio(
            self.samples,
            self.sample_rate,
            path,
            codec=codec,
            bitrate=bitrate,
            format=format,
            output_sample_rate=sample_rate,
            output_channels=channels,
            overwrite=overwrite,
        )

    def available_presets(self) -> tuple[str, ...]:
        return preset_names()

    def gain(self, db: float, *, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(gain_effect(db), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def lowpass(self, frequency_hz: float, *, q: float = 0.70710678, stages: int = 1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(lowpass_effect(frequency_hz, q=q, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def highpass(self, frequency_hz: float, *, q: float = 0.70710678, stages: int = 1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(highpass_effect(frequency_hz, q=q, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def bandpass(self, frequency_hz: float, *, q: float = 0.70710678, stages: int = 1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(bandpass_effect(frequency_hz, q=q, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def notch(self, frequency_hz: float, *, q: float = 0.70710678, stages: int = 1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(notch_effect(frequency_hz, q=q, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def peak_eq(self, frequency_hz: float, gain_db: float, *, q: float = 1.0, stages: int = 1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(peak_eq_effect(frequency_hz, gain_db, q=q, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def low_shelf(self, frequency_hz: float, gain_db: float, *, slope: float = 1.0, stages: int = 1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(low_shelf_effect(frequency_hz, gain_db, slope=slope, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def high_shelf(self, frequency_hz: float, gain_db: float, *, slope: float = 1.0, stages: int = 1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(high_shelf_effect(frequency_hz, gain_db, slope=slope, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def graphic_eq(self, bands: dict[float, float] | list[tuple[float, float]] | tuple[tuple[float, float], ...], *, q: float = 1.1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(graphic_eq_effect(bands, q=q), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def resonant_filter(self, frequency_hz: float, *, resonance: float = 1.6, mode: str = "lowpass", stages: int = 1, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(resonant_filter_effect(frequency_hz, resonance=resonance, mode=mode, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def dynamic_eq(self, frequency_hz: float, *, threshold_db: float = -24.0, cut_db: float = -6.0, q: float = 1.2, attack_ms: float = 10.0, release_ms: float = 120.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(dynamic_eq_effect(frequency_hz, threshold_db=threshold_db, cut_db=cut_db, q=q, attack_ms=attack_ms, release_ms=release_ms), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def formant_filter(self, morph: float = 0.0, *, intensity: float = 1.0, q: float = 4.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(formant_filter_effect(morph, intensity=intensity, q=q), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def delay(self, delay_ms: float, *, feedback: float = 0.35, mix: float = 0.2, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(delay_effect(delay_ms, feedback=feedback, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def feedback_delay(self, delay_ms: float, *, feedback: float = 0.6, mix: float = 0.35, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(feedback_delay_effect(delay_ms, feedback=feedback, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def echo(self, delay_ms: float = 320.0, *, feedback: float = 0.38, mix: float = 0.28, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(echo_effect(delay_ms=delay_ms, feedback=feedback, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def ping_pong_delay(self, delay_ms: float, *, feedback: float = 0.55, mix: float = 0.3, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(ping_pong_delay_effect(delay_ms, feedback=feedback, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def multi_tap_delay(self, *, delay_ms: float = 120.0, taps: int = 4, spacing_ms: float = 65.0, decay: float = 0.6, mix: float = 0.32, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(multi_tap_delay_effect(delay_ms=delay_ms, taps=taps, spacing_ms=spacing_ms, decay=decay, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def slapback(self, delay_ms: float = 95.0, *, mix: float = 0.24, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(slapback_effect(delay_ms=delay_ms, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def early_reflections(self, *, pre_delay_ms: float = 12.0, spread_ms: float = 8.0, taps: int = 6, decay: float = 0.7, mix: float = 0.22, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(early_reflections_effect(pre_delay_ms=pre_delay_ms, spread_ms=spread_ms, taps=taps, decay=decay, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def room_reverb(self, *, decay_seconds: float = 0.8, mix: float = 0.22, tone_hz: float = 8_000.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(room_reverb_effect(decay_seconds=decay_seconds, mix=mix, tone_hz=tone_hz), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def hall_reverb(self, *, decay_seconds: float = 1.8, mix: float = 0.28, tone_hz: float = 7_200.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(hall_reverb_effect(decay_seconds=decay_seconds, mix=mix, tone_hz=tone_hz), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def plate_reverb(self, *, decay_seconds: float = 1.2, mix: float = 0.24, tone_hz: float = 9_500.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(plate_reverb_effect(decay_seconds=decay_seconds, mix=mix, tone_hz=tone_hz), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def convolution_reverb(self, impulse_response: Any, *, mix: float = 0.28, normalize_ir: bool = True, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(convolution_reverb_effect(impulse_response, mix=mix, normalize_ir=normalize_ir), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def chorus(self, *, rate_hz: float = 0.9, depth_ms: float = 7.5, delay_ms: float = 18.0, mix: float = 0.35, feedback: float = 0.12, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(chorus_effect(rate_hz=rate_hz, depth_ms=depth_ms, delay_ms=delay_ms, mix=mix, feedback=feedback), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def flanger(self, *, rate_hz: float = 0.25, depth_ms: float = 1.8, delay_ms: float = 2.5, mix: float = 0.45, feedback: float = 0.35, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(flanger_effect(rate_hz=rate_hz, depth_ms=depth_ms, delay_ms=delay_ms, mix=mix, feedback=feedback), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def phaser(self, *, rate_hz: float = 0.35, depth: float = 0.75, center_hz: float = 900.0, feedback: float = 0.2, mix: float = 0.5, stages: int = 4, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(phaser_effect(rate_hz=rate_hz, depth=depth, center_hz=center_hz, feedback=feedback, mix=mix, stages=stages), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def tremolo(self, rate_hz: float, *, depth: float = 0.5, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(tremolo_effect(rate_hz, depth=depth), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def vibrato(self, *, rate_hz: float = 5.0, depth_ms: float = 3.5, delay_ms: float = 5.5, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(vibrato_effect(rate_hz=rate_hz, depth_ms=depth_ms, delay_ms=delay_ms), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def auto_pan(self, *, rate_hz: float = 0.35, depth: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(auto_pan_effect(rate_hz=rate_hz, depth=depth), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def rotary_speaker(self, *, rate_hz: float = 0.8, depth: float = 0.7, mix: float = 0.65, crossover_hz: float = 900.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(rotary_speaker_effect(rate_hz=rate_hz, depth=depth, mix=mix, crossover_hz=crossover_hz), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def ring_modulation(self, *, frequency_hz: float = 30.0, mix: float = 0.5, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(ring_modulation_effect(frequency_hz=frequency_hz, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def frequency_shifter(self, *, shift_hz: float = 120.0, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(frequency_shifter_effect(shift_hz=shift_hz, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def distortion(self, drive: float = 2.0, *, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(distortion_effect(drive), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def overdrive(self, drive: float = 1.8, *, tone: float = 0.55, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(overdrive_effect(drive=drive, tone=tone, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def fuzz(self, drive: float = 3.6, *, bias: float = 0.12, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(fuzz_effect(drive=drive, bias=bias, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def bitcrusher(self, bit_depth: int = 8, *, sample_rate_reduction: int = 4, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(bitcrusher_effect(bit_depth=bit_depth, sample_rate_reduction=sample_rate_reduction, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def waveshaper(self, amount: float = 1.4, *, symmetry: float = 0.0, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(waveshaper_effect(amount=amount, symmetry=symmetry, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def tube_saturation(self, drive: float = 1.6, *, bias: float = 0.08, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(tube_saturation_effect(drive=drive, bias=bias, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def tape_saturation(self, drive: float = 1.4, *, softness: float = 0.35, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(tape_saturation_effect(drive=drive, softness=softness, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def soft_clipping(self, threshold: float = 0.85, *, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(soft_clipping_effect(threshold=threshold), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def hard_clipping(self, threshold: float = 0.92, *, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(hard_clipping_effect(threshold=threshold), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def pitch_shift(self, semitones: float, *, fft_size: int = 1536, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(pitch_shift_effect(semitones, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def time_stretch(self, rate: float = 0.9, *, fft_size: int = 1536, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(time_stretch_effect(rate=rate, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def time_compression(self, rate: float = 1.15, *, fft_size: int = 1536, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(time_compression_effect(rate=rate, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def auto_tune(self, *, strength: float = 0.7, key: str = "C", scale: str = "chromatic", min_hz: float = 80.0, max_hz: float = 1_000.0, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(auto_tune_effect(strength=strength, key=key, scale=scale, min_hz=min_hz, max_hz=max_hz, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def harmonizer(self, intervals_semitones: list[float] | tuple[float, ...] | float = (7.0,), *, mix: float = 0.35, fft_size: int = 1536, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(harmonizer_effect(intervals_semitones, mix=mix, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def octaver(self, *, octaves_down: int = 1, octaves_up: int = 0, down_mix: float = 0.45, up_mix: float = 0.0, fft_size: int = 1536, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(octaver_effect(octaves_down=octaves_down, octaves_up=octaves_up, down_mix=down_mix, up_mix=up_mix, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def formant_shifting(self, shift: float = 1.12, *, mix: float = 1.0, fft_size: int = 1536, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(formant_shifting_effect(shift=shift, mix=mix, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def noise_reduction(self, *, strength: float = 0.5, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(noise_reduction_effect(strength=strength, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def voice_isolation(self, *, strength: float = 0.75, low_hz: float = 120.0, high_hz: float = 5_200.0, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(voice_isolation_effect(strength=strength, low_hz=low_hz, high_hz=high_hz, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def source_separation(self, *, target: str = "vocals", strength: float = 0.8, low_hz: float = 120.0, high_hz: float = 5_200.0, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(source_separation_effect(target=target, strength=strength, low_hz=low_hz, high_hz=high_hz, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def de_reverb(self, *, amount: float = 0.45, tail_ms: float = 240.0, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(de_reverb_effect(amount=amount, tail_ms=tail_ms, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def de_echo(self, *, amount: float = 0.45, min_delay_ms: float = 60.0, max_delay_ms: float = 800.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(de_echo_effect(amount=amount, min_delay_ms=min_delay_ms, max_delay_ms=max_delay_ms), block_size=block_size)  # type: ignore[return-value]

    def spectral_repair(self, *, strength: float = 0.35, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(spectral_repair_effect(strength=strength, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def ai_enhancer(self, *, amount: float = 0.6, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(ai_enhancer_effect(amount=amount, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def speech_enhancement(self, *, amount: float = 0.7, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(speech_enhancement_effect(amount=amount, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def glitch_effect(self, *, slice_ms: float = 70.0, repeat_probability: float = 0.22, dropout_probability: float = 0.12, reverse_probability: float = 0.10, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(glitch_effect_builder(slice_ms=slice_ms, repeat_probability=repeat_probability, dropout_probability=dropout_probability, reverse_probability=reverse_probability, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def stutter(self, *, slice_ms: float = 90.0, repeats: int = 3, interval_ms: float = 480.0, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(stutter_effect(slice_ms=slice_ms, repeats=repeats, interval_ms=interval_ms, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def tape_stop(self, *, stop_time_ms: float = 900.0, curve: float = 2.0, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(tape_stop_effect(stop_time_ms=stop_time_ms, curve=curve, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def reverse_reverb(self, *, decay_seconds: float = 1.2, mix: float = 0.45, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(reverse_reverb_effect(decay_seconds=decay_seconds, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def granular_synthesis(self, *, grain_ms: float = 80.0, overlap: float = 0.5, jitter_ms: float = 25.0, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(granular_synthesis_effect(grain_ms=grain_ms, overlap=overlap, jitter_ms=jitter_ms, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def time_slicing(self, *, slice_ms: float = 120.0, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(time_slicing_effect(slice_ms=slice_ms, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def random_pitch_mod(self, *, depth_semitones: float = 2.0, segment_ms: float = 180.0, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(random_pitch_mod_effect(depth_semitones=depth_semitones, segment_ms=segment_ms, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def vinyl_effect(self, *, noise: float = 0.08, wow: float = 0.15, crackle: float = 0.12, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(vinyl_effect_effect(noise=noise, wow=wow, crackle=crackle, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def radio_effect(self, *, noise_level: float = 0.04, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(radio_effect_effect(noise_level=noise_level, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def telephone_effect(self, *, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(telephone_effect_effect(mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def retro_8bit(self, *, bit_depth: int = 6, sample_rate_reduction: int = 8, mix: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(retro_8bit_effect(bit_depth=bit_depth, sample_rate_reduction=sample_rate_reduction, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def slow_motion_extreme(self, *, rate: float = 0.45, tone_hz: float = 4_800.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(slow_motion_extreme_effect(rate=rate, tone_hz=tone_hz), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def robot_voice(self, *, carrier_hz: float = 70.0, mix: float = 0.85, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(robot_voice_effect(carrier_hz=carrier_hz, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def alien_voice(self, *, shift_semitones: float = 5.0, formant_shift: float = 1.18, mix: float = 0.8, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(alien_voice_effect(shift_semitones=shift_semitones, formant_shift=formant_shift, mix=mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def fft_filter(self, *, low_hz: float = 80.0, high_hz: float = 12_000.0, mix: float = 1.0, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(fft_filter_effect(low_hz=low_hz, high_hz=high_hz, mix=mix, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def spectral_gating(self, *, threshold_db: float = -42.0, floor: float = 0.08, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(spectral_gating_effect(threshold_db=threshold_db, floor=floor, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def spectral_blur(self, *, amount: float = 0.45, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(spectral_blur_effect(amount=amount, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def spectral_freeze(self, *, start_ms: float = 120.0, mix: float = 0.7, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(spectral_freeze_effect(start_ms=start_ms, mix=mix, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def spectral_morphing(self, *, amount: float = 0.5, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(spectral_morphing_effect(amount=amount, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def phase_vocoder(self, *, rate: float = 0.85, fft_size: int = 1536, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(phase_vocoder_effect(rate=rate, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def harmonic_percussive_separation(self, *, target: str = "harmonic", mix: float = 1.0, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(harmonic_percussive_separation_effect(target=target, mix=mix, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def spectral_delay(self, *, max_delay_ms: float = 240.0, feedback: float = 0.15, mix: float = 0.35, fft_size: int = 1024, hop_size: int = 512, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        _ = workers
        return self.apply(spectral_delay_effect(max_delay_ms=max_delay_ms, feedback=feedback, mix=mix, fft_size=fft_size, hop_size=hop_size), block_size=block_size)  # type: ignore[return-value]

    def compressor(self, *, threshold_db: float = -18.0, ratio: float = 4.0, attack_ms: float = 10.0, release_ms: float = 80.0, makeup_db: float = 0.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(compressor_effect(threshold_db=threshold_db, ratio=ratio, attack_ms=attack_ms, release_ms=release_ms, makeup_db=makeup_db), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def downward_compression(self, *, threshold_db: float = -18.0, ratio: float = 4.0, attack_ms: float = 10.0, release_ms: float = 80.0, makeup_db: float = 0.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(downward_compression_effect(threshold_db=threshold_db, ratio=ratio, attack_ms=attack_ms, release_ms=release_ms, makeup_db=makeup_db), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def upward_compression(self, *, threshold_db: float = -42.0, ratio: float = 2.0, attack_ms: float = 12.0, release_ms: float = 120.0, max_gain_db: float = 18.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(upward_compression_effect(threshold_db=threshold_db, ratio=ratio, attack_ms=attack_ms, release_ms=release_ms, max_gain_db=max_gain_db), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def limiter(self, *, ceiling_db: float = -1.0, attack_ms: float = 1.0, release_ms: float = 60.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(limiter_effect(ceiling_db=ceiling_db, attack_ms=attack_ms, release_ms=release_ms), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def expander(self, *, threshold_db: float = -35.0, ratio: float = 2.0, attack_ms: float = 8.0, release_ms: float = 80.0, makeup_db: float = 0.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(expander_effect(threshold_db=threshold_db, ratio=ratio, attack_ms=attack_ms, release_ms=release_ms, makeup_db=makeup_db), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def noise_gate(self, *, threshold_db: float = -45.0, attack_ms: float = 3.0, release_ms: float = 60.0, floor_db: float = -80.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(noise_gate_effect(threshold_db=threshold_db, attack_ms=attack_ms, release_ms=release_ms, floor_db=floor_db), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def deesser(self, *, frequency_hz: float = 6_500.0, threshold_db: float = -28.0, ratio: float = 4.0, attack_ms: float = 2.0, release_ms: float = 60.0, amount: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(deesser_effect(frequency_hz=frequency_hz, threshold_db=threshold_db, ratio=ratio, attack_ms=attack_ms, release_ms=release_ms, amount=amount), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def transient_shaper(self, *, attack: float = 0.7, sustain: float = 0.2, attack_ms: float = 18.0, release_ms: float = 120.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(transient_shaper_effect(attack=attack, sustain=sustain, attack_ms=attack_ms, release_ms=release_ms), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def multiband_compressor(
        self,
        *,
        low_cut_hz: float = 180.0,
        high_cut_hz: float = 3_200.0,
        low_threshold_db: float = -24.0,
        mid_threshold_db: float = -18.0,
        high_threshold_db: float = -20.0,
        low_ratio: float = 2.2,
        mid_ratio: float = 3.0,
        high_ratio: float = 2.4,
        attack_ms: float = 10.0,
        release_ms: float = 90.0,
        low_makeup_db: float = 0.0,
        mid_makeup_db: float = 0.0,
        high_makeup_db: float = 0.0,
        block_size: int = 2048,
        workers: int = 1,
        lazy: bool = False,
    ) -> "AudioClip | DeferredClip":
        processor = multiband_compressor_builder(
            self.sample_rate,
            low_cut_hz=low_cut_hz,
            high_cut_hz=high_cut_hz,
            low_threshold_db=low_threshold_db,
            mid_threshold_db=mid_threshold_db,
            high_threshold_db=high_threshold_db,
            low_ratio=low_ratio,
            mid_ratio=mid_ratio,
            high_ratio=high_ratio,
            attack_ms=attack_ms,
            release_ms=release_ms,
            low_makeup_db=low_makeup_db,
            mid_makeup_db=mid_makeup_db,
            high_makeup_db=high_makeup_db,
            block_size=block_size,
            workers=workers,
        )
        return self.process_bands(processor, lazy=lazy)

    def pan(self, position: float, *, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(pan_effect(position), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def stereo_width(self, width: float = 1.0, *, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(stereo_width_effect(width), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def stereo_widening(self, amount: float = 1.25, *, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(stereo_widening_effect(amount), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def mid_side_processing(self, *, mid_gain_db: float = 0.0, side_gain_db: float = 0.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(mid_side_processing_effect(mid_gain_db=mid_gain_db, side_gain_db=side_gain_db), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def stereo_imager(self, *, low_width: float = 0.9, high_width: float = 1.35, crossover_hz: float = 280.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(stereo_imager_effect(low_width=low_width, high_width=high_width, crossover_hz=crossover_hz), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def binaural_effect(self, *, azimuth_deg: float = 25.0, distance: float = 1.0, room_mix: float = 0.08, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(binaural_effect_effect(azimuth_deg=azimuth_deg, distance=distance, room_mix=room_mix), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def spatial_positioning(self, *, azimuth_deg: float = 25.0, elevation_deg: float = 0.0, distance: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(spatial_positioning_effect(azimuth_deg=azimuth_deg, elevation_deg=elevation_deg, distance=distance), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def hrtf_simulation(self, *, azimuth_deg: float = 30.0, elevation_deg: float = 0.0, distance: float = 1.0, block_size: int = 2048, workers: int = 1) -> "AudioClip":
        return self.apply(hrtf_simulation_effect(azimuth_deg=azimuth_deg, elevation_deg=elevation_deg, distance=distance), block_size=block_size, workers=workers)  # type: ignore[return-value]

    def resample(self, target_sample_rate: int) -> "AudioClip":
        target_rate = max(1, int(target_sample_rate))
        resampled = resample_audio(self.samples, self.sample_rate, target_rate)
        return AudioClip(
            samples=resampled,
            sample_rate=target_rate,
            _pipeline_steps=self._pipeline_steps + (f"resample(sample_rate={target_rate})",),
        )

    def dither(self, *, bit_depth: int = 16) -> "AudioClip":
        dithered = dither_audio(self.samples, bit_depth=bit_depth)
        return self._with_pipeline_steps(dithered, (f"dither(bit_depth={int(bit_depth)})",))

    def bit_depth_conversion(self, bit_depth: int = 16, *, dither: bool = True) -> "AudioClip":
        converted = bit_depth_convert_audio(self.samples, bit_depth=bit_depth, dither=dither)
        return self._with_pipeline_steps(
            converted,
            (f"bit_depth_conversion(bit_depth={int(bit_depth)}, dither={bool(dither)})",),
        )

    def loudness_normalization(self, *, target_lufs: float = -16.0) -> "AudioClip":
        normalized = loudness_normalize_audio(self.samples, self.sample_rate, target_lufs=target_lufs)
        return self._with_pipeline_steps(normalized, (f"loudness_normalization(target_lufs={float(target_lufs):.2f})",))

    def peak_detection(self) -> float:
        return peak_dbfs_analysis(self.samples)

    def rms_analysis(self) -> float:
        return rms_dbfs_analysis(self.samples)

    def loudness_lufs(self) -> float:
        return integrated_lufs(self.samples, self.sample_rate)

    def envelope_follower(self, *, attack_ms: float = 10.0, release_ms: float = 80.0) -> np.ndarray:
        return envelope_follower_analysis(
            self.samples,
            self.sample_rate,
            attack_ms=attack_ms,
            release_ms=release_ms,
        )


@dataclass(frozen=True, slots=True)
class _DeferredOperation:
    kind: str
    payload: Any


@dataclass(slots=True)
class DeferredClip:
    source: AudioClip
    operations: list[_DeferredOperation] = field(default_factory=list)

    @property
    def sample_rate(self) -> int:
        return self.source.sample_rate

    @property
    def channels(self) -> int:
        return self.source.channels

    @property
    def duration_seconds(self) -> float:
        return self.source.duration_seconds

    def _clone_with(self, operation: _DeferredOperation) -> "DeferredClip":
        operations = list(self.operations)
        if operations and operation.kind == "pipeline" and operations[-1].kind == "pipeline":
            merged = operations[-1].payload.clone()
            merged.extend(operation.payload.effects)
            operations[-1] = _DeferredOperation("pipeline", merged)
        else:
            operations.append(operation)
        return DeferredClip(self.source, operations)

    def _signature(self) -> str:
        parts: list[str] = []
        for operation in self.operations:
            if operation.kind == "pipeline":
                parts.append(f"pipeline:{operation.payload.signature()}")
            elif operation.kind == "bands":
                parts.append(f"bands:{id(operation.payload)}")
            elif operation.kind == "normalize":
                parts.append(f"normalize:{operation.payload}")
            else:
                parts.append(f"{operation.kind}:{repr(operation.payload)}")
        return "|".join(parts)

    def pipeline_info(self) -> str:
        steps = list(self.source._pipeline_steps)
        for operation in self.operations:
            if operation.kind == "pipeline":
                steps.extend(effect.describe() for effect in operation.payload.effects)
            elif operation.kind == "bands":
                steps.append(f"multiband_pipeline(bands={len(operation.payload.bands)})")
            elif operation.kind == "normalize":
                steps.append(f"normalize(headroom_db={float(operation.payload):.2f}dB)")
        return _format_pipeline_steps(tuple(steps))

    def apply(self, *effects: Any, block_size: int = 2048, workers: int = 1) -> "DeferredClip":
        pipeline = Pipeline.from_effects(
            self.sample_rate,
            *effects,
            channels=self.channels,
            block_size=block_size,
            workers=workers,
        )
        return self.apply_pipeline(pipeline)

    def preset(self, name: str, *, block_size: int = 2048, workers: int = 1) -> "DeferredClip":
        return self.apply(name, block_size=block_size, workers=workers)

    def apply_pipeline(self, pipeline: Pipeline) -> "DeferredClip":
        return self._clone_with(_DeferredOperation("pipeline", pipeline.clone()))

    def process_bands(self, processor: MultibandPipeline) -> "DeferredClip":
        return self._clone_with(_DeferredOperation("bands", processor))

    def normalize(self, headroom_db: float = 1.0) -> "DeferredClip":
        return self._clone_with(_DeferredOperation("normalize", float(headroom_db)))

    def render(self) -> AudioClip:
        signature = self._signature()
        if signature in self.source._render_cache:
            return self.source._render_cache[signature].copy()

        clip = self.source.copy()
        for operation in self.operations:
            if operation.kind == "pipeline":
                clip = clip.apply_pipeline(operation.payload, lazy=False)  # type: ignore[assignment]
            elif operation.kind == "bands":
                clip = clip.process_bands(operation.payload, lazy=False)  # type: ignore[assignment]
            elif operation.kind == "normalize":
                clip = clip.normalize(headroom_db=operation.payload, lazy=False)  # type: ignore[assignment]
            else:
                raise RuntimeError(f"Unknown deferred operation kind: {operation.kind}")

        final_clip = AudioClip(
            clip.samples,
            clip.sample_rate,
            _pipeline_steps=tuple(
                line.split("] ", 1)[1] if "] " in line else line
                for line in self.pipeline_info().splitlines()
            )
            if self.pipeline_info() != "(source clip)"
            else tuple(),
        )
        self.source._render_cache[signature] = final_clip.copy()
        return final_clip

    def numpy(self) -> np.ndarray:
        return self.render().numpy()

    def export(
        self,
        path: str | Path,
        *,
        codec: str | None = None,
        bitrate: str | None = None,
        format: str | None = None,
        sample_rate: int | None = None,
        channels: int | None = None,
        overwrite: bool = True,
    ) -> Path:
        return self.render().export(
            path,
            codec=codec,
            bitrate=bitrate,
            format=format,
            sample_rate=sample_rate,
            channels=channels,
            overwrite=overwrite,
        )

    def available_presets(self) -> tuple[str, ...]:
        return preset_names()

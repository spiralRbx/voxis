from __future__ import annotations

import numpy as np
import voxis.pipeline as pipeline_module

from voxis import (
    AudioClip,
    MultibandPipeline,
    Pipeline,
    auto_pan,
    bandpass,
    chorus,
    compressor,
    convolution_reverb,
    delay,
    distortion,
    eq_band,
    gain,
    limiter,
    lowpass,
    notch,
    parametric_eq,
    peak_eq,
    ping_pong_delay,
    preset_names,
    room_reverb,
    stereo_width,
    tremolo,
)


def make_stereo_sine(
    *,
    sample_rate: int = 48_000,
    duration_seconds: float = 0.5,
    frequency_hz: float = 440.0,
) -> np.ndarray:
    timeline = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    mono = 0.25 * np.sin(2.0 * np.pi * frequency_hz * timeline)
    return np.column_stack([mono, mono]).astype(np.float32)


def test_pipeline_keeps_shape_and_dtype() -> None:
    samples = make_stereo_sine()
    pipeline = (
        Pipeline(sample_rate=48_000, channels=2, block_size=1024)
        >> [
            gain(3.0),
            distortion(2.2),
            lowpass(8_000.0, stages=2),
            tremolo(5.0, depth=0.35),
            compressor(threshold_db=-18.0, ratio=3.0),
            limiter(),
        ]
    )

    output = pipeline.process(samples)

    assert output.shape == samples.shape
    assert output.dtype == np.float32
    assert np.isfinite(output).all()
    assert not np.allclose(output, samples)


def test_delay_pushes_energy_forward() -> None:
    samples = np.zeros((48_000, 2), dtype=np.float32)
    samples[0] = (1.0, 1.0)

    output = Pipeline.from_effects(
        48_000,
        delay(100.0, feedback=0.4, mix=0.5),
        channels=2,
        block_size=512,
    ).process(samples)

    delayed_index = 4_800
    assert output[0, 0] != 0.0
    assert abs(output[delayed_index, 0]) > 0.1


def test_eq_family_effects_are_processable() -> None:
    samples = make_stereo_sine(frequency_hz=1_500.0)
    pipeline = Pipeline.from_effects(
        48_000,
        bandpass(1_500.0, q=1.2),
        notch(400.0, q=2.0),
        peak_eq(2_000.0, 2.5, q=0.9),
        parametric_eq(
            eq_band("low_shelf", 120.0, gain_db=1.5),
            eq_band("peak", 3_000.0, gain_db=2.0, q=1.1),
            eq_band("high_shelf", 9_000.0, gain_db=1.0),
        ),
        channels=2,
    )

    output = pipeline.process(samples)

    assert output.shape == samples.shape
    assert output.dtype == np.float32
    assert np.isfinite(output).all()


def test_python_effects_process_finite_audio() -> None:
    samples = make_stereo_sine(duration_seconds=0.35)
    ir = np.zeros((512, 1), dtype=np.float32)
    ir[0, 0] = 1.0
    ir[120, 0] = 0.35

    pipeline = Pipeline.from_effects(
        48_000,
        ping_pong_delay(160.0, feedback=0.35, mix=0.25),
        chorus(rate_hz=0.8, depth_ms=6.0, mix=0.25),
        room_reverb(decay_seconds=0.6, mix=0.18),
        auto_pan(rate_hz=0.3, depth=0.8),
        convolution_reverb(ir, mix=0.12),
        channels=2,
    )

    output = pipeline.process(samples)

    assert output.shape == samples.shape
    assert output.dtype == np.float32
    assert np.isfinite(output).all()


def test_automation_delay_is_supported() -> None:
    samples = make_stereo_sine(duration_seconds=0.2)
    pipeline = Pipeline.from_effects(
        48_000,
        delay(lambda t: 80.0 + t * 40.0, feedback=0.2, mix=0.2),
        channels=2,
    )

    output = pipeline.process(samples)
    assert output.shape == samples.shape
    assert np.isfinite(output).all()


def test_multiband_pipeline_recombines_signal() -> None:
    samples = make_stereo_sine(frequency_hz=880.0)

    lows = Pipeline.from_effects(48_000, gain(1.5), channels=2)
    highs = Pipeline.from_effects(48_000, stereo_width(1.2), channels=2)

    multiband = (
        MultibandPipeline(sample_rate=48_000, block_size=1024)
        .add_band("low", high_cut_hz=250.0, pipeline=lows)
        .add_band("mid", low_cut_hz=250.0, high_cut_hz=2_000.0)
        .add_band("high", low_cut_hz=2_000.0, pipeline=highs)
    )

    output = multiband.process(samples)

    assert output.shape == samples.shape
    assert output.dtype == np.float32
    assert np.isfinite(output).all()


def test_audioclip_lazy_preset_render_and_cache() -> None:
    clip = AudioClip.from_array(make_stereo_sine() * 0.15, 48_000)
    first = clip.apply("radio", lazy=True).normalize(headroom_db=1.0).render()
    second = clip.apply("radio", lazy=True).normalize(headroom_db=1.0).render()

    assert len(clip._render_cache) == 1
    assert np.allclose(first.samples, second.samples)


def test_pipeline_info_contains_human_readable_steps() -> None:
    pipeline = Pipeline(48_000, channels=2) >> [distortion(1.6), lowpass(9_000.0), delay(135.0)]
    info = pipeline.pipeline_info()
    assert "[0] distortion" in info
    assert "lowpass" in info
    assert "delay_ms=135.00ms" in info


def test_preset_registry_exposes_expected_names() -> None:
    presets = set(preset_names())
    assert {"radio", "vocal_enhance", "cinematic", "wide_chorus"}.issubset(presets)


def test_native_effects_fall_back_to_python_when_extension_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(pipeline_module, "_process_pipeline", None)
    monkeypatch.setattr(pipeline_module, "_IMPORT_ERROR", ImportError("native core unavailable"))

    samples = make_stereo_sine(duration_seconds=0.3, frequency_hz=880.0)
    clip = AudioClip.from_array(samples, 48_000)

    processed = clip.apply("podcast_clean")

    assert processed.samples.shape == samples.shape
    assert processed.samples.dtype == np.float32
    assert np.isfinite(processed.samples).all()


def test_eq_family_falls_back_to_python_when_extension_is_missing(monkeypatch) -> None:
    monkeypatch.setattr(pipeline_module, "_process_pipeline", None)
    monkeypatch.setattr(pipeline_module, "_IMPORT_ERROR", ImportError("native core unavailable"))

    samples = make_stereo_sine(frequency_hz=1_500.0)
    pipeline = Pipeline.from_effects(
        48_000,
        bandpass(1_500.0, q=1.2),
        notch(400.0, q=2.0),
        peak_eq(2_000.0, 2.5, q=0.9),
        channels=2,
    )

    output = pipeline.process(samples)

    assert output.shape == samples.shape
    assert output.dtype == np.float32
    assert np.isfinite(output).all()

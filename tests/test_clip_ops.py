from __future__ import annotations

import numpy as np

from voxis import AudioClip


def make_clip(*, sample_rate: int = 48_000, duration_seconds: float = 0.5, channels: int = 2) -> AudioClip:
    timeline = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    mono = 0.2 * np.sin(2.0 * np.pi * 220.0 * timeline)
    if channels == 1:
        samples = mono[:, None]
    else:
        samples = np.column_stack([mono, 0.18 * np.sin(2.0 * np.pi * 330.0 * timeline)])
    return AudioClip.from_array(samples.astype(np.float32), sample_rate)


def test_basic_clip_operations_are_available() -> None:
    clip = make_clip(duration_seconds=0.4)

    faded = clip.fade_in(120.0).fade_out(120.0)
    trimmed = faded.trim(start_ms=20.0, end_ms=220.0)
    cut = trimmed.cut(start_ms=30.0, end_ms=60.0)
    reversed_clip = cut.reverse()
    dc_removed = reversed_clip.remove_dc_offset()
    mono = dc_removed.to_mono()
    stereo = mono.to_stereo()

    assert stereo.channels == 2
    assert stereo.frames > 0
    assert np.isfinite(stereo.samples).all()
    assert "fade_in" in stereo.pipeline_info()
    assert "remove_dc_offset" in stereo.pipeline_info()


def test_duration_seconds_and_duration_ms_are_available() -> None:
    clip = make_clip(duration_seconds=0.25)
    deferred = clip.lazy()

    assert abs(clip.duration_seconds - 0.25) < 1e-6
    assert abs(clip.duration_ms - 250.0) < 1e-3
    assert abs(deferred.duration_seconds - 0.25) < 1e-6
    assert abs(deferred.duration_ms - 250.0) < 1e-3


def test_remove_silence_and_crossfade_behave_as_expected() -> None:
    sample_rate = 48_000
    tone = make_clip(sample_rate=sample_rate, duration_seconds=0.1).samples
    silence = np.zeros((sample_rate // 8, 2), dtype=np.float32)
    source = AudioClip.from_array(np.concatenate([silence, tone, silence, tone], axis=0), sample_rate)

    compact = source.remove_silence(threshold_db=-60.0, min_silence_ms=40.0, padding_ms=5.0)
    assert compact.frames < source.frames

    left = make_clip(duration_seconds=0.2)
    right = make_clip(duration_seconds=0.15)
    merged = left.crossfade(right, 50.0)
    fade_frames = int(round(50.0 * sample_rate / 1000.0))
    assert merged.frames == left.frames + right.frames - fade_frames
    assert np.isfinite(merged.samples).all()


def test_dynamic_item_two_extensions_process_audio() -> None:
    clip = make_clip(duration_seconds=0.35)

    downward = clip.downward_compression(threshold_db=-20.0, ratio=3.5)
    upward = downward.upward_compression(threshold_db=-38.0, ratio=2.0, max_gain_db=12.0)
    shaped = upward.transient_shaper(attack=0.6, sustain=0.2)
    multiband = shaped.multiband_compressor(low_cut_hz=160.0, high_cut_hz=2800.0)

    assert multiband.samples.shape == clip.samples.shape
    assert multiband.samples.dtype == np.float32
    assert np.isfinite(multiband.samples).all()
    assert "multiband_pipeline" in multiband.pipeline_info()

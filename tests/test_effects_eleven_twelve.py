from __future__ import annotations

import numpy as np

from voxis import AudioClip, effect_names


def make_clip(*, sample_rate: int = 24_000, duration_seconds: float = 0.4) -> AudioClip:
    timeline = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    vocal = 0.18 * np.sin(2.0 * np.pi * 220.0 * timeline)
    pad = 0.08 * np.sin(2.0 * np.pi * 440.0 * timeline + 0.5)
    side = 0.05 * np.sin(2.0 * np.pi * 1600.0 * timeline)
    left = vocal + pad + side
    right = vocal + pad - side
    return AudioClip.from_array(np.column_stack([left, right]).astype(np.float32), sample_rate)


def test_item_eleven_spatial_effects_process_audio() -> None:
    clip = make_clip()

    widened = clip.stereo_widening(1.3)
    mid_side = clip.mid_side_processing(mid_gain_db=0.5, side_gain_db=1.5)
    imaged = clip.stereo_imager(low_width=0.85, high_width=1.4)
    binaural = clip.binaural_effect(azimuth_deg=20.0, distance=1.2, room_mix=0.05)
    positioned = clip.spatial_positioning(azimuth_deg=35.0, elevation_deg=12.0, distance=1.1)
    hrtf = clip.hrtf_simulation(azimuth_deg=-28.0, elevation_deg=6.0, distance=1.0)

    for processed in (widened, mid_side, imaged, binaural, positioned, hrtf):
        assert processed.samples.shape[1] == 2
        assert processed.samples.dtype == np.float32
        assert np.isfinite(processed.samples).all()


def test_item_twelve_utilities_and_analysis() -> None:
    clip = make_clip()

    resampled = clip.resample(32_000)
    dithered = clip.dither(bit_depth=12)
    converted = clip.bit_depth_conversion(bit_depth=12)
    normalized = clip.loudness_normalization(target_lufs=-18.0)
    envelope = clip.envelope_follower(attack_ms=8.0, release_ms=60.0)

    assert resampled.sample_rate == 32_000
    assert dithered.samples.shape == clip.samples.shape
    assert converted.samples.shape == clip.samples.shape
    assert normalized.samples.shape == clip.samples.shape
    assert envelope.shape[0] == clip.samples.shape[0]
    assert np.isfinite(envelope).all()
    assert np.isfinite(clip.peak_detection())
    assert np.isfinite(clip.rms_analysis())
    assert np.isfinite(clip.loudness_lufs())


def test_effect_names_include_item_eleven() -> None:
    names = set(effect_names())
    assert {"stereo_widening", "mid_side_processing", "stereo_imager", "binaural_effect", "spatial_positioning", "hrtf_simulation"} <= names

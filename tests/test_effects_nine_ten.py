from __future__ import annotations

import numpy as np

from voxis import AudioClip


def make_clip(*, sample_rate: int = 24_000, duration_seconds: float = 0.35) -> AudioClip:
    timeline = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    left = 0.18 * np.sin(2.0 * np.pi * 220.0 * timeline)
    left += 0.08 * np.sin(2.0 * np.pi * 660.0 * timeline)
    right = 0.16 * np.sin(2.0 * np.pi * 330.0 * timeline)
    right += 0.05 * np.sin(2.0 * np.pi * 1100.0 * timeline)
    return AudioClip.from_array(np.column_stack([left, right]).astype(np.float32), sample_rate)


def test_item_nine_effects_process_audio() -> None:
    clip = make_clip()

    processed = (
        clip.glitch_effect(mix=0.85)
        .stutter(repeats=2, mix=0.6)
        .tape_stop(mix=0.7)
        .reverse_reverb(mix=0.3)
        .granular_synthesis(mix=0.5)
        .time_slicing(mix=0.7)
        .random_pitch_mod(mix=0.5)
        .vinyl_effect(mix=0.8)
        .radio_effect(mix=0.7)
        .telephone_effect(mix=0.65)
        .retro_8bit(mix=0.75)
        .robot_voice(mix=0.6)
        .alien_voice(mix=0.55)
    )

    assert processed.samples.shape == clip.samples.shape
    assert processed.samples.dtype == np.float32
    assert np.isfinite(processed.samples).all()


def test_item_ten_effects_process_audio() -> None:
    clip = make_clip()

    fft_filtered = clip.fft_filter(low_hz=120.0, high_hz=8_000.0, mix=1.0)
    gated = clip.spectral_gating(threshold_db=-45.0, floor=0.12)
    blurred = clip.spectral_blur(amount=0.35)
    frozen = clip.spectral_freeze(start_ms=60.0, mix=0.5)
    morphed = clip.spectral_morphing(amount=0.4)
    vocoded = clip.phase_vocoder(rate=0.9)
    harmonic = clip.harmonic_percussive_separation(target="harmonic", mix=1.0)
    delayed = clip.spectral_delay(max_delay_ms=120.0, feedback=0.15, mix=0.25)

    for processed in (fft_filtered, gated, blurred, frozen, morphed, harmonic, delayed):
        assert processed.samples.shape == clip.samples.shape
        assert processed.samples.dtype == np.float32
        assert np.isfinite(processed.samples).all()

    assert vocoded.samples.shape[1] == clip.samples.shape[1]
    assert vocoded.samples.dtype == np.float32
    assert np.isfinite(vocoded.samples).all()

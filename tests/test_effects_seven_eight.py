from __future__ import annotations

import numpy as np

from voxis import AudioClip


def make_clip(*, sample_rate: int = 24_000, duration_seconds: float = 0.3) -> AudioClip:
    timeline = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    left = 0.2 * np.sin(2.0 * np.pi * 220.0 * timeline)
    right = 0.18 * np.sin(2.0 * np.pi * 330.0 * timeline)
    return AudioClip.from_array(np.column_stack([left, right]).astype(np.float32), sample_rate)


def test_item_seven_effects_process_audio() -> None:
    clip = make_clip()

    shifted = clip.pitch_shift(3.0)
    stretched = clip.time_stretch(rate=0.85)
    compressed = clip.time_compression(rate=1.18)
    tuned = clip.auto_tune(strength=0.6)
    harmonized = clip.harmonizer((7.0,), mix=0.3)
    octaved = clip.octaver(down_mix=0.4, up_mix=0.15)
    formanted = clip.formant_shifting(shift=1.1, mix=0.75)

    assert shifted.samples.shape == clip.samples.shape
    assert tuned.samples.shape == clip.samples.shape
    assert harmonized.samples.shape == clip.samples.shape
    assert octaved.samples.shape == clip.samples.shape
    assert formanted.samples.shape == clip.samples.shape
    assert stretched.samples.shape[0] > clip.samples.shape[0]
    assert compressed.samples.shape[0] < clip.samples.shape[0]
    assert np.isfinite(stretched.samples).all()
    assert np.isfinite(compressed.samples).all()


def test_item_eight_effects_process_audio() -> None:
    clip = make_clip()

    reduced = clip.noise_reduction(strength=0.35)
    isolated = clip.voice_isolation(strength=0.65)
    separated = clip.source_separation(strength=0.7)
    dereverbed = clip.de_reverb(amount=0.25)
    deechoed = clip.de_echo(amount=0.3)
    repaired = clip.spectral_repair(strength=0.25)
    enhanced = clip.ai_enhancer(amount=0.45)
    speech = clip.speech_enhancement(amount=0.55)

    for processed in (reduced, isolated, separated, dereverbed, deechoed, repaired, enhanced, speech):
        assert processed.samples.shape == clip.samples.shape
        assert processed.samples.dtype == np.float32
        assert np.isfinite(processed.samples).all()

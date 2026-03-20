from __future__ import annotations

import numpy as np

from voxis import (
    AudioClip,
    Pipeline,
    dynamic_eq,
    formant_filter,
    frequency_shifter,
    graphic_eq,
    resonant_filter,
    ring_modulation,
    rotary_speaker,
)


def make_clip(*, sample_rate: int = 48_000, duration_seconds: float = 0.25) -> AudioClip:
    timeline = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    left = 0.16 * np.sin(2.0 * np.pi * 220.0 * timeline)
    right = 0.14 * np.sin(2.0 * np.pi * 440.0 * timeline)
    return AudioClip.from_array(np.column_stack([left, right]).astype(np.float32), sample_rate)


def test_missing_item_three_and_four_effects_process_audio() -> None:
    clip = make_clip()
    pipeline = Pipeline.from_effects(
        clip.sample_rate,
        resonant_filter(1_200.0, resonance=2.2),
        dynamic_eq(2_800.0, threshold_db=-26.0, cut_db=-5.0),
        graphic_eq({100.0: 1.0, 250.0: -0.5, 1_000.0: 1.5, 4_000.0: -1.0, 12_000.0: 0.8}),
        formant_filter(1.5, intensity=0.8),
        rotary_speaker(rate_hz=0.9, depth=0.65, mix=0.55),
        ring_modulation(frequency_hz=35.0, mix=0.35),
        frequency_shifter(shift_hz=90.0, mix=0.8),
        channels=2,
        block_size=512,
    )

    output = pipeline.process(clip.samples)
    assert output.shape == clip.samples.shape
    assert output.dtype == np.float32
    assert np.isfinite(output).all()

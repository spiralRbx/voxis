from __future__ import annotations

import numpy as np

from voxis import (
    AudioClip,
    Pipeline,
    bitcrusher,
    echo,
    fuzz,
    hard_clipping,
    overdrive,
    soft_clipping,
    tape_saturation,
    tube_saturation,
    waveshaper,
)


def make_clip(*, sample_rate: int = 48_000, duration_seconds: float = 0.25) -> AudioClip:
    timeline = np.arange(int(sample_rate * duration_seconds), dtype=np.float32) / sample_rate
    left = 0.18 * np.sin(2.0 * np.pi * 110.0 * timeline)
    right = 0.16 * np.sin(2.0 * np.pi * 220.0 * timeline)
    return AudioClip.from_array(np.column_stack([left, right]).astype(np.float32), sample_rate)


def test_missing_item_five_and_six_effects_process_audio() -> None:
    clip = make_clip()
    pipeline = Pipeline.from_effects(
        clip.sample_rate,
        echo(delay_ms=280.0, feedback=0.32, mix=0.24),
        overdrive(drive=1.6, tone=0.58, mix=0.9),
        fuzz(drive=3.2, bias=0.08, mix=0.5),
        bitcrusher(bit_depth=8, sample_rate_reduction=4, mix=0.35),
        waveshaper(amount=1.2, symmetry=0.1, mix=0.65),
        tube_saturation(drive=1.5, bias=0.04, mix=0.7),
        tape_saturation(drive=1.3, softness=0.4, mix=0.6),
        soft_clipping(threshold=0.86),
        hard_clipping(threshold=0.95),
        channels=2,
        block_size=512,
    )

    output = pipeline.process(clip.samples)
    assert output.shape == clip.samples.shape
    assert output.dtype == np.float32
    assert np.isfinite(output).all()

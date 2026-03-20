from __future__ import annotations

import numpy as np
import pytest

from voxis import Pipeline, auto_pan, chorus, flanger, phaser, ping_pong_delay, vibrato
from voxis._python_dsp import process_python_effect


def make_reference_audio(
    *,
    sample_rate: int = 48_000,
    duration_seconds: float = 0.18,
) -> np.ndarray:
    frames = int(sample_rate * duration_seconds)
    timeline = np.arange(frames, dtype=np.float32) / sample_rate
    left = 0.18 * np.sin(2.0 * np.pi * 220.0 * timeline)
    right = 0.15 * np.sin(2.0 * np.pi * 330.0 * timeline + 0.35)
    rng = np.random.default_rng(42)
    noise = rng.normal(0.0, 0.015, size=(frames, 2)).astype(np.float32)
    return np.column_stack([left, right]).astype(np.float32) + noise


@pytest.mark.parametrize(
    ("effect", "atol"),
    [
        (ping_pong_delay(160.0, feedback=0.35, mix=0.25), 1e-6),
        (chorus(rate_hz=0.8, depth_ms=6.0, delay_ms=17.0, mix=0.28, feedback=0.1), 2e-3),
        (flanger(rate_hz=0.3, depth_ms=1.6, delay_ms=2.0, mix=0.42, feedback=0.3), 2e-6),
        (vibrato(rate_hz=5.2, depth_ms=3.0, delay_ms=5.0), 5e-6),
        (auto_pan(rate_hz=0.45, depth=0.85), 1e-5),
        (phaser(rate_hz=0.4, depth=0.7, center_hz=800.0, feedback=0.18, mix=0.48, stages=4), 1e-4),
    ],
)
def test_native_fast_path_matches_python_reference(effect, atol: float) -> None:
    samples = make_reference_audio()
    pipeline = Pipeline.from_effects(48_000, effect, channels=2, block_size=256)

    native = pipeline.process(samples)
    python = process_python_effect(effect, samples, 48_000, 256)

    assert native.shape == python.shape
    assert native.dtype == np.float32
    assert np.max(np.abs(native - python)) <= atol

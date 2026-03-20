from __future__ import annotations

from typing import Any

from ._util import flatten_effects
from .effects import (
    Effect,
    chorus,
    compressor,
    deesser,
    distortion,
    expander,
    hall_reverb,
    high_shelf,
    highpass,
    limiter,
    low_shelf,
    lowpass,
    noise_gate,
    parametric_eq,
    peak_eq,
    room_reverb,
    slapback,
    stereo_width,
)


PRESETS: dict[str, tuple[Any, ...]] = {
    "radio": (
        highpass(180.0, stages=2),
        lowpass(3_200.0, stages=2),
        distortion(1.2),
        compressor(threshold_db=-24.0, ratio=4.5, attack_ms=4.0, release_ms=90.0, makeup_db=2.0),
        limiter(ceiling_db=-1.0),
    ),
    "vocal_enhance": (
        highpass(85.0, stages=2),
        peak_eq(250.0, -2.0, q=1.1),
        peak_eq(3_200.0, 3.0, q=0.9),
        high_shelf(11_000.0, 1.8),
        deesser(frequency_hz=6_500.0, threshold_db=-30.0, ratio=4.5, amount=0.75),
        compressor(threshold_db=-20.0, ratio=3.0, attack_ms=8.0, release_ms=90.0, makeup_db=1.5),
        limiter(ceiling_db=-1.0),
    ),
    "cinematic": (
        low_shelf(120.0, 2.0),
        peak_eq(2_500.0, 1.5, q=0.8),
        high_shelf(9_500.0, 2.0),
        hall_reverb(decay_seconds=1.9, mix=0.16, tone_hz=7_000.0),
        stereo_width(1.3),
        compressor(threshold_db=-16.0, ratio=2.0, attack_ms=20.0, release_ms=140.0, makeup_db=1.0),
        limiter(ceiling_db=-1.0),
    ),
    "podcast_clean": (
        highpass(75.0, stages=2),
        noise_gate(threshold_db=-52.0, attack_ms=3.0, release_ms=120.0, floor_db=-85.0),
        expander(threshold_db=-38.0, ratio=1.8, attack_ms=6.0, release_ms=90.0),
        deesser(frequency_hz=6_000.0, threshold_db=-32.0, ratio=3.5, amount=0.7),
        compressor(threshold_db=-19.0, ratio=2.6, attack_ms=10.0, release_ms=110.0, makeup_db=2.0),
        limiter(ceiling_db=-1.0),
    ),
    "lofi": (
        highpass(120.0),
        lowpass(4_600.0, stages=2),
        peak_eq(1_800.0, 1.5, q=1.4),
        distortion(1.55),
        room_reverb(decay_seconds=0.7, mix=0.1, tone_hz=5_000.0),
        compressor(threshold_db=-24.0, ratio=2.2, makeup_db=1.0),
    ),
    "wide_chorus": (
        chorus(rate_hz=0.55, depth_ms=9.0, delay_ms=20.0, mix=0.42, feedback=0.08),
        stereo_width(1.4),
        slapback(delay_ms=85.0, mix=0.12),
    ),
    "clarity_eq": tuple(
        parametric_eq(
            {"kind": "low_shelf", "frequency_hz": 120.0, "gain_db": 1.5},
            {"kind": "peak", "frequency_hz": 450.0, "gain_db": -1.5, "q": 1.1},
            {"kind": "peak", "frequency_hz": 2_800.0, "gain_db": 2.5, "q": 0.9},
            {"kind": "high_shelf", "frequency_hz": 10_500.0, "gain_db": 1.5},
        )
    ),
}


def preset_names() -> tuple[str, ...]:
    return tuple(sorted(PRESETS))


def get_preset(name: str) -> list[Effect]:
    key = name.strip().lower()
    if key not in PRESETS:
        available = ", ".join(preset_names())
        raise KeyError(f"Unknown preset {name!r}. Available presets: {available}")
    return list(resolve_effects(PRESETS[key]))


def resolve_effects(items: Any) -> list[Effect]:
    resolved: list[Effect] = []
    for item in flatten_effects((items,)):
        if isinstance(item, Effect):
            resolved.append(item)
        elif isinstance(item, str):
            resolved.extend(get_preset(item))
        else:
            raise TypeError(
                "Effects must be Effect instances, preset names, or flat/nested sequences of those values."
            )
    return resolved

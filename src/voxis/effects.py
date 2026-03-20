from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True, slots=True)
class Automation:
    fn: Callable[[float], float]
    label: str | None = None

    def evaluate(self, time_seconds: float) -> float:
        return float(self.fn(float(time_seconds)))

    def describe(self) -> str:
        if self.label:
            return self.label
        name = getattr(self.fn, "__name__", None)
        return name if name and name != "<lambda>" else "automation"


def automation(fn: Callable[[float], float], *, label: str | None = None) -> Automation:
    return Automation(fn=fn, label=label)


def _normalize_param(value: Any) -> Any:
    if isinstance(value, Automation):
        return value
    if callable(value):
        return automation(value)
    if isinstance(value, list):
        return [_normalize_param(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_normalize_param(item) for item in value)
    return value


def _contains_dynamic(value: Any) -> bool:
    if isinstance(value, Automation):
        return True
    if isinstance(value, dict):
        return any(_contains_dynamic(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_dynamic(item) for item in value)
    return False


def _signature_value(value: Any) -> str:
    if isinstance(value, Automation):
        return f"automation:{value.describe()}:{id(value.fn)}"
    if isinstance(value, np.ndarray):
        return f"ndarray:{value.shape}:{value.dtype}:{id(value)}"
    if isinstance(value, Path):
        return f"path:{value.as_posix()}"
    if isinstance(value, dict):
        parts = ",".join(f"{key}={_signature_value(val)}" for key, val in sorted(value.items()))
        return "{" + parts + "}"
    if isinstance(value, (list, tuple)):
        parts = ",".join(_signature_value(item) for item in value)
        return "[" + parts + "]"
    return repr(value)


def _format_param(name: str, value: Any) -> str:
    if isinstance(value, Automation):
        return f"{name}=<{value.describe()}>"
    if isinstance(value, float):
        if name.endswith("_hz"):
            return f"{name}={value:.2f}Hz"
        if name.endswith("_ms"):
            return f"{name}={value:.2f}ms"
        if name.endswith("_db"):
            return f"{name}={value:.2f}dB"
        return f"{name}={value:.3f}".rstrip("0").rstrip(".")
    if isinstance(value, np.ndarray):
        return f"{name}=ndarray{value.shape}"
    if isinstance(value, (list, tuple)):
        return f"{name}=[{', '.join(_format_param('', item).lstrip('=') for item in value)}]"
    return f"{name}={value}"


@dataclass(frozen=True, slots=True)
class Effect:
    type: str
    params: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = {key: _normalize_param(value) for key, value in self.params.items()}
        object.__setattr__(self, "params", normalized)

    @property
    def display_name(self) -> str:
        display_name = self.params.get("_display_name")
        return str(display_name) if display_name else self.type

    def has_dynamic_params(self) -> bool:
        return any(_contains_dynamic(value) for value in self.params.values())

    def to_spec(self) -> dict[str, Any]:
        if self.has_dynamic_params():
            raise TypeError(f"Effect {self.display_name!r} contains dynamic parameters and cannot use the native path.")
        spec = {"type": self.type}
        for key, value in self.params.items():
            if key.startswith("_"):
                continue
            spec[key] = value
        return spec

    def describe(self) -> str:
        visible_params = [
            _format_param(key, value)
            for key, value in self.params.items()
            if not key.startswith("_")
        ]
        if not visible_params:
            return f"{self.display_name}()"
        return f"{self.display_name}({', '.join(visible_params)})"

    def signature(self) -> str:
        visible_params = {
            key: value
            for key, value in self.params.items()
            if not key.startswith("_")
        }
        return f"{self.type}:{_signature_value(visible_params)}"


@dataclass(frozen=True, slots=True)
class EQBand:
    kind: str
    frequency_hz: float
    gain_db: float = 0.0
    q: float = 0.70710678
    slope: float = 1.0
    stages: int = 1


def gain(db: float) -> Effect:
    return Effect("gain", {"db": float(db)})


def clip(threshold: float = 0.98) -> Effect:
    return Effect("clip", {"threshold": float(threshold)})


def lowpass(
    frequency_hz: float,
    q: float = 0.70710678,
    stages: int = 1,
) -> Effect:
    return Effect(
        "lowpass",
        {
            "frequency_hz": frequency_hz,
            "q": q,
            "stages": int(stages),
        },
    )


def highpass(
    frequency_hz: float,
    q: float = 0.70710678,
    stages: int = 1,
) -> Effect:
    return Effect(
        "highpass",
        {
            "frequency_hz": frequency_hz,
            "q": q,
            "stages": int(stages),
        },
    )


def bandpass(
    frequency_hz: float,
    q: float = 0.70710678,
    stages: int = 1,
) -> Effect:
    return Effect(
        "bandpass",
        {
            "frequency_hz": frequency_hz,
            "q": q,
            "stages": int(stages),
        },
    )


def notch(
    frequency_hz: float,
    q: float = 0.70710678,
    stages: int = 1,
) -> Effect:
    return Effect(
        "notch",
        {
            "frequency_hz": frequency_hz,
            "q": q,
            "stages": int(stages),
        },
    )


def peak_eq(
    frequency_hz: float,
    gain_db: float,
    q: float = 1.0,
    stages: int = 1,
) -> Effect:
    return Effect(
        "peak_eq",
        {
            "frequency_hz": frequency_hz,
            "gain_db": gain_db,
            "q": q,
            "stages": int(stages),
        },
    )


def low_shelf(
    frequency_hz: float,
    gain_db: float,
    slope: float = 1.0,
    stages: int = 1,
) -> Effect:
    return Effect(
        "low_shelf",
        {
            "frequency_hz": frequency_hz,
            "gain_db": gain_db,
            "slope": slope,
            "stages": int(stages),
        },
    )


def high_shelf(
    frequency_hz: float,
    gain_db: float,
    slope: float = 1.0,
    stages: int = 1,
) -> Effect:
    return Effect(
        "high_shelf",
        {
            "frequency_hz": frequency_hz,
            "gain_db": gain_db,
            "slope": slope,
            "stages": int(stages),
        },
    )


def graphic_eq(
    bands: dict[float, float] | list[tuple[float, float]] | tuple[tuple[float, float], ...],
    *,
    q: float = 1.1,
) -> list[Effect]:
    items = sorted(dict(bands).items()) if isinstance(bands, dict) else sorted((float(freq), float(gain)) for freq, gain in bands)
    if not items:
        return []

    effects: list[Effect] = []
    for index, (frequency_hz, gain_db) in enumerate(items):
        if index == 0:
            effects.append(
                Effect(
                    "low_shelf",
                    {
                        "frequency_hz": frequency_hz,
                        "gain_db": gain_db,
                        "slope": 1.0,
                        "stages": 1,
                        "_display_name": "graphic_eq",
                    },
                )
            )
        elif index == len(items) - 1:
            effects.append(
                Effect(
                    "high_shelf",
                    {
                        "frequency_hz": frequency_hz,
                        "gain_db": gain_db,
                        "slope": 1.0,
                        "stages": 1,
                        "_display_name": "graphic_eq",
                    },
                )
            )
        else:
            effects.append(
                Effect(
                    "peak_eq",
                    {
                        "frequency_hz": frequency_hz,
                        "gain_db": gain_db,
                        "q": q,
                        "stages": 1,
                        "_display_name": "graphic_eq",
                    },
                )
            )
    return effects


def resonant_filter(
    frequency_hz: float,
    *,
    resonance: float = 1.6,
    mode: str = "lowpass",
    stages: int = 1,
) -> Effect:
    normalized_mode = mode.lower()
    params = {
        "frequency_hz": float(frequency_hz),
        "q": float(max(resonance, 0.1)),
        "stages": int(stages),
        "_display_name": "resonant_filter",
    }
    if normalized_mode == "highpass":
        return Effect("highpass", params)
    if normalized_mode == "bandpass":
        return Effect("bandpass", params)
    return Effect("lowpass", params)


def dynamic_eq(
    frequency_hz: float,
    *,
    threshold_db: float = -24.0,
    cut_db: float = -6.0,
    q: float = 1.2,
    attack_ms: float = 10.0,
    release_ms: float = 120.0,
) -> Effect:
    return Effect(
        "dynamic_eq",
        {
            "frequency_hz": frequency_hz,
            "threshold_db": threshold_db,
            "cut_db": cut_db,
            "q": q,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
        },
    )


def formant_filter(
    morph: float = 0.0,
    *,
    intensity: float = 1.0,
    q: float = 4.0,
) -> list[Effect]:
    vowels = [
        ((800.0, 1150.0, 2900.0), "a"),
        ((400.0, 1700.0, 2600.0), "e"),
        ((350.0, 2000.0, 2800.0), "i"),
        ((450.0, 800.0, 2830.0), "o"),
        ((325.0, 700.0, 2530.0), "u"),
    ]
    clamped = float(np.clip(morph, 0.0, len(vowels) - 1))
    low_index = int(np.floor(clamped))
    high_index = min(len(vowels) - 1, low_index + 1)
    blend = clamped - low_index
    low_formants, _ = vowels[low_index]
    high_formants, _ = vowels[high_index]
    gains = [6.0 * intensity, 4.5 * intensity, 3.5 * intensity]

    effects: list[Effect] = []
    for band_index, gain_db in enumerate(gains):
        frequency_hz = (1.0 - blend) * low_formants[band_index] + blend * high_formants[band_index]
        effects.append(
            Effect(
                "peak_eq",
                {
                    "frequency_hz": frequency_hz,
                    "gain_db": gain_db,
                    "q": q,
                    "stages": 1,
                    "_display_name": "formant_filter",
                },
            )
        )
    return effects


def delay(delay_ms: float | Automation | Callable[[float], float], feedback: float = 0.35, mix: float = 0.2) -> Effect:
    return Effect(
        "delay",
        {
            "delay_ms": delay_ms,
            "feedback": feedback,
            "mix": mix,
        },
    )


def feedback_delay(
    delay_ms: float | Automation | Callable[[float], float],
    feedback: float = 0.6,
    mix: float = 0.35,
) -> Effect:
    return Effect(
        "delay",
        {
            "delay_ms": delay_ms,
            "feedback": feedback,
            "mix": mix,
            "_display_name": "feedback_delay",
        },
    )


def echo(
    delay_ms: float | Automation | Callable[[float], float] = 320.0,
    feedback: float = 0.38,
    mix: float = 0.28,
) -> Effect:
    return Effect(
        "delay",
        {
            "delay_ms": delay_ms,
            "feedback": feedback,
            "mix": mix,
            "_display_name": "echo",
        },
    )


def slapback(delay_ms: float | Automation | Callable[[float], float] = 95.0, mix: float = 0.24) -> Effect:
    return Effect(
        "delay",
        {
            "delay_ms": delay_ms,
            "feedback": 0.12,
            "mix": mix,
            "_display_name": "slapback",
        },
    )


def ping_pong_delay(
    delay_ms: float | Automation | Callable[[float], float],
    feedback: float = 0.55,
    mix: float = 0.3,
) -> Effect:
    return Effect(
        "ping_pong_delay",
        {
            "delay_ms": delay_ms,
            "feedback": feedback,
            "mix": mix,
        },
    )


def multi_tap_delay(
    delay_ms: float = 120.0,
    taps: int = 4,
    spacing_ms: float = 65.0,
    decay: float = 0.6,
    mix: float = 0.32,
) -> Effect:
    return Effect(
        "multi_tap_delay",
        {
            "delay_ms": delay_ms,
            "taps": int(taps),
            "spacing_ms": spacing_ms,
            "decay": decay,
            "mix": mix,
        },
    )


def tremolo(rate_hz: float | Automation | Callable[[float], float], depth: float = 0.5) -> Effect:
    return Effect("tremolo", {"rate_hz": rate_hz, "depth": depth})


def chorus(
    rate_hz: float = 0.9,
    depth_ms: float = 7.5,
    delay_ms: float = 18.0,
    mix: float = 0.35,
    feedback: float = 0.12,
) -> Effect:
    return Effect(
        "chorus",
        {
            "rate_hz": rate_hz,
            "depth_ms": depth_ms,
            "delay_ms": delay_ms,
            "mix": mix,
            "feedback": feedback,
        },
    )


def flanger(
    rate_hz: float = 0.25,
    depth_ms: float = 1.8,
    delay_ms: float = 2.5,
    mix: float = 0.45,
    feedback: float = 0.35,
) -> Effect:
    return Effect(
        "flanger",
        {
            "rate_hz": rate_hz,
            "depth_ms": depth_ms,
            "delay_ms": delay_ms,
            "mix": mix,
            "feedback": feedback,
        },
    )


def vibrato(
    rate_hz: float = 5.0,
    depth_ms: float = 3.5,
    delay_ms: float = 5.5,
) -> Effect:
    return Effect(
        "vibrato",
        {
            "rate_hz": rate_hz,
            "depth_ms": depth_ms,
            "delay_ms": delay_ms,
            "mix": 1.0,
            "feedback": 0.0,
        },
    )


def auto_pan(rate_hz: float = 0.35, depth: float = 1.0) -> Effect:
    return Effect("auto_pan", {"rate_hz": rate_hz, "depth": depth})


def rotary_speaker(
    rate_hz: float = 0.8,
    depth: float = 0.7,
    mix: float = 0.65,
    crossover_hz: float = 900.0,
) -> Effect:
    return Effect(
        "rotary_speaker",
        {
            "rate_hz": rate_hz,
            "depth": depth,
            "mix": mix,
            "crossover_hz": crossover_hz,
        },
    )


def ring_modulation(
    frequency_hz: float = 30.0,
    mix: float = 0.5,
) -> Effect:
    return Effect(
        "ring_modulation",
        {
            "frequency_hz": frequency_hz,
            "mix": mix,
        },
    )


def frequency_shifter(
    shift_hz: float = 120.0,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "frequency_shifter",
        {
            "shift_hz": shift_hz,
            "mix": mix,
        },
    )


def phaser(
    rate_hz: float = 0.35,
    depth: float = 0.75,
    center_hz: float = 900.0,
    feedback: float = 0.2,
    mix: float = 0.5,
    stages: int = 4,
) -> Effect:
    return Effect(
        "phaser",
        {
            "rate_hz": rate_hz,
            "depth": depth,
            "center_hz": center_hz,
            "feedback": feedback,
            "mix": mix,
            "stages": int(stages),
        },
    )


def distortion(drive: float = 2.0) -> Effect:
    return Effect("distortion", {"drive": drive})


def overdrive(
    drive: float = 1.8,
    *,
    tone: float = 0.55,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "overdrive",
        {
            "drive": drive,
            "tone": tone,
            "mix": mix,
        },
    )


def fuzz(
    drive: float = 3.6,
    *,
    bias: float = 0.12,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "fuzz",
        {
            "drive": drive,
            "bias": bias,
            "mix": mix,
        },
    )


def bitcrusher(
    bit_depth: int = 8,
    *,
    sample_rate_reduction: int = 4,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "bitcrusher",
        {
            "bit_depth": int(bit_depth),
            "sample_rate_reduction": int(sample_rate_reduction),
            "mix": mix,
        },
    )


def waveshaper(
    amount: float = 1.4,
    *,
    symmetry: float = 0.0,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "waveshaper",
        {
            "amount": amount,
            "symmetry": symmetry,
            "mix": mix,
        },
    )


def tube_saturation(
    drive: float = 1.6,
    *,
    bias: float = 0.08,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "tube_saturation",
        {
            "drive": drive,
            "bias": bias,
            "mix": mix,
        },
    )


def tape_saturation(
    drive: float = 1.4,
    *,
    softness: float = 0.35,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "tape_saturation",
        {
            "drive": drive,
            "softness": softness,
            "mix": mix,
        },
    )


def soft_clipping(threshold: float = 0.85) -> Effect:
    return Effect("soft_clipping", {"threshold": threshold})


def hard_clipping(threshold: float = 0.92) -> Effect:
    return Effect(
        "clip",
        {
            "threshold": threshold,
            "_display_name": "hard_clipping",
        },
    )


def pitch_shift(
    semitones: float,
    *,
    fft_size: int = 1536,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "pitch_shift",
        {
            "semitones": semitones,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def time_stretch(
    rate: float = 0.9,
    *,
    fft_size: int = 1536,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "time_stretch",
        {
            "rate": rate,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def time_compression(
    rate: float = 1.15,
    *,
    fft_size: int = 1536,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "time_stretch",
        {
            "rate": rate,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
            "_display_name": "time_compression",
        },
    )


def auto_tune(
    *,
    strength: float = 0.7,
    key: str = "C",
    scale: str = "chromatic",
    min_hz: float = 80.0,
    max_hz: float = 1_000.0,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "auto_tune",
        {
            "strength": strength,
            "key": key,
            "scale": scale,
            "min_hz": min_hz,
            "max_hz": max_hz,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def harmonizer(
    intervals_semitones: Iterable[float] | float = (7.0,),
    *,
    mix: float = 0.35,
    fft_size: int = 1536,
    hop_size: int = 512,
) -> Effect:
    if isinstance(intervals_semitones, (int, float)):
        intervals = (float(intervals_semitones),)
    else:
        intervals = tuple(float(value) for value in intervals_semitones)
    return Effect(
        "harmonizer",
        {
            "intervals_semitones": intervals,
            "mix": mix,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def octaver(
    *,
    octaves_down: int = 1,
    octaves_up: int = 0,
    down_mix: float = 0.45,
    up_mix: float = 0.0,
    fft_size: int = 1536,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "octaver",
        {
            "octaves_down": int(octaves_down),
            "octaves_up": int(octaves_up),
            "down_mix": down_mix,
            "up_mix": up_mix,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def formant_shifting(
    shift: float = 1.12,
    *,
    mix: float = 1.0,
    fft_size: int = 1536,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "formant_shifting",
        {
            "shift": shift,
            "mix": mix,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def noise_reduction(
    *,
    strength: float = 0.5,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "noise_reduction",
        {
            "strength": strength,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def voice_isolation(
    *,
    strength: float = 0.75,
    low_hz: float = 120.0,
    high_hz: float = 5_200.0,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "voice_isolation",
        {
            "strength": strength,
            "low_hz": low_hz,
            "high_hz": high_hz,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def source_separation(
    *,
    target: str = "vocals",
    strength: float = 0.8,
    low_hz: float = 120.0,
    high_hz: float = 5_200.0,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "source_separation",
        {
            "target": target,
            "strength": strength,
            "low_hz": low_hz,
            "high_hz": high_hz,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def de_reverb(
    *,
    amount: float = 0.45,
    tail_ms: float = 240.0,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "de_reverb",
        {
            "amount": amount,
            "tail_ms": tail_ms,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def de_echo(
    *,
    amount: float = 0.45,
    min_delay_ms: float = 60.0,
    max_delay_ms: float = 800.0,
) -> Effect:
    return Effect(
        "de_echo",
        {
            "amount": amount,
            "min_delay_ms": min_delay_ms,
            "max_delay_ms": max_delay_ms,
        },
    )


def spectral_repair(
    *,
    strength: float = 0.35,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "spectral_repair",
        {
            "strength": strength,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def ai_enhancer(
    *,
    amount: float = 0.6,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "ai_enhancer",
        {
            "amount": amount,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def speech_enhancement(
    *,
    amount: float = 0.7,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "speech_enhancement",
        {
            "amount": amount,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def glitch_effect(
    *,
    slice_ms: float = 70.0,
    repeat_probability: float = 0.22,
    dropout_probability: float = 0.12,
    reverse_probability: float = 0.10,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "glitch_effect",
        {
            "slice_ms": slice_ms,
            "repeat_probability": repeat_probability,
            "dropout_probability": dropout_probability,
            "reverse_probability": reverse_probability,
            "mix": mix,
        },
    )


def stutter(
    *,
    slice_ms: float = 90.0,
    repeats: int = 3,
    interval_ms: float = 480.0,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "stutter",
        {
            "slice_ms": slice_ms,
            "repeats": int(repeats),
            "interval_ms": interval_ms,
            "mix": mix,
        },
    )


def tape_stop(
    *,
    stop_time_ms: float = 900.0,
    curve: float = 2.0,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "tape_stop",
        {
            "stop_time_ms": stop_time_ms,
            "curve": curve,
            "mix": mix,
        },
    )


def reverse_reverb(
    *,
    decay_seconds: float = 1.2,
    mix: float = 0.45,
) -> Effect:
    return Effect(
        "reverse_reverb",
        {
            "decay_seconds": decay_seconds,
            "mix": mix,
        },
    )


def granular_synthesis(
    *,
    grain_ms: float = 80.0,
    overlap: float = 0.5,
    jitter_ms: float = 25.0,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "granular_synthesis",
        {
            "grain_ms": grain_ms,
            "overlap": overlap,
            "jitter_ms": jitter_ms,
            "mix": mix,
        },
    )


def time_slicing(
    *,
    slice_ms: float = 120.0,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "time_slicing",
        {
            "slice_ms": slice_ms,
            "mix": mix,
        },
    )


def random_pitch_mod(
    *,
    depth_semitones: float = 2.0,
    segment_ms: float = 180.0,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "random_pitch_mod",
        {
            "depth_semitones": depth_semitones,
            "segment_ms": segment_ms,
            "mix": mix,
        },
    )


def vinyl_effect(
    *,
    noise: float = 0.08,
    wow: float = 0.15,
    crackle: float = 0.12,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "vinyl_effect",
        {
            "noise": noise,
            "wow": wow,
            "crackle": crackle,
            "mix": mix,
        },
    )


def radio_effect(
    *,
    noise_level: float = 0.04,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "radio_effect",
        {
            "noise_level": noise_level,
            "mix": mix,
        },
    )


def telephone_effect(
    *,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "telephone_effect",
        {
            "mix": mix,
        },
    )


def retro_8bit(
    *,
    bit_depth: int = 6,
    sample_rate_reduction: int = 8,
    mix: float = 1.0,
) -> Effect:
    return Effect(
        "retro_8bit",
        {
            "bit_depth": int(bit_depth),
            "sample_rate_reduction": int(sample_rate_reduction),
            "mix": mix,
        },
    )


def slow_motion_extreme(
    *,
    rate: float = 0.45,
    tone_hz: float = 4_800.0,
) -> Effect:
    return Effect(
        "slow_motion_extreme",
        {
            "rate": rate,
            "tone_hz": tone_hz,
        },
    )


def robot_voice(
    *,
    carrier_hz: float = 70.0,
    mix: float = 0.85,
) -> Effect:
    return Effect(
        "robot_voice",
        {
            "carrier_hz": carrier_hz,
            "mix": mix,
        },
    )


def alien_voice(
    *,
    shift_semitones: float = 5.0,
    formant_shift: float = 1.18,
    mix: float = 0.8,
) -> Effect:
    return Effect(
        "alien_voice",
        {
            "shift_semitones": shift_semitones,
            "formant_shift": formant_shift,
            "mix": mix,
        },
    )


def fft_filter(
    *,
    low_hz: float = 80.0,
    high_hz: float = 12_000.0,
    mix: float = 1.0,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "fft_filter",
        {
            "low_hz": low_hz,
            "high_hz": high_hz,
            "mix": mix,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def spectral_gating(
    *,
    threshold_db: float = -42.0,
    floor: float = 0.08,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "spectral_gating",
        {
            "threshold_db": threshold_db,
            "floor": floor,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def spectral_blur(
    *,
    amount: float = 0.45,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "spectral_blur",
        {
            "amount": amount,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def spectral_freeze(
    *,
    start_ms: float = 120.0,
    mix: float = 0.7,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "spectral_freeze",
        {
            "start_ms": start_ms,
            "mix": mix,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def spectral_morphing(
    *,
    amount: float = 0.5,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "spectral_morphing",
        {
            "amount": amount,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def phase_vocoder(
    *,
    rate: float = 0.85,
    fft_size: int = 1536,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "phase_vocoder",
        {
            "rate": rate,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def harmonic_percussive_separation(
    *,
    target: str = "harmonic",
    mix: float = 1.0,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "harmonic_percussive_separation",
        {
            "target": target,
            "mix": mix,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def spectral_delay(
    *,
    max_delay_ms: float = 240.0,
    feedback: float = 0.15,
    mix: float = 0.35,
    fft_size: int = 1024,
    hop_size: int = 512,
) -> Effect:
    return Effect(
        "spectral_delay",
        {
            "max_delay_ms": max_delay_ms,
            "feedback": feedback,
            "mix": mix,
            "fft_size": int(fft_size),
            "hop_size": int(hop_size),
        },
    )


def compressor(
    threshold_db: float = -18.0,
    ratio: float = 4.0,
    attack_ms: float = 10.0,
    release_ms: float = 80.0,
    makeup_db: float = 0.0,
) -> Effect:
    return Effect(
        "compressor",
        {
            "threshold_db": threshold_db,
            "ratio": ratio,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
            "makeup_db": makeup_db,
        },
    )


def downward_compression(
    threshold_db: float = -18.0,
    ratio: float = 4.0,
    attack_ms: float = 10.0,
    release_ms: float = 80.0,
    makeup_db: float = 0.0,
) -> Effect:
    return Effect(
        "compressor",
        {
            "threshold_db": threshold_db,
            "ratio": ratio,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
            "makeup_db": makeup_db,
            "_display_name": "downward_compression",
        },
    )


def upward_compression(
    threshold_db: float = -42.0,
    ratio: float = 2.0,
    attack_ms: float = 12.0,
    release_ms: float = 120.0,
    max_gain_db: float = 18.0,
) -> Effect:
    return Effect(
        "upward_compression",
        {
            "threshold_db": threshold_db,
            "ratio": ratio,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
            "max_gain_db": max_gain_db,
        },
    )


def limiter(
    ceiling_db: float = -1.0,
    attack_ms: float = 1.0,
    release_ms: float = 60.0,
) -> Effect:
    return Effect(
        "limiter",
        {
            "ceiling_db": ceiling_db,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
        },
    )


def transient_shaper(
    attack: float = 0.7,
    sustain: float = 0.2,
    attack_ms: float = 18.0,
    release_ms: float = 120.0,
) -> Effect:
    return Effect(
        "transient_shaper",
        {
            "attack": attack,
            "sustain": sustain,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
        },
    )


def expander(
    threshold_db: float = -35.0,
    ratio: float = 2.0,
    attack_ms: float = 8.0,
    release_ms: float = 80.0,
    makeup_db: float = 0.0,
) -> Effect:
    return Effect(
        "expander",
        {
            "threshold_db": threshold_db,
            "ratio": ratio,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
            "makeup_db": makeup_db,
        },
    )


def noise_gate(
    threshold_db: float = -45.0,
    attack_ms: float = 3.0,
    release_ms: float = 60.0,
    floor_db: float = -80.0,
) -> Effect:
    return Effect(
        "noise_gate",
        {
            "threshold_db": threshold_db,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
            "floor_db": floor_db,
        },
    )


def deesser(
    frequency_hz: float = 6_500.0,
    threshold_db: float = -28.0,
    ratio: float = 4.0,
    attack_ms: float = 2.0,
    release_ms: float = 60.0,
    amount: float = 1.0,
) -> Effect:
    return Effect(
        "deesser",
        {
            "frequency_hz": frequency_hz,
            "threshold_db": threshold_db,
            "ratio": ratio,
            "attack_ms": attack_ms,
            "release_ms": release_ms,
            "amount": amount,
        },
    )


def early_reflections(
    pre_delay_ms: float = 12.0,
    spread_ms: float = 8.0,
    taps: int = 6,
    decay: float = 0.7,
    mix: float = 0.22,
) -> Effect:
    return Effect(
        "early_reflections",
        {
            "pre_delay_ms": pre_delay_ms,
            "spread_ms": spread_ms,
            "taps": int(taps),
            "decay": decay,
            "mix": mix,
        },
    )


def room_reverb(decay_seconds: float = 0.8, mix: float = 0.22, tone_hz: float = 8_000.0) -> Effect:
    return Effect(
        "room_reverb",
        {
            "decay_seconds": decay_seconds,
            "mix": mix,
            "tone_hz": tone_hz,
        },
    )


def hall_reverb(decay_seconds: float = 1.8, mix: float = 0.28, tone_hz: float = 7_200.0) -> Effect:
    return Effect(
        "hall_reverb",
        {
            "decay_seconds": decay_seconds,
            "mix": mix,
            "tone_hz": tone_hz,
        },
    )


def plate_reverb(decay_seconds: float = 1.2, mix: float = 0.24, tone_hz: float = 9_500.0) -> Effect:
    return Effect(
        "plate_reverb",
        {
            "decay_seconds": decay_seconds,
            "mix": mix,
            "tone_hz": tone_hz,
        },
    )


def convolution_reverb(
    impulse_response: str | Path | np.ndarray | list[float] | list[list[float]],
    mix: float = 0.28,
    normalize_ir: bool = True,
) -> Effect:
    return Effect(
        "convolution_reverb",
        {
            "impulse_response": impulse_response,
            "mix": mix,
            "normalize_ir": bool(normalize_ir),
        },
    )


def pan(position: float) -> Effect:
    return Effect("pan", {"position": position})


def stereo_width(width: float = 1.0) -> Effect:
    return Effect("stereo_width", {"width": width})


def stereo_widening(amount: float = 1.25) -> Effect:
    return Effect("stereo_widening", {"amount": amount})


def mid_side_processing(
    *,
    mid_gain_db: float = 0.0,
    side_gain_db: float = 0.0,
) -> Effect:
    return Effect(
        "mid_side_processing",
        {
            "mid_gain_db": mid_gain_db,
            "side_gain_db": side_gain_db,
        },
    )


def stereo_imager(
    *,
    low_width: float = 0.9,
    high_width: float = 1.35,
    crossover_hz: float = 280.0,
) -> Effect:
    return Effect(
        "stereo_imager",
        {
            "low_width": low_width,
            "high_width": high_width,
            "crossover_hz": crossover_hz,
        },
    )


def binaural_effect(
    *,
    azimuth_deg: float = 25.0,
    distance: float = 1.0,
    room_mix: float = 0.08,
) -> Effect:
    return Effect(
        "binaural_effect",
        {
            "azimuth_deg": azimuth_deg,
            "distance": distance,
            "room_mix": room_mix,
        },
    )


def spatial_positioning(
    *,
    azimuth_deg: float = 25.0,
    elevation_deg: float = 0.0,
    distance: float = 1.0,
) -> Effect:
    return Effect(
        "spatial_positioning",
        {
            "azimuth_deg": azimuth_deg,
            "elevation_deg": elevation_deg,
            "distance": distance,
        },
    )


def hrtf_simulation(
    *,
    azimuth_deg: float = 30.0,
    elevation_deg: float = 0.0,
    distance: float = 1.0,
) -> Effect:
    return Effect(
        "hrtf_simulation",
        {
            "azimuth_deg": azimuth_deg,
            "elevation_deg": elevation_deg,
            "distance": distance,
        },
    )


def eq_band(
    kind: str,
    frequency_hz: float,
    *,
    gain_db: float = 0.0,
    q: float = 0.70710678,
    slope: float = 1.0,
    stages: int = 1,
) -> EQBand:
    return EQBand(
        kind=kind,
        frequency_hz=float(frequency_hz),
        gain_db=float(gain_db),
        q=float(q),
        slope=float(slope),
        stages=int(stages),
    )


def parametric_eq(*bands: EQBand | dict[str, Any]) -> list[Effect]:
    effects: list[Effect] = []
    for band in bands:
        normalized = band if isinstance(band, EQBand) else EQBand(**band)
        kind = normalized.kind.lower()

        if kind == "peak":
            effects.append(
                peak_eq(
                    normalized.frequency_hz,
                    normalized.gain_db,
                    q=normalized.q,
                    stages=normalized.stages,
                )
            )
        elif kind == "low_shelf":
            effects.append(
                low_shelf(
                    normalized.frequency_hz,
                    normalized.gain_db,
                    slope=normalized.slope,
                    stages=normalized.stages,
                )
            )
        elif kind == "high_shelf":
            effects.append(
                high_shelf(
                    normalized.frequency_hz,
                    normalized.gain_db,
                    slope=normalized.slope,
                    stages=normalized.stages,
                )
            )
        elif kind == "lowpass":
            effects.append(
                lowpass(
                    normalized.frequency_hz,
                    q=normalized.q,
                    stages=normalized.stages,
                )
            )
        elif kind == "highpass":
            effects.append(
                highpass(
                    normalized.frequency_hz,
                    q=normalized.q,
                    stages=normalized.stages,
                )
            )
        elif kind == "bandpass":
            effects.append(
                bandpass(
                    normalized.frequency_hz,
                    q=normalized.q,
                    stages=normalized.stages,
                )
            )
        elif kind == "notch":
            effects.append(
                notch(
                    normalized.frequency_hz,
                    q=normalized.q,
                    stages=normalized.stages,
                )
            )
        else:
            raise ValueError(f"Unsupported EQ band kind: {normalized.kind!r}")

    return effects


def effect_names() -> tuple[str, ...]:
    return (
        "gain",
        "clip",
        "lowpass",
        "highpass",
        "bandpass",
        "notch",
        "peak_eq",
        "low_shelf",
        "high_shelf",
        "graphic_eq",
        "resonant_filter",
        "dynamic_eq",
        "formant_filter",
        "delay",
        "feedback_delay",
        "echo",
        "ping_pong_delay",
        "multi_tap_delay",
        "slapback",
        "early_reflections",
        "room_reverb",
        "hall_reverb",
        "plate_reverb",
        "convolution_reverb",
        "chorus",
        "flanger",
        "phaser",
        "tremolo",
        "vibrato",
        "auto_pan",
        "rotary_speaker",
        "ring_modulation",
        "frequency_shifter",
        "distortion",
        "overdrive",
        "fuzz",
        "bitcrusher",
        "waveshaper",
        "tube_saturation",
        "tape_saturation",
        "soft_clipping",
        "hard_clipping",
        "pitch_shift",
        "time_stretch",
        "time_compression",
        "auto_tune",
        "harmonizer",
        "octaver",
        "formant_shifting",
        "noise_reduction",
        "voice_isolation",
        "source_separation",
        "de_reverb",
        "de_echo",
        "spectral_repair",
        "ai_enhancer",
        "speech_enhancement",
        "glitch_effect",
        "stutter",
        "tape_stop",
        "reverse_reverb",
        "granular_synthesis",
        "time_slicing",
        "random_pitch_mod",
        "vinyl_effect",
        "radio_effect",
        "telephone_effect",
        "retro_8bit",
        "slow_motion_extreme",
        "robot_voice",
        "alien_voice",
        "fft_filter",
        "spectral_gating",
        "spectral_blur",
        "spectral_freeze",
        "spectral_morphing",
        "phase_vocoder",
        "harmonic_percussive_separation",
        "spectral_delay",
        "compressor",
        "downward_compression",
        "upward_compression",
        "limiter",
        "expander",
        "noise_gate",
        "deesser",
        "transient_shaper",
        "pan",
        "stereo_width",
        "stereo_widening",
        "mid_side_processing",
        "stereo_imager",
        "binaural_effect",
        "spatial_positioning",
        "hrtf_simulation",
    )


def is_effect_sequence(value: Any) -> bool:
    return isinstance(value, Iterable) and not isinstance(value, (str, bytes, Effect))

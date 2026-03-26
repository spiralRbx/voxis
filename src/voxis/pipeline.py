from __future__ import annotations

from typing import Any

from ._python_dsp import requires_python_processing, process_python_effect
from ._util import ensure_float32_frames
from .effects import Effect
from .presets import resolve_effects

try:
    from ._voxis_core import process_pipeline as _process_pipeline
except ImportError as exc:  # pragma: no cover
    _IMPORT_ERROR = exc
    _process_pipeline = None
else:
    _IMPORT_ERROR = None

_NATIVE_EFFECT_TYPES = {
    "gain",
    "clip",
    "lowpass",
    "highpass",
    "bandpass",
    "notch",
    "peak_eq",
    "low_shelf",
    "high_shelf",
    "delay",
    "ping_pong_delay",
    "tremolo",
    "chorus",
    "flanger",
    "phaser",
    "vibrato",
    "auto_pan",
    "dynamic_eq",
    "rotary_speaker",
    "distortion",
    "compressor",
    "upward_compression",
    "limiter",
    "expander",
    "noise_gate",
    "deesser",
    "transient_shaper",
    "pan",
    "stereo_width",
}


class Pipeline:
    def __init__(
        self,
        sample_rate: int,
        channels: int | None = None,
        block_size: int = 2048,
        workers: int = 1,
    ) -> None:
        self.sample_rate = int(sample_rate)
        self.channels = None if channels is None else int(channels)
        self.block_size = int(block_size)
        self.workers = int(workers)
        self._effects: list[Effect] = []

    @property
    def effects(self) -> tuple[Effect, ...]:
        return tuple(self._effects)

    def add(self, effect: Any) -> "Pipeline":
        self._effects.extend(resolve_effects(effect))
        return self

    def extend(self, effects: Any) -> "Pipeline":
        self._effects.extend(resolve_effects(effects))
        return self

    def clone(self) -> "Pipeline":
        cloned = Pipeline(
            sample_rate=self.sample_rate,
            channels=self.channels,
            block_size=self.block_size,
            workers=self.workers,
        )
        cloned._effects.extend(self._effects)
        return cloned

    def __rshift__(self, effects: Any) -> "Pipeline":
        cloned = self.clone()
        cloned.extend(effects)
        return cloned

    def __irshift__(self, effects: Any) -> "Pipeline":
        return self.extend(effects)

    def signature(self) -> str:
        return "|".join(effect.signature() for effect in self._effects)

    def pipeline_info(self) -> str:
        if not self._effects:
            return "(empty pipeline)"
        return "\n".join(f"[{index}] {effect.describe()}" for index, effect in enumerate(self._effects))

    def _native_compatible(self, effect: Effect) -> bool:
        return effect.type in _NATIVE_EFFECT_TYPES and not requires_python_processing(effect)

    def _run_python_segment(self, samples: Any, effects: list[Effect]) -> Any:
        current = ensure_float32_frames(samples)
        for effect in effects:
            current = process_python_effect(
                effect,
                current,
                self.sample_rate,
                self.block_size,
            )
        return current

    def _run_native_segment(self, samples: Any, effects: list[Effect], workers: int) -> Any:
        if _process_pipeline is None:
            return self._run_python_segment(samples, effects)

        specs = [effect.to_spec() for effect in effects]
        return _process_pipeline(
            samples,
            self.sample_rate,
            specs,
            self.block_size,
            workers,
        )

    def process(self, samples: Any, *, workers: int | None = None) -> Any:
        frames = ensure_float32_frames(samples)
        if self.channels is not None and frames.shape[1] != self.channels:
            raise ValueError(
                f"Pipeline expected {self.channels} channels, got {frames.shape[1]}."
            )

        resolved_workers = self.workers if workers is None else int(workers)
        if resolved_workers <= 0:
            resolved_workers = 1

        if not self._effects:
            return frames.copy()

        current = frames
        native_segment: list[Effect] = []

        for effect in self._effects:
            if self._native_compatible(effect):
                native_segment.append(effect)
                continue

            if native_segment:
                current = self._run_native_segment(current, native_segment, resolved_workers)
                native_segment.clear()

            current = self._run_python_segment(current, [effect])

        if native_segment:
            current = self._run_native_segment(current, native_segment, resolved_workers)

        return ensure_float32_frames(current)

    def __call__(self, samples: Any, *, workers: int | None = None) -> Any:
        return self.process(samples, workers=workers)

    @classmethod
    def from_effects(
        cls,
        sample_rate: int,
        *effects: Any,
        channels: int | None = None,
        block_size: int = 2048,
        workers: int = 1,
    ) -> "Pipeline":
        pipeline = cls(
            sample_rate=sample_rate,
            channels=channels,
            block_size=block_size,
            workers=workers,
        )
        pipeline.extend(effects)
        return pipeline

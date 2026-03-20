from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ._util import ensure_float32_frames
from .effects import compressor, highpass, lowpass
from .pipeline import Pipeline


@dataclass(slots=True)
class Band:
    name: str
    low_cut_hz: float | None = None
    high_cut_hz: float | None = None
    pipeline: Pipeline | None = None


class MultibandPipeline:
    def __init__(self, sample_rate: int, block_size: int = 2048, workers: int = 1) -> None:
        self.sample_rate = int(sample_rate)
        self.block_size = int(block_size)
        self.workers = int(workers)
        self._bands: list[Band] = []

    @property
    def bands(self) -> tuple[Band, ...]:
        return tuple(self._bands)

    def add_band(
        self,
        name: str,
        *,
        low_cut_hz: float | None = None,
        high_cut_hz: float | None = None,
        pipeline: Pipeline | None = None,
    ) -> "MultibandPipeline":
        self._bands.append(
            Band(
                name=name,
                low_cut_hz=low_cut_hz,
                high_cut_hz=high_cut_hz,
                pipeline=pipeline,
            )
        )
        return self

    def process(self, samples: Any) -> np.ndarray:
        if not self._bands:
            raise ValueError("At least one band must be configured before processing.")

        frames = ensure_float32_frames(samples)
        mixed = np.zeros_like(frames)

        for band in self._bands:
            band_signal = np.array(frames, copy=True)

            if band.high_cut_hz is not None:
                band_signal = Pipeline.from_effects(
                    self.sample_rate,
                    lowpass(band.high_cut_hz, stages=2),
                    channels=frames.shape[1],
                    block_size=self.block_size,
                    workers=self.workers,
                ).process(band_signal)

            if band.low_cut_hz is not None:
                band_signal = Pipeline.from_effects(
                    self.sample_rate,
                    highpass(band.low_cut_hz, stages=2),
                    channels=frames.shape[1],
                    block_size=self.block_size,
                    workers=self.workers,
                ).process(band_signal)

            if band.pipeline is not None:
                band_signal = band.pipeline.process(band_signal)

            mixed += band_signal

        return mixed

    def __call__(self, samples: Any) -> np.ndarray:
        return self.process(samples)


def multiband_compressor(
    sample_rate: int,
    *,
    low_cut_hz: float = 180.0,
    high_cut_hz: float = 3_200.0,
    low_threshold_db: float = -24.0,
    mid_threshold_db: float = -18.0,
    high_threshold_db: float = -20.0,
    low_ratio: float = 2.2,
    mid_ratio: float = 3.0,
    high_ratio: float = 2.4,
    attack_ms: float = 10.0,
    release_ms: float = 90.0,
    low_makeup_db: float = 0.0,
    mid_makeup_db: float = 0.0,
    high_makeup_db: float = 0.0,
    block_size: int = 2048,
    workers: int = 1,
) -> MultibandPipeline:
    processor = MultibandPipeline(sample_rate=sample_rate, block_size=block_size, workers=workers)
    processor.add_band(
        "low",
        high_cut_hz=low_cut_hz,
        pipeline=Pipeline.from_effects(
            sample_rate,
            compressor(
                threshold_db=low_threshold_db,
                ratio=low_ratio,
                attack_ms=attack_ms,
                release_ms=release_ms,
                makeup_db=low_makeup_db,
            ),
            block_size=block_size,
            workers=workers,
        ),
    )
    processor.add_band(
        "mid",
        low_cut_hz=low_cut_hz,
        high_cut_hz=high_cut_hz,
        pipeline=Pipeline.from_effects(
            sample_rate,
            compressor(
                threshold_db=mid_threshold_db,
                ratio=mid_ratio,
                attack_ms=attack_ms,
                release_ms=release_ms,
                makeup_db=mid_makeup_db,
            ),
            block_size=block_size,
            workers=workers,
        ),
    )
    processor.add_band(
        "high",
        low_cut_hz=high_cut_hz,
        pipeline=Pipeline.from_effects(
            sample_rate,
            compressor(
                threshold_db=high_threshold_db,
                ratio=high_ratio,
                attack_ms=attack_ms,
                release_ms=release_ms,
                makeup_db=high_makeup_db,
            ),
            block_size=block_size,
            workers=workers,
        ),
    )
    return processor

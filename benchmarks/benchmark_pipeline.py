from __future__ import annotations

import argparse
import time

import numpy as np

from voxis import Pipeline, compressor, delay, distortion, gain, lowpass, tremolo


def make_noise(sample_rate: int, seconds: float, channels: int) -> np.ndarray:
    generator = np.random.default_rng(42)
    return generator.uniform(-0.4, 0.4, size=(int(sample_rate * seconds), channels)).astype(np.float32)


def numpy_tremolo(samples: np.ndarray, sample_rate: int, rate_hz: float, depth: float) -> np.ndarray:
    timeline = np.arange(samples.shape[0], dtype=np.float32) / sample_rate
    lfo = (1.0 - depth) + depth * (0.5 * (np.sin(2.0 * np.pi * rate_hz * timeline) + 1.0))
    return samples * lfo[:, None]


def numpy_distortion(samples: np.ndarray, drive: float) -> np.ndarray:
    return np.tanh(samples * drive) / np.tanh(max(drive, 1.0))


def numpy_clip(samples: np.ndarray, threshold: float) -> np.ndarray:
    return np.clip(samples, -threshold, threshold)


def numpy_gain(samples: np.ndarray, db: float) -> np.ndarray:
    return samples * np.float32(10.0 ** (db / 20.0))


def benchmark(sample_rate: int, seconds: float, channels: int, iterations: int) -> None:
    samples = make_noise(sample_rate, seconds, channels)

    native = (
        Pipeline(sample_rate=sample_rate, channels=channels, block_size=2048)
        .add(gain(4.0))
        .add(tremolo(4.5, depth=0.4))
        .add(distortion(2.0))
        .add(lowpass(7_500.0, stages=2))
        .add(delay(90.0, feedback=0.25, mix=0.15))
        .add(compressor(threshold_db=-20.0, ratio=2.5))
    )

    start = time.perf_counter()
    for _ in range(iterations):
        native.process(samples)
    native_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(iterations):
        numpy_clip(
            numpy_distortion(
                numpy_tremolo(
                    numpy_gain(samples, 4.0),
                    sample_rate,
                    4.5,
                    0.4,
                ),
                2.0,
            ),
            0.98,
        )
    numpy_time = time.perf_counter() - start

    print(f"Frames: {samples.shape[0]:,}  Channels: {channels}")
    print(f"Iterations: {iterations}")
    print(f"Voxis native pipeline: {native_time:.4f}s")
    print(f"Approx NumPy chain:     {numpy_time:.4f}s")
    if native_time > 0.0:
        print(f"Speed ratio (NumPy / Voxis): {numpy_time / native_time:.2f}x")


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Voxis native pipeline.")
    parser.add_argument("--sample-rate", type=int, default=48_000)
    parser.add_argument("--seconds", type=float, default=8.0)
    parser.add_argument("--channels", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=10)
    args = parser.parse_args()

    benchmark(args.sample_rate, args.seconds, args.channels, args.iterations)


if __name__ == "__main__":
    main()

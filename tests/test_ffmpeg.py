from __future__ import annotations

import numpy as np

from voxis import AudioClip, FORMAT_CAPABILITIES, prepare_export_settings


def test_ffmpeg_roundtrip_wav(tmp_path) -> None:
    sample_rate = 44_100
    timeline = np.arange(sample_rate, dtype=np.float32) / sample_rate
    mono = 0.2 * np.sin(2.0 * np.pi * 220.0 * timeline)
    samples = np.column_stack([mono, mono]).astype(np.float32)

    original = AudioClip.from_array(samples, sample_rate)
    output_path = tmp_path / "roundtrip.wav"
    original.export(output_path)

    recovered = AudioClip.from_file(output_path)

    assert recovered.sample_rate == sample_rate
    assert recovered.channels == 2
    assert recovered.frames == original.frames
    assert np.max(np.abs(recovered.samples - original.samples)) < 5e-4


def test_lazy_export_supports_format_and_resample(tmp_path) -> None:
    sample_rate = 48_000
    timeline = np.arange(sample_rate, dtype=np.float32) / sample_rate
    mono = 0.15 * np.sin(2.0 * np.pi * 330.0 * timeline)
    samples = np.column_stack([mono, mono]).astype(np.float32)

    clip = AudioClip.from_array(samples, sample_rate)
    output_path = tmp_path / "resampled.wav"

    clip.apply("cinematic", lazy=True).export(
        output_path,
        format="wav",
        sample_rate=22_050,
        channels=1,
    )

    recovered = AudioClip.from_file(output_path)

    assert recovered.sample_rate == 22_050
    assert recovered.channels == 1


def test_export_validation_ignores_bitrate_for_wav() -> None:
    settings = prepare_export_settings("demo.wav", format="wav", bitrate="320k")
    assert settings.format == "wav"
    assert settings.bitrate is None
    assert settings.warnings
    assert FORMAT_CAPABILITIES["wav"]["bitrate"] is False


def test_ogg_export_coerces_unsupported_sample_rate(tmp_path) -> None:
    sample_rate = 44_100
    timeline = np.arange(sample_rate, dtype=np.float32) / sample_rate
    mono = 0.2 * np.sin(2.0 * np.pi * 180.0 * timeline)
    samples = np.column_stack([mono, mono]).astype(np.float32)

    clip = AudioClip.from_array(samples, sample_rate).resample(44_100)
    output_path = tmp_path / "resampled.ogg"

    clip.export(output_path, format="ogg", bitrate="192k")
    recovered = AudioClip.from_file(output_path)

    assert output_path.exists()
    assert recovered.sample_rate in set(FORMAT_CAPABILITIES["ogg"]["supported_sample_rates"])  # type: ignore[index]

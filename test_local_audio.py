from __future__ import annotations

import argparse
from pathlib import Path

from voxis import AudioClip, Pipeline, compressor, delay, distortion, lowpass, preset_names, stereo_width


SUPPORTED_EXTENSIONS = (".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac")


def find_default_input(base_dir: Path) -> Path:
    for path in sorted(base_dir.iterdir()):
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return path
    raise FileNotFoundError(
        "Nenhum arquivo de audio foi encontrado no diretorio atual. "
        "Passe um caminho com --input."
    )


def build_preview_pipeline(sample_rate: int, channels: int) -> Pipeline:
    return (
        Pipeline(sample_rate=sample_rate, channels=channels, block_size=2048)
        >> [
            distortion(drive=1.6),
            lowpass(frequency_hz=9000.0, stages=2),
            delay(delay_ms=135.0, feedback=0.28, mix=0.18),
            compressor(threshold_db=-18.0, ratio=3.0, makeup_db=1.5),
            stereo_width(width=1.15),
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Teste rapido da biblioteca Voxis.")
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Arquivo de entrada. Se nao for passado, Voxis usa o primeiro audio do diretorio.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("voxis_preview.wav"),
        help="Arquivo de saida gerado pelo teste.",
    )
    parser.add_argument(
        "--preset",
        type=str,
        default=None,
        help=f"Preset pronto. Opcoes: {', '.join(preset_names())}",
    )
    parser.add_argument("--format", type=str, default="wav", help="Formato de exportacao.")
    parser.add_argument("--bitrate", type=str, default=None, help="Bitrate de exportacao.")
    parser.add_argument("--sample-rate", type=int, default=None, help="Sample rate de saida.")
    parser.add_argument("--channels", type=int, default=None, help="Numero de canais de saida.")
    args = parser.parse_args()

    input_path = args.input if args.input is not None else find_default_input(Path.cwd())
    clip = AudioClip.from_file(input_path)

    print(f"Entrada: {input_path}")
    print(
        f"Formato: {clip.sample_rate} Hz | {clip.channels} canais | "
        f"{clip.duration_seconds:.2f} segundos"
    )

    if args.preset:
        rendered = clip.apply(args.preset, lazy=True).normalize(headroom_db=1.0)
        print(f"Preset aplicado: {args.preset}")
    else:
        rendered = clip.apply_pipeline(
            build_preview_pipeline(clip.sample_rate, clip.channels),
            lazy=True,
        ).normalize(headroom_db=1.0)
        print("Pipeline manual aplicada: distortion + lowpass + delay + compressor + stereo_width")

    output_path = rendered.export(
        args.output,
        format=args.format,
        bitrate=args.bitrate,
        sample_rate=args.sample_rate,
        channels=args.channels,
    )

    print(f"Saida criada: {output_path}")


if __name__ == "__main__":
    main()

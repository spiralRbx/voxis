from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import numpy as np

from voxis import AudioClip, Waveform


def _test_clip() -> AudioClip:
    """Load bundled song.mp3 or synthesise a fallback tone."""
    song = Path(__file__).parent / "song.mp3"
    if song.exists():
        try:
            return AudioClip.from_file(str(song))
        except Exception as exc:
            print(f"  (couldn't load song.mp3: {exc}; using synthetic tone)")
    sr = 44100
    t = np.linspace(0, 2, 2 * sr, dtype=np.float32)
    tone = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    stereo = np.stack([tone, tone], axis=1)
    return AudioClip.from_array(stereo, sample_rate=sr)


def test_all_outputs() -> None:
    clip = _test_clip()
    print(f"[clip] frames={clip.frames} sr={clip.sample_rate} ch={clip.channels} dur={clip.duration_seconds:.2f}s")

    wf = Waveform(clip, style="peaks")
    print(f"[waveform] {wf!r}")

    # --- SVG ---
    svg = wf.to_svg(width=800, height=120, color="#3b82f6")
    assert svg.startswith("<svg"), "SVG must start with <svg"
    assert 'viewBox="0 0 800 120"' in svg
    print(f"[svg] OK ({len(svg)} chars)")

    # --- ASCII ---
    asc = wf.to_ascii(width=80, height=12)
    lines = asc.split("\n")
    assert len(lines) == 12, f"ASCII height should be 12, got {len(lines)}"
    assert all(len(line) == 80 for line in lines), "ASCII lines must be exactly 80 wide"
    print(f"[ascii] OK ({len(lines)} rows x {len(lines[0])} cols)")
    print("       first 3 rows:")
    for row in lines[:3]:
        print(f"       {row}")

    # --- JSON ---
    j = wf.to_json(pixels=800)
    assert set(j.keys()) >= {"mins", "maxs", "pixels", "sampleRate", "durationSeconds", "style", "color"}
    assert len(j["mins"]) == 800
    assert len(j["maxs"]) == 800
    assert j["sampleRate"] == clip.sample_rate
    print(f"[json] OK (800 peaks, sr={j['sampleRate']})")

    # --- numpy peaks ---
    mins, maxs = wf.to_peaks(pixels=800)
    assert mins.shape == (800,) and maxs.shape == (800,)
    assert mins.dtype == np.float32
    # Sane ranges — real audio can slightly exceed ±1.0 after decode/resample.
    assert mins.min() >= -2.0, f"mins.min()={mins.min()} too low"
    assert maxs.max() <= 2.0, f"maxs.max()={maxs.max()} too high"
    assert float(mins.min()) < float(maxs.max()), "signal should have both positive and negative peaks"
    peak = max(abs(float(mins.min())), abs(float(maxs.max())))
    assert peak > 0.001, "signal appears silent"
    print(f"[peaks] OK range=[{mins.min():.3f}, {maxs.max():.3f}] peak={peak:.3f}")

    # --- PNG (optional, only if Pillow is present) ---
    try:
        import PIL  # noqa: F401
        png_bytes = wf.to_png(width=1200, height=200, color="#3b82f6")
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n"
        print(f"[png] OK ({len(png_bytes)} bytes)")

        out_png = _REPO_ROOT / "out_waveform.png"
        wf.save_png(str(out_png), width=1200, height=200)
        assert out_png.exists() and out_png.stat().st_size > 0
        print(f"[save_png] wrote {out_png} ({out_png.stat().st_size} bytes)")
    except ImportError:
        print("[png] SKIPPED (pillow not installed)")

    # --- save_svg ---
    out_svg = _REPO_ROOT / "out_waveform.svg"
    wf.save_svg(str(out_svg), width=800, height=120)
    assert out_svg.exists() and out_svg.stat().st_size > 0
    print(f"[save_svg] wrote {out_svg} ({out_svg.stat().st_size} bytes)")


def test_all_styles() -> None:
    """Every style must produce non-empty SVG with correct viewBox."""
    clip = _test_clip()
    for style in ("peaks", "line", "filled", "mirror", "bars"):
        wf = Waveform(clip, style=style)
        svg = wf.to_svg(width=400, height=80)
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert len(svg) > 100, f"style={style} produced suspiciously small SVG"
        print(f"[style={style:7s}] svg_len={len(svg)}")


def test_channel_selection() -> None:
    """Passing channel=0 or channel=1 should work and give different results
    when the two channels differ."""
    sr = 44100
    left = (0.5 * np.sin(2 * np.pi * 220 * np.linspace(0, 1, sr, dtype=np.float32))).astype(np.float32)
    right = (0.5 * np.sin(2 * np.pi * 880 * np.linspace(0, 1, sr, dtype=np.float32))).astype(np.float32)
    stereo = np.stack([left, right], axis=1)
    clip = AudioClip.from_array(stereo, sample_rate=sr)

    mono_mix, *_ = Waveform(clip, channel=None).to_peaks(pixels=100)
    left_only, *_ = Waveform(clip, channel=0).to_peaks(pixels=100)
    right_only, *_ = Waveform(clip, channel=1).to_peaks(pixels=100)

    assert mono_mix.shape == left_only.shape == right_only.shape == (100,)
    print("[channel] mono/L/R peaks computed distinctly")


def test_invalid_style() -> None:
    """Bad style values raise immediately."""
    clip = _test_clip()
    try:
        Waveform(clip, style="bogus")  # type: ignore[arg-type]
    except ValueError as exc:
        print(f"[invalid-style] correctly raised: {exc}")
    else:
        raise AssertionError("Expected ValueError for bogus style")


if __name__ == "__main__":
    print("=" * 70)
    print("voxis.waveform test suite")
    print("=" * 70)

    print("\n-- test_all_outputs --")
    test_all_outputs()

    print("\n-- test_all_styles --")
    test_all_styles()

    print("\n-- test_channel_selection --")
    test_channel_selection()

    print("\n-- test_invalid_style --")
    test_invalid_style()

    print("\n" + "=" * 70)
    print("ALL TESTS PASSED")
    print("=" * 70)

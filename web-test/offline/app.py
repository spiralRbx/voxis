from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from html import escape
from pathlib import Path

import numpy as np
from flask import Flask, render_template, request, send_file

from voxis import (
    AudioClip,
    FORMAT_CAPABILITIES,
    effect_names,
    prepare_export_settings,
    preset_names,
    downward_compression,
)

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_UPLOAD_FOLDER = BASE_DIR / "uploads"
DEFAULT_OUTPUT_FOLDER = BASE_DIR / "outputs"
app.config.setdefault("VOXIS_UPLOAD_FOLDER", DEFAULT_UPLOAD_FOLDER)
app.config.setdefault("VOXIS_OUTPUT_FOLDER", DEFAULT_OUTPUT_FOLDER)


def upload_folder() -> Path:
    return Path(app.config.get("VOXIS_UPLOAD_FOLDER", DEFAULT_UPLOAD_FOLDER))


def output_folder() -> Path:
    return Path(app.config.get("VOXIS_OUTPUT_FOLDER", DEFAULT_OUTPUT_FOLDER))


def ensure_runtime_dirs() -> tuple[Path, Path]:
    uploads = upload_folder()
    outputs = output_folder()
    uploads.mkdir(parents=True, exist_ok=True)
    outputs.mkdir(parents=True, exist_ok=True)
    return uploads, outputs


ensure_runtime_dirs()


def range_field(name: str, label: str, minimum: float, maximum: float, step: float, value: float) -> dict[str, float | str]:
    return {"name": name, "label": label, "min": minimum, "max": maximum, "step": step, "value": value}


RG = range_field

EFFECT_GROUPS = [
    ("Basic", [
        ("gain", "Gain", [RG("gain_db", "dB", -24.0, 24.0, 0.1, 0.0)]),
        ("fade_in", "Fade In", [RG("fade_in_ms", "Dur", 10, 5000, 10, 220)]),
        ("fade_out", "Fade Out", [RG("fade_out_ms", "Dur", 10, 5000, 10, 220)]),
        ("trim", "Trim", [RG("trim_start_ms", "Start", 0, 120000, 10, 0), RG("trim_end_ms", "End", 0, 120000, 10, 12000)]),
        ("cut", "Cut", [RG("cut_start_ms", "Start", 0, 120000, 10, 500), RG("cut_end_ms", "End", 0, 120000, 10, 1200)]),
        ("remove_silence", "Silence Removal", [RG("silence_threshold_db", "Threshold", -90, -10, 1, -48), RG("silence_min_ms", "Min", 10, 3000, 10, 100), RG("silence_padding_ms", "Pad", 0, 300, 5, 20)]),
        ("reverse", "Reverse", []),
        ("to_mono", "Mono", []),
        ("to_stereo", "Stereo", []),
        ("remove_dc_offset", "DC Offset", []),
        ("crossfade", "Crossfade", [RG("crossfade_ms", "Dur", 20, 5000, 10, 400)]),
        ("pan", "Pan", [RG("pan_position", "Pos", -1.0, 1.0, 0.05, 0.0)]),
    ]),
    ("Dynamics", [
        ("compressor", "Compressor", [RG("compressor_threshold_db", "Threshold", -40, -4, 1, -18), RG("compressor_ratio", "Ratio", 1.0, 10.0, 0.1, 3.2)]),
        ("downward_compression", "Downward Compression", [RG("downward_threshold_db", "Threshold", -40, -4, 1, -18), RG("downward_ratio", "Ratio", 1.0, 10.0, 0.1, 4.0)]),
        ("upward_compression", "Upward Compression", [RG("upward_threshold_db", "Threshold", -70, -12, 1, -42), RG("upward_ratio", "Ratio", 1.0, 6.0, 0.1, 2.0), RG("upward_max_gain_db", "Max Gain", 0.0, 30.0, 0.5, 18.0)]),
        ("limiter", "Limiter", [RG("limiter_ceiling_db", "Ceiling", -6.0, 0.0, 0.1, -1.0)]),
        ("expander", "Expander", [RG("expander_threshold_db", "Threshold", -60, -10, 1, -34), RG("expander_ratio", "Ratio", 1.0, 4.0, 0.1, 1.8)]),
        ("noise_gate", "Noise Gate", [RG("gate_threshold_db", "Threshold", -70, -10, 1, -48), RG("gate_floor_db", "Floor", -96, -20, 1, -80)]),
        ("deesser", "De-esser", [RG("deesser_frequency_hz", "Freq", 3000, 10000, 100, 6500), RG("deesser_threshold_db", "Threshold", -40, -8, 1, -28), RG("deesser_amount", "Amount", 0.0, 1.0, 0.05, 0.8)]),
        ("transient_shaper", "Transient Shaper", [RG("transient_attack", "Attack", -1.0, 2.0, 0.05, 0.75), RG("transient_sustain", "Sustain", -1.0, 2.0, 0.05, 0.25)]),
        ("multiband_compressor", "Multiband Compressor", [RG("mb_low_cut_hz", "Low Cut", 60, 600, 10, 180), RG("mb_high_cut_hz", "High Cut", 1200, 8000, 50, 3200), RG("mb_low_threshold_db", "Low Th", -40, -4, 1, -24), RG("mb_mid_threshold_db", "Mid Th", -40, -4, 1, -18), RG("mb_high_threshold_db", "High Th", -40, -4, 1, -20), RG("mb_ratio", "Ratio", 1.0, 8.0, 0.1, 2.6)]),
    ]),
    ("Tone / EQ", [
        ("distortion", "Distortion", [RG("drive", "Drive", 0.5, 5.0, 0.1, 1.8)]),
        ("lowpass", "Low-pass", [RG("lowpass_freq", "Freq", 100, 20000, 100, 9000)]),
        ("highpass", "High-pass", [RG("highpass_freq", "Freq", 20, 8000, 10, 120)]),
        ("bandpass", "Band-pass", [RG("bandpass_freq", "Center", 50, 12000, 50, 1200), RG("bandpass_q", "Q", 0.2, 10.0, 0.1, 0.9)]),
        ("notch", "Notch", [RG("notch_freq", "Freq", 50, 12000, 50, 3500), RG("notch_q", "Q", 0.2, 10.0, 0.1, 2.0)]),
        ("peak_eq", "Peak EQ", [RG("peak_eq_freq", "Freq", 50, 12000, 50, 2800), RG("peak_eq_gain_db", "Gain", -12, 12, 0.1, 2.5)]),
        ("low_shelf", "Low Shelf", [RG("low_shelf_freq", "Freq", 30, 500, 10, 120), RG("low_shelf_gain_db", "Gain", -12, 12, 0.1, 2.0)]),
        ("high_shelf", "High Shelf", [RG("high_shelf_freq", "Freq", 1000, 18000, 100, 9000), RG("high_shelf_gain_db", "Gain", -12, 12, 0.1, 1.8)]),
        ("graphic_eq", "Graphic EQ", [RG("geq_100", "100", -12, 12, 0.1, 0.0), RG("geq_250", "250", -12, 12, 0.1, 0.0), RG("geq_1000", "1k", -12, 12, 0.1, 0.0), RG("geq_4000", "4k", -12, 12, 0.1, 0.0), RG("geq_12000", "12k", -12, 12, 0.1, 0.0)]),
        ("resonant_filter", "Resonant Filter", [RG("resonant_freq", "Freq", 40, 12000, 10, 1200), RG("resonant_q", "Q", 0.2, 20.0, 0.1, 2.4)]),
        ("dynamic_eq", "Dynamic EQ", [RG("dynamic_eq_freq", "Freq", 80, 12000, 10, 2800), RG("dynamic_eq_threshold_db", "Threshold", -48, -4, 1, -24), RG("dynamic_eq_cut_db", "Cut", -18, 0, 0.1, -6)]),
        ("formant_filter", "Formant Filter", [RG("formant_morph", "Morph", 0.0, 4.0, 0.05, 0.0), RG("formant_intensity", "Intensity", 0.0, 2.0, 0.05, 1.0)]),
        ("stereo_width", "Stereo Width", [RG("stereo_width_amount", "Width", 0.0, 2.0, 0.05, 1.2)]),
    ]),
    ("Delay", [
        ("delay", "Simple Delay", [RG("delay_ms", "Delay", 10, 900, 5, 135), RG("delay_feedback", "Feedback", 0.0, 0.95, 0.01, 0.28), RG("delay_mix", "Mix", 0.0, 1.0, 0.01, 0.18)]),
        ("feedback_delay", "Feedback Delay", [RG("feedback_delay_ms", "Delay", 40, 1200, 5, 240), RG("feedback_delay_feedback", "Feedback", 0.0, 0.95, 0.01, 0.62), RG("feedback_delay_mix", "Mix", 0.0, 1.0, 0.01, 0.35)]),
        ("echo", "Echo", [RG("echo_delay_ms", "Delay", 80, 1400, 5, 320), RG("echo_feedback", "Feedback", 0.0, 0.95, 0.01, 0.38), RG("echo_mix", "Mix", 0.0, 1.0, 0.01, 0.28)]),
        ("ping_pong_delay", "Ping-pong", [RG("ping_pong_delay_ms", "Delay", 40, 1200, 5, 220), RG("ping_pong_feedback", "Feedback", 0.0, 0.95, 0.01, 0.58), RG("ping_pong_mix", "Mix", 0.0, 1.0, 0.01, 0.30)]),
        ("multi_tap_delay", "Multi-tap", [RG("multi_tap_delay_ms", "Base", 30, 600, 5, 110), RG("multi_tap_taps", "Taps", 2, 8, 1, 4), RG("multi_tap_mix", "Mix", 0.0, 1.0, 0.01, 0.32)]),
        ("slapback", "Slapback", [RG("slapback_delay_ms", "Delay", 40, 160, 1, 92), RG("slapback_mix", "Mix", 0.0, 1.0, 0.01, 0.22)]),
    ]),
    ("Reverb", [
        ("early_reflections", "Early Reflections", [RG("early_reflections_mix", "Mix", 0.0, 1.0, 0.01, 0.18), RG("early_reflections_taps", "Taps", 2, 10, 1, 6)]),
        ("room_reverb", "Room", [RG("room_decay_seconds", "Decay", 0.2, 2.0, 0.05, 0.8), RG("room_mix", "Mix", 0.0, 1.0, 0.01, 0.22)]),
        ("hall_reverb", "Hall", [RG("hall_decay_seconds", "Decay", 0.5, 4.0, 0.05, 1.9), RG("hall_mix", "Mix", 0.0, 1.0, 0.01, 0.26)]),
        ("plate_reverb", "Plate", [RG("plate_decay_seconds", "Decay", 0.3, 3.0, 0.05, 1.2), RG("plate_mix", "Mix", 0.0, 1.0, 0.01, 0.22)]),
        ("convolution_reverb", "Convolution", [RG("convolution_mix", "Mix", 0.0, 1.0, 0.01, 0.24)]),
    ]),
    ("Modulation", [
        ("chorus", "Chorus", [RG("chorus_rate_hz", "Rate", 0.1, 5.0, 0.05, 0.9), RG("chorus_depth_ms", "Depth", 1.0, 20.0, 0.1, 7.5), RG("chorus_mix", "Mix", 0.0, 1.0, 0.01, 0.35)]),
        ("flanger", "Flanger", [RG("flanger_rate_hz", "Rate", 0.05, 2.0, 0.01, 0.25), RG("flanger_depth_ms", "Depth", 0.1, 6.0, 0.05, 1.8), RG("flanger_mix", "Mix", 0.0, 1.0, 0.01, 0.45)]),
        ("phaser", "Phaser", [RG("phaser_rate_hz", "Rate", 0.05, 3.0, 0.01, 0.35), RG("phaser_depth", "Depth", 0.0, 1.0, 0.01, 0.75), RG("phaser_mix", "Mix", 0.0, 1.0, 0.01, 0.50)]),
        ("tremolo", "Tremolo", [RG("tremolo_rate_hz", "Rate", 0.1, 20.0, 0.1, 5.0), RG("tremolo_depth", "Depth", 0.0, 1.0, 0.01, 0.50)]),
        ("vibrato", "Vibrato", [RG("vibrato_rate_hz", "Rate", 0.2, 10.0, 0.1, 5.0), RG("vibrato_depth_ms", "Depth", 0.2, 10.0, 0.1, 3.5)]),
        ("auto_pan", "Auto-pan", [RG("auto_pan_rate_hz", "Rate", 0.05, 5.0, 0.05, 0.35), RG("auto_pan_depth", "Depth", 0.0, 1.0, 0.01, 1.0)]),
        ("rotary_speaker", "Rotary Speaker", [RG("rotary_rate_hz", "Rate", 0.1, 5.0, 0.05, 0.8), RG("rotary_depth", "Depth", 0.0, 1.0, 0.01, 0.7), RG("rotary_mix", "Mix", 0.0, 1.0, 0.01, 0.65)]),
        ("ring_modulation", "Ring Modulation", [RG("ring_frequency_hz", "Freq", 1.0, 2000.0, 1.0, 30.0), RG("ring_mix", "Mix", 0.0, 1.0, 0.01, 0.5)]),
        ("frequency_shifter", "Frequency Shifter", [RG("shifter_hz", "Shift", -1200.0, 1200.0, 1.0, 120.0), RG("shifter_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
    ]),
    ("Drive / Saturation", [
        ("overdrive", "Overdrive", [RG("overdrive_drive", "Drive", 0.5, 5.0, 0.1, 1.8), RG("overdrive_tone", "Tone", 0.0, 1.0, 0.01, 0.55), RG("overdrive_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("fuzz", "Fuzz", [RG("fuzz_drive", "Drive", 0.8, 8.0, 0.1, 3.6), RG("fuzz_bias", "Bias", -0.4, 0.4, 0.01, 0.12), RG("fuzz_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("bitcrusher", "Bitcrusher", [RG("bitcrusher_bits", "Bits", 4, 16, 1, 8), RG("bitcrusher_reduction", "Hold", 1, 24, 1, 4), RG("bitcrusher_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("waveshaper", "Waveshaper", [RG("waveshaper_amount", "Amount", 0.2, 4.0, 0.05, 1.4), RG("waveshaper_symmetry", "Symmetry", -0.9, 0.9, 0.01, 0.0), RG("waveshaper_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("tube_saturation", "Tube Saturation", [RG("tube_drive", "Drive", 0.5, 5.0, 0.1, 1.6), RG("tube_bias", "Bias", -0.3, 0.3, 0.01, 0.08), RG("tube_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("tape_saturation", "Tape Saturation", [RG("tape_drive", "Drive", 0.5, 5.0, 0.1, 1.4), RG("tape_softness", "Softness", 0.0, 1.0, 0.01, 0.35), RG("tape_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("soft_clipping", "Soft Clipping", [RG("soft_clip_threshold", "Threshold", 0.2, 1.0, 0.01, 0.85)]),
        ("hard_clipping", "Hard Clipping", [RG("hard_clip_threshold", "Threshold", 0.2, 1.0, 0.01, 0.92)]),
    ]),
    ("Pitch / Tempo", [
        ("pitch_shift", "Pitch Shift", [RG("pitch_shift_semitones", "Semitones", -12.0, 12.0, 0.5, 3.0)]),
        ("time_stretch", "Time Stretch", [RG("time_stretch_rate", "Rate", 0.5, 1.5, 0.01, 0.85)]),
        ("time_compression", "Time Compression", [RG("time_compression_rate", "Rate", 1.0, 2.0, 0.01, 1.18)]),
        ("auto_tune", "Auto-Tune", [RG("auto_tune_strength", "Strength", 0.0, 1.0, 0.01, 0.70)]),
        ("harmonizer", "Harmonizer", [RG("harmonizer_interval", "Interval", -12.0, 12.0, 0.5, 7.0), RG("harmonizer_mix", "Mix", 0.0, 1.0, 0.01, 0.35)]),
        ("octaver", "Octaver", [RG("octaver_down_mix", "Down", 0.0, 1.0, 0.01, 0.45), RG("octaver_up_mix", "Up", 0.0, 1.0, 0.01, 0.00)]),
        ("formant_shifting", "Formant Shift", [RG("formant_shift", "Shift", 0.6, 1.6, 0.01, 1.12), RG("formant_shift_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
    ]),
    ("Restoration / AI-like", [
        ("noise_reduction", "Noise Reduction", [RG("noise_reduction_strength", "Strength", 0.0, 1.0, 0.01, 0.50)]),
        ("voice_isolation", "Voice Isolation", [RG("voice_isolation_strength", "Strength", 0.0, 1.0, 0.01, 0.75)]),
        ("source_separation", "Source Separation", [RG("source_separation_strength", "Strength", 0.0, 1.0, 0.01, 0.80)]),
        ("de_reverb", "De-Reverb", [RG("de_reverb_amount", "Amount", 0.0, 1.0, 0.01, 0.45)]),
        ("de_echo", "De-Echo", [RG("de_echo_amount", "Amount", 0.0, 1.0, 0.01, 0.45)]),
        ("spectral_repair", "Spectral Repair", [RG("spectral_repair_strength", "Strength", 0.0, 1.0, 0.01, 0.35)]),
        ("ai_enhancer", "AI Enhancer", [RG("ai_enhancer_amount", "Amount", 0.0, 1.0, 0.01, 0.60)]),
        ("speech_enhancement", "Speech Enhancement", [RG("speech_enhancement_amount", "Amount", 0.0, 1.0, 0.01, 0.70)]),
    ]),
    ("Creative / Special", [
        ("glitch_effect", "Glitch", [RG("glitch_slice_ms", "Slice", 20, 220, 5, 70), RG("glitch_repeat", "Repeat", 0.0, 0.8, 0.01, 0.22), RG("glitch_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("stutter", "Stutter", [RG("stutter_slice_ms", "Slice", 20, 220, 5, 90), RG("stutter_repeats", "Repeats", 1, 8, 1, 3), RG("stutter_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("tape_stop", "Tape Stop", [RG("tape_stop_ms", "Stop", 120, 2400, 10, 900), RG("tape_stop_curve", "Curve", 0.5, 4.0, 0.05, 2.0), RG("tape_stop_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("reverse_reverb", "Reverse Reverb", [RG("reverse_reverb_decay", "Decay", 0.2, 3.0, 0.05, 1.2), RG("reverse_reverb_mix", "Mix", 0.0, 1.0, 0.01, 0.45)]),
        ("granular_synthesis", "Granular", [RG("granular_grain_ms", "Grain", 20, 220, 5, 80), RG("granular_overlap", "Overlap", 0.0, 0.9, 0.01, 0.50), RG("granular_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("time_slicing", "Time Slicing", [RG("time_slicing_ms", "Slice", 30, 320, 5, 120), RG("time_slicing_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("random_pitch_mod", "Random Pitch Mod", [RG("random_pitch_depth", "Depth", 0.0, 6.0, 0.1, 2.0), RG("random_pitch_segment_ms", "Segment", 60, 500, 10, 180), RG("random_pitch_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("vinyl_effect", "Vinyl", [RG("vinyl_noise", "Noise", 0.0, 1.0, 0.01, 0.08), RG("vinyl_wow", "Wow", 0.0, 1.0, 0.01, 0.15), RG("vinyl_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("radio_effect", "Radio", [RG("radio_noise", "Noise", 0.0, 0.3, 0.01, 0.04), RG("radio_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("telephone_effect", "Telephone", [RG("telephone_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("retro_8bit", "Retro 8-bit", [RG("retro_bits", "Bits", 2, 12, 1, 6), RG("retro_hold", "Hold", 1, 20, 1, 8), RG("retro_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("slow_motion_extreme", "Slow Motion", [RG("slow_motion_rate", "Rate", 0.2, 0.9, 0.01, 0.45), RG("slow_motion_tone_hz", "Tone", 800, 12000, 50, 4800)]),
        ("robot_voice", "Robot Voice", [RG("robot_carrier_hz", "Carrier", 20, 240, 1, 70), RG("robot_mix", "Mix", 0.0, 1.0, 0.01, 0.85)]),
        ("alien_voice", "Alien Voice", [RG("alien_shift", "Pitch", -12.0, 12.0, 0.5, 5.0), RG("alien_formant", "Formant", 0.6, 1.8, 0.01, 1.18), RG("alien_mix", "Mix", 0.0, 1.0, 0.01, 0.80)]),
    ]),
    ("Spectral", [
        ("fft_filter", "FFT Filter", [RG("fft_filter_low_hz", "Low", 20, 2000, 10, 80), RG("fft_filter_high_hz", "High", 1000, 20000, 50, 12000), RG("fft_filter_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("spectral_gating", "Spectral Gating", [RG("spectral_gate_threshold_db", "Threshold", -90, -10, 1, -42), RG("spectral_gate_floor", "Floor", 0.0, 1.0, 0.01, 0.08)]),
        ("spectral_blur", "Spectral Blur", [RG("spectral_blur_amount", "Amount", 0.0, 1.0, 0.01, 0.45)]),
        ("spectral_freeze", "Spectral Freeze", [RG("spectral_freeze_start_ms", "Start", 0, 4000, 10, 120), RG("spectral_freeze_mix", "Mix", 0.0, 1.0, 0.01, 0.70)]),
        ("spectral_morphing", "Spectral Morphing", [RG("spectral_morph_amount", "Amount", 0.0, 1.0, 0.01, 0.50)]),
        ("phase_vocoder", "Phase Vocoder", [RG("phase_vocoder_rate", "Rate", 0.4, 1.6, 0.01, 0.85)]),
        ("harmonic_percussive_separation", "Harmonic/Percussive", [RG("hps_mix", "Mix", 0.0, 1.0, 0.01, 1.0)]),
        ("spectral_delay", "Spectral Delay", [RG("spectral_delay_ms", "Delay", 20, 800, 5, 240), RG("spectral_delay_feedback", "Feedback", 0.0, 0.95, 0.01, 0.15), RG("spectral_delay_mix", "Mix", 0.0, 1.0, 0.01, 0.35)]),
    ]),
    ("Stereo / Spatial", [
        ("stereo_widening", "Stereo Widening", [RG("stereo_widening_amount", "Amount", 0.0, 2.5, 0.01, 1.25)]),
        ("mid_side_processing", "Mid/Side", [RG("mid_gain_db", "Mid dB", -12.0, 12.0, 0.1, 0.0), RG("side_gain_db", "Side dB", -12.0, 12.0, 0.1, 1.5)]),
        ("stereo_imager", "Stereo Imager", [RG("stereo_imager_low", "Low Width", 0.0, 2.0, 0.01, 0.90), RG("stereo_imager_high", "High Width", 0.0, 2.5, 0.01, 1.35)]),
        ("binaural_effect", "Binaural", [RG("binaural_azimuth", "Azimuth", -90.0, 90.0, 1.0, 25.0), RG("binaural_distance", "Distance", 0.3, 3.0, 0.01, 1.0), RG("binaural_room_mix", "Room", 0.0, 0.4, 0.01, 0.08)]),
        ("spatial_positioning", "3D Position", [RG("spatial_azimuth", "Azimuth", -90.0, 90.0, 1.0, 25.0), RG("spatial_elevation", "Elevation", -60.0, 60.0, 1.0, 0.0), RG("spatial_distance", "Distance", 0.3, 3.0, 0.01, 1.0)]),
        ("hrtf_simulation", "HRTF Sim", [RG("hrtf_azimuth", "Azimuth", -90.0, 90.0, 1.0, 30.0), RG("hrtf_elevation", "Elevation", -60.0, 60.0, 1.0, 0.0), RG("hrtf_distance", "Distance", 0.3, 3.0, 0.01, 1.0)]),
    ]),
    ("Utilities / Analysis", [
        ("resample", "Resample", [RG("utility_resample_rate", "Rate", 8_000, 96_000, 100, 48_000)]),
        ("dither", "Dither", [RG("utility_dither_bits", "Bits", 4, 24, 1, 16)]),
        ("bit_depth_conversion", "Bit Depth", [RG("utility_bit_depth", "Bits", 4, 24, 1, 16)]),
        ("loudness_normalization", "Loudness", [RG("utility_target_lufs", "LUFS", -30.0, -8.0, 0.1, -16.0)]),
        ("analysis_envelope", "Envelope Follow", [RG("analysis_attack_ms", "Attack", 0.1, 200.0, 0.1, 10.0), RG("analysis_release_ms", "Release", 1.0, 500.0, 0.1, 80.0)]),
    ]),
]


def split_effect_groups(groups: list[tuple[str, list[tuple[str, str, list[dict[str, float | int | str]]]]]], column_count: int = 2) -> list[list[tuple[str, list[tuple[str, str, list[dict[str, float | int | str]]]]]]]:
    lanes: list[list[tuple[str, list[tuple[str, str, list[dict[str, float | int | str]]]]]]] = [[] for _ in range(max(1, int(column_count)))]
    weights = [0] * len(lanes)
    for group in groups:
        lane_index = min(range(len(lanes)), key=lambda index: weights[index])
        lanes[lane_index].append(group)
        weights[lane_index] += max(1, len(group[1]))
    return lanes


TEMPLATE_NAME = "index.html"


@dataclass(slots=True)
class RenderStep:
    label: str
    apply: Callable[[AudioClip], AudioClip]


def f(name: str, default: float) -> float:
    return float(request.form.get(name, default))


def i(name: str, default: int) -> int:
    return int(float(request.form.get(name, default)))


def metric_lines(clip: AudioClip, *, include_envelope: bool = False, attack_ms: float = 10.0, release_ms: float = 80.0) -> list[str]:
    lines = [
        f"sample_rate: {clip.sample_rate}",
        f"channels: {clip.channels}",
        f"duration_seconds: {clip.duration_seconds:.2f}",
        f"peak_dbfs: {clip.peak_detection():.2f}",
        f"rms_dbfs: {clip.rms_analysis():.2f}",
        f"lufs_approx: {clip.loudness_lufs():.2f}",
    ]
    if include_envelope:
        envelope = clip.envelope_follower(attack_ms=attack_ms, release_ms=release_ms)
        lines.append(f"envelope_mean: {float(np.mean(envelope)):.4f}")
        lines.append(f"envelope_peak: {float(np.max(envelope)):.4f}")
    return lines


def default_ir(sample_rate: int, channels: int) -> np.ndarray:
    length = max(64, int(sample_rate * 0.8))
    t = np.arange(length, dtype=np.float32) / sample_rate
    decay = np.exp(-t / 0.28).astype(np.float32)
    noise = np.random.default_rng(77).normal(0.0, 1.0, size=(length, channels)).astype(np.float32)
    ir = noise * decay[:, None]
    ir[0, :] += 1.0
    peak = float(np.max(np.abs(ir)))
    return (ir / peak).astype(np.float32) if peak > 0 else ir


def save_optional_upload(field_name: str, uid: str, suffix_label: str) -> Path | None:
    file_obj = request.files.get(field_name)
    if file_obj is None or file_obj.filename == "":
        return None
    uploads, _ = ensure_runtime_dirs()
    ext = Path(file_obj.filename).suffix.lower() or ".wav"
    path = uploads / f"{uid}_{suffix_label}{ext}"
    file_obj.save(path)
    return path


def build_steps(uid: str, clip: AudioClip, crossfade_clip: AudioClip | None) -> list[RenderStep]:
    steps: list[RenderStep] = []
    preset = request.form.get("preset", "").strip()
    if preset:
        steps.append(RenderStep(f'preset("{preset}")', lambda current, preset_name=preset: current.preset(preset_name)))  # type: ignore[arg-type]

    if "gain" in request.form:
        gain_db = f("gain_db", 0.0)
        steps.append(RenderStep(f"gain(db={gain_db:.2f})", lambda current, value=gain_db: current.gain(value)))
    if "fade_in" in request.form:
        fade_in_ms = f("fade_in_ms", 220.0)
        steps.append(RenderStep(f"fade_in(duration_ms={fade_in_ms:.2f})", lambda current, value=fade_in_ms: current.fade_in(value)))
    if "fade_out" in request.form:
        fade_out_ms = f("fade_out_ms", 220.0)
        steps.append(RenderStep(f"fade_out(duration_ms={fade_out_ms:.2f})", lambda current, value=fade_out_ms: current.fade_out(value)))
    if "trim" in request.form:
        trim_start_ms = f("trim_start_ms", 0.0)
        trim_end_ms = f("trim_end_ms", 12000.0)
        steps.append(RenderStep(f"trim(start_ms={trim_start_ms:.2f}, end_ms={trim_end_ms:.2f})", lambda current, start=trim_start_ms, end=trim_end_ms: current.trim(start_ms=start, end_ms=end)))
    if "cut" in request.form:
        cut_start_ms = f("cut_start_ms", 500.0)
        cut_end_ms = f("cut_end_ms", 1200.0)
        steps.append(RenderStep(f"cut(start_ms={cut_start_ms:.2f}, end_ms={cut_end_ms:.2f})", lambda current, start=cut_start_ms, end=cut_end_ms: current.cut(start_ms=start, end_ms=end)))
    if "remove_silence" in request.form:
        silence_threshold_db = f("silence_threshold_db", -48.0)
        silence_min_ms = f("silence_min_ms", 100.0)
        silence_padding_ms = f("silence_padding_ms", 20.0)
        steps.append(RenderStep(f"remove_silence(threshold_db={silence_threshold_db:.2f}, min_silence_ms={silence_min_ms:.2f}, padding_ms={silence_padding_ms:.2f})", lambda current, threshold=silence_threshold_db, min_ms=silence_min_ms, pad=silence_padding_ms: current.remove_silence(threshold_db=threshold, min_silence_ms=min_ms, padding_ms=pad)))
    if "reverse" in request.form:
        steps.append(RenderStep("reverse()", lambda current: current.reverse()))
    if "to_mono" in request.form:
        steps.append(RenderStep("to_mono()", lambda current: current.to_mono()))
    if "to_stereo" in request.form:
        steps.append(RenderStep("to_stereo()", lambda current: current.to_stereo()))
    if "remove_dc_offset" in request.form:
        steps.append(RenderStep("remove_dc_offset()", lambda current: current.remove_dc_offset()))
    if "crossfade" in request.form:
        if crossfade_clip is None:
            raise ValueError("Crossfade was enabled, but the second file was not uploaded.")
        crossfade_ms = f("crossfade_ms", 400.0)
        steps.append(RenderStep(f"crossfade(duration_ms={crossfade_ms:.2f})", lambda current, other=crossfade_clip, duration=crossfade_ms: current.crossfade(other, duration)))
    if "pan" in request.form:
        pan_position = f("pan_position", 0.0)
        steps.append(RenderStep(f"pan(position={pan_position:.2f})", lambda current, value=pan_position: current.pan(value)))

    if "compressor" in request.form:
        threshold_db = f("compressor_threshold_db", -18.0)
        ratio = f("compressor_ratio", 3.2)
        steps.append(RenderStep(f"compressor(threshold_db={threshold_db:.2f}, ratio={ratio:.2f})", lambda current, threshold=threshold_db, ratio_value=ratio: current.compressor(threshold_db=threshold, ratio=ratio_value)))
    if "downward_compression" in request.form:
        threshold_db = f("downward_threshold_db", -18.0)
        ratio = f("downward_ratio", 4.0)
        steps.append(RenderStep(f"downward_compression(threshold_db={threshold_db:.2f}, ratio={ratio:.2f})", lambda current, threshold=threshold_db, ratio_value=ratio: current.apply(downward_compression(threshold_db=threshold, ratio=ratio_value))))
    if "upward_compression" in request.form:
        threshold_db = f("upward_threshold_db", -42.0)
        ratio = f("upward_ratio", 2.0)
        max_gain_db = f("upward_max_gain_db", 18.0)
        steps.append(RenderStep(f"upward_compression(threshold_db={threshold_db:.2f}, ratio={ratio:.2f}, max_gain_db={max_gain_db:.2f})", lambda current, threshold=threshold_db, ratio_value=ratio, max_gain=max_gain_db: current.upward_compression(threshold_db=threshold, ratio=ratio_value, max_gain_db=max_gain)))
    if "limiter" in request.form:
        ceiling_db = f("limiter_ceiling_db", -1.0)
        steps.append(RenderStep(f"limiter(ceiling_db={ceiling_db:.2f})", lambda current, value=ceiling_db: current.limiter(ceiling_db=value)))
    if "expander" in request.form:
        threshold_db = f("expander_threshold_db", -34.0)
        ratio = f("expander_ratio", 1.8)
        steps.append(RenderStep(f"expander(threshold_db={threshold_db:.2f}, ratio={ratio:.2f})", lambda current, threshold=threshold_db, ratio_value=ratio: current.expander(threshold_db=threshold, ratio=ratio_value)))
    if "noise_gate" in request.form:
        threshold_db = f("gate_threshold_db", -48.0)
        floor_db = f("gate_floor_db", -80.0)
        steps.append(RenderStep(f"noise_gate(threshold_db={threshold_db:.2f}, floor_db={floor_db:.2f})", lambda current, threshold=threshold_db, floor=floor_db: current.noise_gate(threshold_db=threshold, floor_db=floor)))
    if "deesser" in request.form:
        frequency_hz = f("deesser_frequency_hz", 6500.0)
        threshold_db = f("deesser_threshold_db", -28.0)
        amount = f("deesser_amount", 0.8)
        steps.append(RenderStep(f"deesser(frequency_hz={frequency_hz:.2f}, threshold_db={threshold_db:.2f}, amount={amount:.2f})", lambda current, freq=frequency_hz, threshold=threshold_db, amount_value=amount: current.deesser(frequency_hz=freq, threshold_db=threshold, amount=amount_value)))
    if "transient_shaper" in request.form:
        attack = f("transient_attack", 0.75)
        sustain = f("transient_sustain", 0.25)
        steps.append(RenderStep(f"transient_shaper(attack={attack:.2f}, sustain={sustain:.2f})", lambda current, attack_value=attack, sustain_value=sustain: current.transient_shaper(attack=attack_value, sustain=sustain_value)))
    if "multiband_compressor" in request.form:
        low_cut_hz = f("mb_low_cut_hz", 180.0)
        high_cut_hz = f("mb_high_cut_hz", 3200.0)
        low_threshold_db = f("mb_low_threshold_db", -24.0)
        mid_threshold_db = f("mb_mid_threshold_db", -18.0)
        high_threshold_db = f("mb_high_threshold_db", -20.0)
        ratio = f("mb_ratio", 2.6)
        steps.append(RenderStep(f"multiband_compressor(low_cut_hz={low_cut_hz:.2f}, high_cut_hz={high_cut_hz:.2f}, ratio={ratio:.2f})", lambda current, low_cut=low_cut_hz, high_cut=high_cut_hz, low_th=low_threshold_db, mid_th=mid_threshold_db, high_th=high_threshold_db, ratio_value=ratio: current.multiband_compressor(low_cut_hz=low_cut, high_cut_hz=high_cut, low_threshold_db=low_th, mid_threshold_db=mid_th, high_threshold_db=high_th, low_ratio=ratio_value, mid_ratio=ratio_value, high_ratio=ratio_value)))

    tone_map = {
        "distortion": lambda: RenderStep(f"distortion(drive={f('drive', 1.8):.2f})", lambda current, value=f("drive", 1.8): current.distortion(value)),
        "lowpass": lambda: RenderStep(f"lowpass(frequency_hz={f('lowpass_freq', 9000.0):.2f})", lambda current, value=f("lowpass_freq", 9000.0): current.lowpass(value)),
        "highpass": lambda: RenderStep(f"highpass(frequency_hz={f('highpass_freq', 120.0):.2f})", lambda current, value=f('highpass_freq', 120.0): current.highpass(value)),
        "bandpass": lambda: RenderStep(f"bandpass(frequency_hz={f('bandpass_freq', 1200.0):.2f}, q={f('bandpass_q', 0.9):.2f})", lambda current, value=f('bandpass_freq', 1200.0), q_value=f('bandpass_q', 0.9): current.bandpass(value, q=q_value)),
        "notch": lambda: RenderStep(f"notch(frequency_hz={f('notch_freq', 3500.0):.2f}, q={f('notch_q', 2.0):.2f})", lambda current, value=f('notch_freq', 3500.0), q_value=f('notch_q', 2.0): current.notch(value, q=q_value)),
        "peak_eq": lambda: RenderStep(f"peak_eq(frequency_hz={f('peak_eq_freq', 2800.0):.2f}, gain_db={f('peak_eq_gain_db', 2.5):.2f})", lambda current, value=f('peak_eq_freq', 2800.0), gain_value=f('peak_eq_gain_db', 2.5): current.peak_eq(value, gain_value)),
        "low_shelf": lambda: RenderStep(f"low_shelf(frequency_hz={f('low_shelf_freq', 120.0):.2f}, gain_db={f('low_shelf_gain_db', 2.0):.2f})", lambda current, value=f('low_shelf_freq', 120.0), gain_value=f('low_shelf_gain_db', 2.0): current.low_shelf(value, gain_value)),
        "high_shelf": lambda: RenderStep(f"high_shelf(frequency_hz={f('high_shelf_freq', 9000.0):.2f}, gain_db={f('high_shelf_gain_db', 1.8):.2f})", lambda current, value=f('high_shelf_freq', 9000.0), gain_value=f('high_shelf_gain_db', 1.8): current.high_shelf(value, gain_value)),
        "graphic_eq": lambda: RenderStep("graphic_eq(...)", lambda current: current.graphic_eq({100.0: f("geq_100", 0.0), 250.0: f("geq_250", 0.0), 1000.0: f("geq_1000", 0.0), 4000.0: f("geq_4000", 0.0), 12000.0: f("geq_12000", 0.0)})),
        "resonant_filter": lambda: RenderStep(f"resonant_filter(frequency_hz={f('resonant_freq', 1200.0):.2f}, resonance={f('resonant_q', 2.4):.2f})", lambda current, value=f('resonant_freq', 1200.0), q_value=f('resonant_q', 2.4): current.resonant_filter(value, resonance=q_value)),
        "dynamic_eq": lambda: RenderStep(f"dynamic_eq(frequency_hz={f('dynamic_eq_freq', 2800.0):.2f}, threshold_db={f('dynamic_eq_threshold_db', -24.0):.2f}, cut_db={f('dynamic_eq_cut_db', -6.0):.2f})", lambda current, freq=f('dynamic_eq_freq', 2800.0), threshold=f('dynamic_eq_threshold_db', -24.0), cut=f('dynamic_eq_cut_db', -6.0): current.dynamic_eq(freq, threshold_db=threshold, cut_db=cut)),
        "formant_filter": lambda: RenderStep(f"formant_filter(morph={f('formant_morph', 0.0):.2f}, intensity={f('formant_intensity', 1.0):.2f})", lambda current, morph=f('formant_morph', 0.0), intensity=f('formant_intensity', 1.0): current.formant_filter(morph, intensity=intensity)),
        "stereo_width": lambda: RenderStep(f"stereo_width(width={f('stereo_width_amount', 1.2):.2f})", lambda current, value=f('stereo_width_amount', 1.2): current.stereo_width(value)),
        "delay": lambda: RenderStep(f"delay(delay_ms={f('delay_ms', 135.0):.2f}, feedback={f('delay_feedback', 0.28):.2f}, mix={f('delay_mix', 0.18):.2f})", lambda current, delay_value=f('delay_ms', 135.0), feedback_value=f('delay_feedback', 0.28), mix_value=f('delay_mix', 0.18): current.delay(delay_value, feedback=feedback_value, mix=mix_value)),
        "feedback_delay": lambda: RenderStep(f"feedback_delay(delay_ms={f('feedback_delay_ms', 240.0):.2f}, feedback={f('feedback_delay_feedback', 0.62):.2f}, mix={f('feedback_delay_mix', 0.35):.2f})", lambda current, delay_value=f('feedback_delay_ms', 240.0), feedback_value=f('feedback_delay_feedback', 0.62), mix_value=f('feedback_delay_mix', 0.35): current.feedback_delay(delay_value, feedback=feedback_value, mix=mix_value)),
        "echo": lambda: RenderStep(f"echo(delay_ms={f('echo_delay_ms', 320.0):.2f}, feedback={f('echo_feedback', 0.38):.2f}, mix={f('echo_mix', 0.28):.2f})", lambda current, delay_value=f('echo_delay_ms', 320.0), feedback_value=f('echo_feedback', 0.38), mix_value=f('echo_mix', 0.28): current.echo(delay_ms=delay_value, feedback=feedback_value, mix=mix_value)),
        "ping_pong_delay": lambda: RenderStep(f"ping_pong_delay(delay_ms={f('ping_pong_delay_ms', 220.0):.2f}, feedback={f('ping_pong_feedback', 0.58):.2f}, mix={f('ping_pong_mix', 0.30):.2f})", lambda current, delay_value=f('ping_pong_delay_ms', 220.0), feedback_value=f('ping_pong_feedback', 0.58), mix_value=f('ping_pong_mix', 0.30): current.ping_pong_delay(delay_value, feedback=feedback_value, mix=mix_value)),
        "multi_tap_delay": lambda: RenderStep(f"multi_tap_delay(delay_ms={f('multi_tap_delay_ms', 110.0):.2f}, taps={i('multi_tap_taps', 4)}, mix={f('multi_tap_mix', 0.32):.2f})", lambda current, delay_value=f('multi_tap_delay_ms', 110.0), taps_value=i('multi_tap_taps', 4), mix_value=f('multi_tap_mix', 0.32): current.multi_tap_delay(delay_ms=delay_value, taps=taps_value, mix=mix_value)),
        "slapback": lambda: RenderStep(f"slapback(delay_ms={f('slapback_delay_ms', 92.0):.2f}, mix={f('slapback_mix', 0.22):.2f})", lambda current, delay_value=f('slapback_delay_ms', 92.0), mix_value=f('slapback_mix', 0.22): current.slapback(delay_ms=delay_value, mix=mix_value)),
        "early_reflections": lambda: RenderStep(f"early_reflections(taps={i('early_reflections_taps', 6)}, mix={f('early_reflections_mix', 0.18):.2f})", lambda current, taps_value=i('early_reflections_taps', 6), mix_value=f('early_reflections_mix', 0.18): current.early_reflections(taps=taps_value, mix=mix_value)),
        "room_reverb": lambda: RenderStep(f"room_reverb(decay_seconds={f('room_decay_seconds', 0.8):.2f}, mix={f('room_mix', 0.22):.2f})", lambda current, decay_value=f('room_decay_seconds', 0.8), mix_value=f('room_mix', 0.22): current.room_reverb(decay_seconds=decay_value, mix=mix_value)),
        "hall_reverb": lambda: RenderStep(f"hall_reverb(decay_seconds={f('hall_decay_seconds', 1.9):.2f}, mix={f('hall_mix', 0.26):.2f})", lambda current, decay_value=f('hall_decay_seconds', 1.9), mix_value=f('hall_mix', 0.26): current.hall_reverb(decay_seconds=decay_value, mix=mix_value)),
        "plate_reverb": lambda: RenderStep(f"plate_reverb(decay_seconds={f('plate_decay_seconds', 1.2):.2f}, mix={f('plate_mix', 0.22):.2f})", lambda current, decay_value=f('plate_decay_seconds', 1.2), mix_value=f('plate_mix', 0.22): current.plate_reverb(decay_seconds=decay_value, mix=mix_value)),
        "chorus": lambda: RenderStep(f"chorus(rate_hz={f('chorus_rate_hz', 0.9):.2f}, depth_ms={f('chorus_depth_ms', 7.5):.2f}, mix={f('chorus_mix', 0.35):.2f})", lambda current, rate_value=f('chorus_rate_hz', 0.9), depth_value=f('chorus_depth_ms', 7.5), mix_value=f('chorus_mix', 0.35): current.chorus(rate_hz=rate_value, depth_ms=depth_value, mix=mix_value)),
        "flanger": lambda: RenderStep(f"flanger(rate_hz={f('flanger_rate_hz', 0.25):.2f}, depth_ms={f('flanger_depth_ms', 1.8):.2f}, mix={f('flanger_mix', 0.45):.2f})", lambda current, rate_value=f('flanger_rate_hz', 0.25), depth_value=f('flanger_depth_ms', 1.8), mix_value=f('flanger_mix', 0.45): current.flanger(rate_hz=rate_value, depth_ms=depth_value, mix=mix_value)),
        "phaser": lambda: RenderStep(f"phaser(rate_hz={f('phaser_rate_hz', 0.35):.2f}, depth={f('phaser_depth', 0.75):.2f}, mix={f('phaser_mix', 0.50):.2f})", lambda current, rate_value=f('phaser_rate_hz', 0.35), depth_value=f('phaser_depth', 0.75), mix_value=f('phaser_mix', 0.50): current.phaser(rate_hz=rate_value, depth=depth_value, mix=mix_value)),
        "tremolo": lambda: RenderStep(f"tremolo(rate_hz={f('tremolo_rate_hz', 5.0):.2f}, depth={f('tremolo_depth', 0.50):.2f})", lambda current, rate_value=f('tremolo_rate_hz', 5.0), depth_value=f('tremolo_depth', 0.50): current.tremolo(rate_value, depth=depth_value)),
        "vibrato": lambda: RenderStep(f"vibrato(rate_hz={f('vibrato_rate_hz', 5.0):.2f}, depth_ms={f('vibrato_depth_ms', 3.5):.2f})", lambda current, rate_value=f('vibrato_rate_hz', 5.0), depth_value=f('vibrato_depth_ms', 3.5): current.vibrato(rate_hz=rate_value, depth_ms=depth_value)),
        "auto_pan": lambda: RenderStep(f"auto_pan(rate_hz={f('auto_pan_rate_hz', 0.35):.2f}, depth={f('auto_pan_depth', 1.0):.2f})", lambda current, rate_value=f('auto_pan_rate_hz', 0.35), depth_value=f('auto_pan_depth', 1.0): current.auto_pan(rate_hz=rate_value, depth=depth_value)),
        "rotary_speaker": lambda: RenderStep(f"rotary_speaker(rate_hz={f('rotary_rate_hz', 0.8):.2f}, depth={f('rotary_depth', 0.7):.2f}, mix={f('rotary_mix', 0.65):.2f})", lambda current, rate_value=f('rotary_rate_hz', 0.8), depth_value=f('rotary_depth', 0.7), mix_value=f('rotary_mix', 0.65): current.rotary_speaker(rate_hz=rate_value, depth=depth_value, mix=mix_value)),
        "ring_modulation": lambda: RenderStep(f"ring_modulation(frequency_hz={f('ring_frequency_hz', 30.0):.2f}, mix={f('ring_mix', 0.5):.2f})", lambda current, freq=f('ring_frequency_hz', 30.0), mix_value=f('ring_mix', 0.5): current.ring_modulation(frequency_hz=freq, mix=mix_value)),
        "frequency_shifter": lambda: RenderStep(f"frequency_shifter(shift_hz={f('shifter_hz', 120.0):.2f}, mix={f('shifter_mix', 1.0):.2f})", lambda current, shift=f('shifter_hz', 120.0), mix_value=f('shifter_mix', 1.0): current.frequency_shifter(shift_hz=shift, mix=mix_value)),
        "overdrive": lambda: RenderStep(f"overdrive(drive={f('overdrive_drive', 1.8):.2f}, tone={f('overdrive_tone', 0.55):.2f}, mix={f('overdrive_mix', 1.0):.2f})", lambda current, drive_value=f('overdrive_drive', 1.8), tone_value=f('overdrive_tone', 0.55), mix_value=f('overdrive_mix', 1.0): current.overdrive(drive=drive_value, tone=tone_value, mix=mix_value)),
        "fuzz": lambda: RenderStep(f"fuzz(drive={f('fuzz_drive', 3.6):.2f}, bias={f('fuzz_bias', 0.12):.2f}, mix={f('fuzz_mix', 1.0):.2f})", lambda current, drive_value=f('fuzz_drive', 3.6), bias_value=f('fuzz_bias', 0.12), mix_value=f('fuzz_mix', 1.0): current.fuzz(drive=drive_value, bias=bias_value, mix=mix_value)),
        "bitcrusher": lambda: RenderStep(f"bitcrusher(bit_depth={i('bitcrusher_bits', 8)}, sample_rate_reduction={i('bitcrusher_reduction', 4)}, mix={f('bitcrusher_mix', 1.0):.2f})", lambda current, bits_value=i('bitcrusher_bits', 8), reduction_value=i('bitcrusher_reduction', 4), mix_value=f('bitcrusher_mix', 1.0): current.bitcrusher(bit_depth=bits_value, sample_rate_reduction=reduction_value, mix=mix_value)),
        "waveshaper": lambda: RenderStep(f"waveshaper(amount={f('waveshaper_amount', 1.4):.2f}, symmetry={f('waveshaper_symmetry', 0.0):.2f}, mix={f('waveshaper_mix', 1.0):.2f})", lambda current, amount_value=f('waveshaper_amount', 1.4), symmetry_value=f('waveshaper_symmetry', 0.0), mix_value=f('waveshaper_mix', 1.0): current.waveshaper(amount=amount_value, symmetry=symmetry_value, mix=mix_value)),
        "tube_saturation": lambda: RenderStep(f"tube_saturation(drive={f('tube_drive', 1.6):.2f}, bias={f('tube_bias', 0.08):.2f}, mix={f('tube_mix', 1.0):.2f})", lambda current, drive_value=f('tube_drive', 1.6), bias_value=f('tube_bias', 0.08), mix_value=f('tube_mix', 1.0): current.tube_saturation(drive=drive_value, bias=bias_value, mix=mix_value)),
        "tape_saturation": lambda: RenderStep(f"tape_saturation(drive={f('tape_drive', 1.4):.2f}, softness={f('tape_softness', 0.35):.2f}, mix={f('tape_mix', 1.0):.2f})", lambda current, drive_value=f('tape_drive', 1.4), softness_value=f('tape_softness', 0.35), mix_value=f('tape_mix', 1.0): current.tape_saturation(drive=drive_value, softness=softness_value, mix=mix_value)),
        "soft_clipping": lambda: RenderStep(f"soft_clipping(threshold={f('soft_clip_threshold', 0.85):.2f})", lambda current, threshold_value=f('soft_clip_threshold', 0.85): current.soft_clipping(threshold=threshold_value)),
        "hard_clipping": lambda: RenderStep(f"hard_clipping(threshold={f('hard_clip_threshold', 0.92):.2f})", lambda current, threshold_value=f('hard_clip_threshold', 0.92): current.hard_clipping(threshold=threshold_value)),
        "pitch_shift": lambda: RenderStep(f"pitch_shift(semitones={f('pitch_shift_semitones', 3.0):.2f})", lambda current, semitones=f('pitch_shift_semitones', 3.0): current.pitch_shift(semitones, fft_size=1536, hop_size=512)),
        "time_stretch": lambda: RenderStep(f"time_stretch(rate={f('time_stretch_rate', 0.85):.2f})", lambda current, rate_value=f('time_stretch_rate', 0.85): current.time_stretch(rate=rate_value, fft_size=1536, hop_size=512)),
        "time_compression": lambda: RenderStep(f"time_compression(rate={f('time_compression_rate', 1.18):.2f})", lambda current, rate_value=f('time_compression_rate', 1.18): current.time_compression(rate=rate_value, fft_size=1536, hop_size=512)),
        "auto_tune": lambda: RenderStep(f"auto_tune(strength={f('auto_tune_strength', 0.70):.2f})", lambda current, strength_value=f('auto_tune_strength', 0.70): current.auto_tune(strength=strength_value, fft_size=1024, hop_size=512)),
        "harmonizer": lambda: RenderStep(f"harmonizer(interval={f('harmonizer_interval', 7.0):.2f}, mix={f('harmonizer_mix', 0.35):.2f})", lambda current, interval_value=f('harmonizer_interval', 7.0), mix_value=f('harmonizer_mix', 0.35): current.harmonizer((interval_value,), mix=mix_value, fft_size=1536, hop_size=512)),
        "octaver": lambda: RenderStep(f"octaver(down_mix={f('octaver_down_mix', 0.45):.2f}, up_mix={f('octaver_up_mix', 0.0):.2f})", lambda current, down_value=f('octaver_down_mix', 0.45), up_value=f('octaver_up_mix', 0.0): current.octaver(down_mix=down_value, up_mix=up_value, fft_size=1536, hop_size=512)),
        "formant_shifting": lambda: RenderStep(f"formant_shifting(shift={f('formant_shift', 1.12):.2f}, mix={f('formant_shift_mix', 1.0):.2f})", lambda current, shift_value=f('formant_shift', 1.12), mix_value=f('formant_shift_mix', 1.0): current.formant_shifting(shift=shift_value, mix=mix_value, fft_size=1536, hop_size=512)),
        "noise_reduction": lambda: RenderStep(f"noise_reduction(strength={f('noise_reduction_strength', 0.50):.2f})", lambda current, strength_value=f('noise_reduction_strength', 0.50): current.noise_reduction(strength=strength_value, fft_size=1024, hop_size=512)),
        "voice_isolation": lambda: RenderStep(f"voice_isolation(strength={f('voice_isolation_strength', 0.75):.2f})", lambda current, strength_value=f('voice_isolation_strength', 0.75): current.voice_isolation(strength=strength_value, low_hz=140.0, high_hz=4_800.0, fft_size=1024, hop_size=512)),
        "source_separation": lambda: RenderStep(f"source_separation(strength={f('source_separation_strength', 0.80):.2f})", lambda current, strength_value=f('source_separation_strength', 0.80): current.source_separation(strength=strength_value, low_hz=140.0, high_hz=4_800.0, fft_size=1024, hop_size=512)),
        "de_reverb": lambda: RenderStep(f"de_reverb(amount={f('de_reverb_amount', 0.45):.2f})", lambda current, amount_value=f('de_reverb_amount', 0.45): current.de_reverb(amount=amount_value, fft_size=1024, hop_size=512)),
        "de_echo": lambda: RenderStep(f"de_echo(amount={f('de_echo_amount', 0.45):.2f})", lambda current, amount_value=f('de_echo_amount', 0.45): current.de_echo(amount=amount_value)),
        "spectral_repair": lambda: RenderStep(f"spectral_repair(strength={f('spectral_repair_strength', 0.35):.2f})", lambda current, strength_value=f('spectral_repair_strength', 0.35): current.spectral_repair(strength=strength_value, fft_size=1024, hop_size=512)),
        "ai_enhancer": lambda: RenderStep(f"ai_enhancer(amount={f('ai_enhancer_amount', 0.60):.2f})", lambda current, amount_value=f('ai_enhancer_amount', 0.60): current.ai_enhancer(amount=amount_value, fft_size=1024, hop_size=512)),
        "speech_enhancement": lambda: RenderStep(f"speech_enhancement(amount={f('speech_enhancement_amount', 0.70):.2f})", lambda current, amount_value=f('speech_enhancement_amount', 0.70): current.speech_enhancement(amount=amount_value, fft_size=1024, hop_size=512)),
        "glitch_effect": lambda: RenderStep(f"glitch_effect(slice_ms={f('glitch_slice_ms', 70.0):.2f}, mix={f('glitch_mix', 1.0):.2f})", lambda current, slice_value=f('glitch_slice_ms', 70.0), repeat=f('glitch_repeat', 0.22), mix_value=f('glitch_mix', 1.0): current.glitch_effect(slice_ms=slice_value, repeat_probability=repeat, mix=mix_value)),
        "stutter": lambda: RenderStep(f"stutter(slice_ms={f('stutter_slice_ms', 90.0):.2f}, repeats={i('stutter_repeats', 3)}, mix={f('stutter_mix', 1.0):.2f})", lambda current, slice_value=f('stutter_slice_ms', 90.0), repeats_value=i('stutter_repeats', 3), mix_value=f('stutter_mix', 1.0): current.stutter(slice_ms=slice_value, repeats=repeats_value, mix=mix_value)),
        "tape_stop": lambda: RenderStep(f"tape_stop(stop_time_ms={f('tape_stop_ms', 900.0):.2f}, curve={f('tape_stop_curve', 2.0):.2f}, mix={f('tape_stop_mix', 1.0):.2f})", lambda current, stop_value=f('tape_stop_ms', 900.0), curve_value=f('tape_stop_curve', 2.0), mix_value=f('tape_stop_mix', 1.0): current.tape_stop(stop_time_ms=stop_value, curve=curve_value, mix=mix_value)),
        "reverse_reverb": lambda: RenderStep(f"reverse_reverb(decay_seconds={f('reverse_reverb_decay', 1.2):.2f}, mix={f('reverse_reverb_mix', 0.45):.2f})", lambda current, decay_value=f('reverse_reverb_decay', 1.2), mix_value=f('reverse_reverb_mix', 0.45): current.reverse_reverb(decay_seconds=decay_value, mix=mix_value)),
        "granular_synthesis": lambda: RenderStep(f"granular_synthesis(grain_ms={f('granular_grain_ms', 80.0):.2f}, overlap={f('granular_overlap', 0.50):.2f}, mix={f('granular_mix', 1.0):.2f})", lambda current, grain_value=f('granular_grain_ms', 80.0), overlap_value=f('granular_overlap', 0.50), mix_value=f('granular_mix', 1.0): current.granular_synthesis(grain_ms=grain_value, overlap=overlap_value, mix=mix_value)),
        "time_slicing": lambda: RenderStep(f"time_slicing(slice_ms={f('time_slicing_ms', 120.0):.2f}, mix={f('time_slicing_mix', 1.0):.2f})", lambda current, slice_value=f('time_slicing_ms', 120.0), mix_value=f('time_slicing_mix', 1.0): current.time_slicing(slice_ms=slice_value, mix=mix_value)),
        "random_pitch_mod": lambda: RenderStep(f"random_pitch_mod(depth_semitones={f('random_pitch_depth', 2.0):.2f}, segment_ms={f('random_pitch_segment_ms', 180.0):.2f}, mix={f('random_pitch_mix', 1.0):.2f})", lambda current, depth_value=f('random_pitch_depth', 2.0), segment_value=f('random_pitch_segment_ms', 180.0), mix_value=f('random_pitch_mix', 1.0): current.random_pitch_mod(depth_semitones=depth_value, segment_ms=segment_value, mix=mix_value)),
        "vinyl_effect": lambda: RenderStep(f"vinyl_effect(noise={f('vinyl_noise', 0.08):.2f}, wow={f('vinyl_wow', 0.15):.2f}, mix={f('vinyl_mix', 1.0):.2f})", lambda current, noise_value=f('vinyl_noise', 0.08), wow_value=f('vinyl_wow', 0.15), mix_value=f('vinyl_mix', 1.0): current.vinyl_effect(noise=noise_value, wow=wow_value, mix=mix_value)),
        "radio_effect": lambda: RenderStep(f"radio_effect(noise_level={f('radio_noise', 0.04):.2f}, mix={f('radio_mix', 1.0):.2f})", lambda current, noise_value=f('radio_noise', 0.04), mix_value=f('radio_mix', 1.0): current.radio_effect(noise_level=noise_value, mix=mix_value)),
        "telephone_effect": lambda: RenderStep(f"telephone_effect(mix={f('telephone_mix', 1.0):.2f})", lambda current, mix_value=f('telephone_mix', 1.0): current.telephone_effect(mix=mix_value)),
        "retro_8bit": lambda: RenderStep(f"retro_8bit(bit_depth={i('retro_bits', 6)}, sample_rate_reduction={i('retro_hold', 8)}, mix={f('retro_mix', 1.0):.2f})", lambda current, bits_value=i('retro_bits', 6), hold_value=i('retro_hold', 8), mix_value=f('retro_mix', 1.0): current.retro_8bit(bit_depth=bits_value, sample_rate_reduction=hold_value, mix=mix_value)),
        "slow_motion_extreme": lambda: RenderStep(f"slow_motion_extreme(rate={f('slow_motion_rate', 0.45):.2f}, tone_hz={f('slow_motion_tone_hz', 4800.0):.2f})", lambda current, rate_value=f('slow_motion_rate', 0.45), tone_value=f('slow_motion_tone_hz', 4800.0): current.slow_motion_extreme(rate=rate_value, tone_hz=tone_value)),
        "robot_voice": lambda: RenderStep(f"robot_voice(carrier_hz={f('robot_carrier_hz', 70.0):.2f}, mix={f('robot_mix', 0.85):.2f})", lambda current, carrier_value=f('robot_carrier_hz', 70.0), mix_value=f('robot_mix', 0.85): current.robot_voice(carrier_hz=carrier_value, mix=mix_value)),
        "alien_voice": lambda: RenderStep(f"alien_voice(shift_semitones={f('alien_shift', 5.0):.2f}, formant_shift={f('alien_formant', 1.18):.2f}, mix={f('alien_mix', 0.80):.2f})", lambda current, shift_value=f('alien_shift', 5.0), formant_value=f('alien_formant', 1.18), mix_value=f('alien_mix', 0.80): current.alien_voice(shift_semitones=shift_value, formant_shift=formant_value, mix=mix_value)),
        "fft_filter": lambda: RenderStep(f"fft_filter(low_hz={f('fft_filter_low_hz', 80.0):.2f}, high_hz={f('fft_filter_high_hz', 12000.0):.2f}, mix={f('fft_filter_mix', 1.0):.2f})", lambda current, low_value=f('fft_filter_low_hz', 80.0), high_value=f('fft_filter_high_hz', 12000.0), mix_value=f('fft_filter_mix', 1.0): current.fft_filter(low_hz=low_value, high_hz=high_value, mix=mix_value, fft_size=1024, hop_size=512)),
        "spectral_gating": lambda: RenderStep(f"spectral_gating(threshold_db={f('spectral_gate_threshold_db', -42.0):.2f}, floor={f('spectral_gate_floor', 0.08):.2f})", lambda current, threshold_value=f('spectral_gate_threshold_db', -42.0), floor_value=f('spectral_gate_floor', 0.08): current.spectral_gating(threshold_db=threshold_value, floor=floor_value, fft_size=1024, hop_size=512)),
        "spectral_blur": lambda: RenderStep(f"spectral_blur(amount={f('spectral_blur_amount', 0.45):.2f})", lambda current, amount_value=f('spectral_blur_amount', 0.45): current.spectral_blur(amount=amount_value, fft_size=1024, hop_size=512)),
        "spectral_freeze": lambda: RenderStep(f"spectral_freeze(start_ms={f('spectral_freeze_start_ms', 120.0):.2f}, mix={f('spectral_freeze_mix', 0.70):.2f})", lambda current, start_value=f('spectral_freeze_start_ms', 120.0), mix_value=f('spectral_freeze_mix', 0.70): current.spectral_freeze(start_ms=start_value, mix=mix_value, fft_size=1024, hop_size=512)),
        "spectral_morphing": lambda: RenderStep(f"spectral_morphing(amount={f('spectral_morph_amount', 0.50):.2f})", lambda current, amount_value=f('spectral_morph_amount', 0.50): current.spectral_morphing(amount=amount_value, fft_size=1024, hop_size=512)),
        "phase_vocoder": lambda: RenderStep(f"phase_vocoder(rate={f('phase_vocoder_rate', 0.85):.2f})", lambda current, rate_value=f('phase_vocoder_rate', 0.85): current.phase_vocoder(rate=rate_value, fft_size=1536, hop_size=512)),
        "harmonic_percussive_separation": lambda: RenderStep(f"harmonic_percussive_separation(target='harmonic', mix={f('hps_mix', 1.0):.2f})", lambda current, mix_value=f('hps_mix', 1.0): current.harmonic_percussive_separation(target='harmonic', mix=mix_value, fft_size=1024, hop_size=512)),
        "spectral_delay": lambda: RenderStep(f"spectral_delay(max_delay_ms={f('spectral_delay_ms', 240.0):.2f}, feedback={f('spectral_delay_feedback', 0.15):.2f}, mix={f('spectral_delay_mix', 0.35):.2f})", lambda current, delay_value=f('spectral_delay_ms', 240.0), feedback_value=f('spectral_delay_feedback', 0.15), mix_value=f('spectral_delay_mix', 0.35): current.spectral_delay(max_delay_ms=delay_value, feedback=feedback_value, mix=mix_value, fft_size=1024, hop_size=512)),
        "stereo_widening": lambda: RenderStep(f"stereo_widening(amount={f('stereo_widening_amount', 1.25):.2f})", lambda current, amount_value=f('stereo_widening_amount', 1.25): current.stereo_widening(amount_value)),
        "mid_side_processing": lambda: RenderStep(f"mid_side_processing(mid_gain_db={f('mid_gain_db', 0.0):.2f}, side_gain_db={f('side_gain_db', 1.5):.2f})", lambda current, mid_value=f('mid_gain_db', 0.0), side_value=f('side_gain_db', 1.5): current.mid_side_processing(mid_gain_db=mid_value, side_gain_db=side_value)),
        "stereo_imager": lambda: RenderStep(f"stereo_imager(low_width={f('stereo_imager_low', 0.90):.2f}, high_width={f('stereo_imager_high', 1.35):.2f})", lambda current, low_value=f('stereo_imager_low', 0.90), high_value=f('stereo_imager_high', 1.35): current.stereo_imager(low_width=low_value, high_width=high_value)),
        "binaural_effect": lambda: RenderStep(f"binaural_effect(azimuth_deg={f('binaural_azimuth', 25.0):.2f}, distance={f('binaural_distance', 1.0):.2f}, room_mix={f('binaural_room_mix', 0.08):.2f})", lambda current, azimuth_value=f('binaural_azimuth', 25.0), distance_value=f('binaural_distance', 1.0), room_value=f('binaural_room_mix', 0.08): current.binaural_effect(azimuth_deg=azimuth_value, distance=distance_value, room_mix=room_value)),
        "spatial_positioning": lambda: RenderStep(f"spatial_positioning(azimuth_deg={f('spatial_azimuth', 25.0):.2f}, elevation_deg={f('spatial_elevation', 0.0):.2f}, distance={f('spatial_distance', 1.0):.2f})", lambda current, azimuth_value=f('spatial_azimuth', 25.0), elevation_value=f('spatial_elevation', 0.0), distance_value=f('spatial_distance', 1.0): current.spatial_positioning(azimuth_deg=azimuth_value, elevation_deg=elevation_value, distance=distance_value)),
        "hrtf_simulation": lambda: RenderStep(f"hrtf_simulation(azimuth_deg={f('hrtf_azimuth', 30.0):.2f}, elevation_deg={f('hrtf_elevation', 0.0):.2f}, distance={f('hrtf_distance', 1.0):.2f})", lambda current, azimuth_value=f('hrtf_azimuth', 30.0), elevation_value=f('hrtf_elevation', 0.0), distance_value=f('hrtf_distance', 1.0): current.hrtf_simulation(azimuth_deg=azimuth_value, elevation_deg=elevation_value, distance=distance_value)),
        "resample": lambda: RenderStep(f"resample(sample_rate={i('utility_resample_rate', 48000)})", lambda current, rate_value=i('utility_resample_rate', 48000): current.resample(rate_value)),
        "dither": lambda: RenderStep(f"dither(bit_depth={i('utility_dither_bits', 16)})", lambda current, bit_depth_value=i('utility_dither_bits', 16): current.dither(bit_depth=bit_depth_value)),
        "bit_depth_conversion": lambda: RenderStep(f"bit_depth_conversion(bit_depth={i('utility_bit_depth', 16)})", lambda current, bit_depth_value=i('utility_bit_depth', 16): current.bit_depth_conversion(bit_depth=bit_depth_value)),
        "loudness_normalization": lambda: RenderStep(f"loudness_normalization(target_lufs={f('utility_target_lufs', -16.0):.2f})", lambda current, target_value=f('utility_target_lufs', -16.0): current.loudness_normalization(target_lufs=target_value)),
    }
    for key, factory in tone_map.items():
        if key in request.form:
            steps.append(factory())

    if "convolution_reverb" in request.form:
        mix = f("convolution_mix", 0.24)
        ir_path = save_optional_upload("impulse_response", uid, "ir")
        impulse_response = ir_path.as_posix() if ir_path is not None else default_ir(clip.sample_rate, clip.channels)
        steps.append(RenderStep(f"convolution_reverb(mix={mix:.2f})", lambda current, ir=impulse_response, mix_value=mix: current.convolution_reverb(ir, mix=mix_value)))
    return steps


@app.route("/")
def index():
    return render_template(
        TEMPLATE_NAME,
        effect_groups=EFFECT_GROUPS,
        effect_count=len(effect_names()),
        presets=preset_names(),
        formats=sorted(FORMAT_CAPABILITIES),
        caps=json.dumps(FORMAT_CAPABILITIES),
    )


@app.route("/process", methods=["POST"])
def process():
    try:
        uploads, outputs = ensure_runtime_dirs()
        total_started = time.perf_counter()
        if "audio" not in request.files or request.files["audio"].filename == "":
            return "<div class='warn'>No audio file was uploaded.</div>"
        file = request.files["audio"]
        uid = str(uuid.uuid4())
        ext = Path(file.filename).suffix.lower() or ".wav"
        input_path = uploads / f"{uid}{ext}"
        file.save(input_path)
        if not input_path.exists() or input_path.stat().st_size == 0:
            return "<div class='warn'>Failed to save the input file.</div>"

        decode_started = time.perf_counter()
        clip = AudioClip.from_file(input_path)
        decode_elapsed = time.perf_counter() - decode_started
        include_envelope = "analysis_envelope" in request.form
        attack_ms = f("analysis_attack_ms", 10.0)
        release_ms = f("analysis_release_ms", 80.0)

        crossfade_clip = None
        timings = [f"decode_input: {decode_elapsed * 1000.0:.2f} ms"]
        input_metrics = metric_lines(
            clip,
            include_envelope=include_envelope,
            attack_ms=attack_ms,
            release_ms=release_ms,
        )
        if "crossfade" in request.form:
            crossfade_path = save_optional_upload("crossfade_audio", uid, "crossfade")
            if crossfade_path is None:
                return "<div class='warn'>Crossfade was enabled, but the second audio file was not uploaded.</div>"
            second_started = time.perf_counter()
            crossfade_clip = AudioClip.from_file(crossfade_path, sample_rate=clip.sample_rate)
            timings.append(f"decode_crossfade: {(time.perf_counter() - second_started) * 1000.0:.2f} ms")

        current = clip
        for index, step in enumerate(build_steps(uid, clip, crossfade_clip)):
            started = time.perf_counter()
            current = step.apply(current)
            timings.append(f"[{index}] {step.label} -> {(time.perf_counter() - started) * 1000.0:.2f} ms")

        if request.form.get("normalize_enabled", "yes") == "yes":
            normalize_headroom_db = f("normalize_headroom_db", 1.0)
            started = time.perf_counter()
            current = current.normalize(headroom_db=normalize_headroom_db)  # type: ignore[assignment]
            timings.append(f"[{len(timings) - 1}] normalize(headroom_db={normalize_headroom_db:.2f}) -> {(time.perf_counter() - started) * 1000.0:.2f} ms")

        fmt = request.form.get("format", "wav")
        bitrate = request.form.get("bitrate") or None
        sample_rate = request.form.get("sample_rate") or None
        channels = request.form.get("channels") or None
        settings = prepare_export_settings(outputs / f"{uid}.{fmt}", format=fmt, bitrate=bitrate)
        output_name = f"{uid}.{settings.format}"
        output_path = outputs / output_name
        export_started = time.perf_counter()
        current.export(output_path, format=settings.format, bitrate=settings.bitrate, sample_rate=int(sample_rate) if sample_rate else None, channels=int(channels) if channels else None)
        timings.append(f"export: {(time.perf_counter() - export_started) * 1000.0:.2f} ms")
        timings.append(f"total: {(time.perf_counter() - total_started) * 1000.0:.2f} ms")
        output_metrics = metric_lines(
            current,
            include_envelope=include_envelope,
            attack_ms=attack_ms,
            release_ms=release_ms,
        )

        mime = str(FORMAT_CAPABILITIES.get(settings.format, {}).get("mime", "audio/wav"))
        warnings = "".join(f"<div class='warn'>{escape(w)}</div>" for w in settings.warnings)
        debug = (
            "Input metrics\n"
            + "\n".join(input_metrics)
            + "\n\nTimings by stage\n"
            + "\n".join(timings)
            + "\n\nPipeline final\n"
            + current.pipeline_info()
            + "\n\nOutput metrics\n"
            + "\n".join(output_metrics)
        )
        return f"<div class='badge'>Render complete</div>{warnings}<audio controls><source src='/download/{output_name}' type='{mime}'></audio><p><a class='btn' href='/download/{output_name}'>Download file</a></p><pre>{escape(debug)}</pre>"
    except Exception as exc:
        return f"<div class='warn'>Processing error: {escape(str(exc))}</div>"


@app.route("/download/<filename>")
def download(filename: str):
    _, outputs = ensure_runtime_dirs()
    return send_file(outputs / filename)


if __name__ == "__main__":
    app.run(debug=True)

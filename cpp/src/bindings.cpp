#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "voxis/dsp.hpp"

namespace py = pybind11;

namespace {

float get_float(const py::dict& spec, const char* key, float fallback) {
    const py::str key_obj(key);
    if (!spec.contains(key_obj)) {
        return fallback;
    }
    return py::cast<float>(spec[key_obj]);
}

int get_int(const py::dict& spec, const char* key, int fallback) {
    const py::str key_obj(key);
    if (!spec.contains(key_obj)) {
        return fallback;
    }
    return py::cast<int>(spec[key_obj]);
}

std::unique_ptr<voxis::Effect> make_filter_effect(
    voxis::FilterKind kind,
    const py::dict& spec,
    int sample_rate,
    int channels,
    float default_frequency_hz,
    float default_q,
    float default_gain_db,
    float default_slope) {
    return std::make_unique<voxis::FilterEffect>(
        kind,
        static_cast<float>(sample_rate),
        channels,
        get_float(spec, "frequency_hz", default_frequency_hz),
        get_float(spec, "q", default_q),
        get_float(spec, "gain_db", default_gain_db),
        get_float(spec, "slope", default_slope),
        get_int(spec, "stages", 1));
}

std::unique_ptr<voxis::Effect> make_effect(const py::dict& spec, int sample_rate, int channels) {
    if (!spec.contains("type")) {
        throw std::runtime_error("Effect spec is missing the 'type' field.");
    }

    const auto type = py::cast<std::string>(spec["type"]);

    if (type == "gain") {
        return std::make_unique<voxis::GainEffect>(get_float(spec, "db", 0.0f));
    }
    if (type == "clip") {
        return std::make_unique<voxis::ClipEffect>(get_float(spec, "threshold", 0.98f));
    }
    if (type == "distortion") {
        return std::make_unique<voxis::DistortionEffect>(get_float(spec, "drive", 2.0f));
    }
    if (type == "tremolo") {
        return std::make_unique<voxis::TremoloEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "rate_hz", 5.0f),
            get_float(spec, "depth", 0.5f));
    }
    if (type == "delay") {
        return std::make_unique<voxis::DelayEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "delay_ms", 150.0f),
            get_float(spec, "feedback", 0.35f),
            get_float(spec, "mix", 0.2f));
    }
    if (type == "ping_pong_delay") {
        return std::make_unique<voxis::PingPongDelayEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "delay_ms", 180.0f),
            get_float(spec, "feedback", 0.55f),
            get_float(spec, "mix", 0.3f));
    }
    if (type == "chorus") {
        return std::make_unique<voxis::ModulatedDelayEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "delay_ms", 18.0f),
            get_float(spec, "depth_ms", 7.5f),
            get_float(spec, "rate_hz", 0.9f),
            get_float(spec, "mix", 0.35f),
            get_float(spec, "feedback", 0.12f));
    }
    if (type == "flanger") {
        return std::make_unique<voxis::ModulatedDelayEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "delay_ms", 2.5f),
            get_float(spec, "depth_ms", 1.8f),
            get_float(spec, "rate_hz", 0.25f),
            get_float(spec, "mix", 0.45f),
            get_float(spec, "feedback", 0.35f));
    }
    if (type == "vibrato") {
        return std::make_unique<voxis::ModulatedDelayEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "delay_ms", 5.5f),
            get_float(spec, "depth_ms", 3.5f),
            get_float(spec, "rate_hz", 5.0f),
            get_float(spec, "mix", 1.0f),
            get_float(spec, "feedback", 0.0f),
            true);
    }
    if (type == "auto_pan") {
        return std::make_unique<voxis::AutoPanEffect>(
            static_cast<float>(sample_rate),
            get_float(spec, "rate_hz", 0.35f),
            get_float(spec, "depth", 1.0f));
    }
    if (type == "phaser") {
        return std::make_unique<voxis::PhaserEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "rate_hz", 0.35f),
            get_float(spec, "depth", 0.75f),
            get_float(spec, "center_hz", 900.0f),
            get_float(spec, "feedback", 0.2f),
            get_float(spec, "mix", 0.5f),
            get_int(spec, "stages", 4));
    }
    if (type == "dynamic_eq") {
        return std::make_unique<voxis::DynamicEQEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "frequency_hz", 2'800.0f),
            get_float(spec, "threshold_db", -24.0f),
            get_float(spec, "cut_db", -6.0f),
            get_float(spec, "q", 1.2f),
            get_float(spec, "attack_ms", 10.0f),
            get_float(spec, "release_ms", 120.0f));
    }
    if (type == "rotary_speaker") {
        return std::make_unique<voxis::RotarySpeakerEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "rate_hz", 0.8f),
            get_float(spec, "depth", 0.7f),
            get_float(spec, "mix", 0.65f),
            get_float(spec, "crossover_hz", 900.0f));
    }
    if (type == "lowpass") {
        return make_filter_effect(
            voxis::FilterKind::Lowpass,
            spec,
            sample_rate,
            channels,
            8'000.0f,
            0.70710678f,
            0.0f,
            1.0f);
    }
    if (type == "highpass") {
        return make_filter_effect(
            voxis::FilterKind::Highpass,
            spec,
            sample_rate,
            channels,
            120.0f,
            0.70710678f,
            0.0f,
            1.0f);
    }
    if (type == "bandpass") {
        return make_filter_effect(
            voxis::FilterKind::Bandpass,
            spec,
            sample_rate,
            channels,
            1'200.0f,
            0.70710678f,
            0.0f,
            1.0f);
    }
    if (type == "notch") {
        return make_filter_effect(
            voxis::FilterKind::Notch,
            spec,
            sample_rate,
            channels,
            1'200.0f,
            0.70710678f,
            0.0f,
            1.0f);
    }
    if (type == "peak_eq") {
        return make_filter_effect(
            voxis::FilterKind::Peak,
            spec,
            sample_rate,
            channels,
            1'000.0f,
            1.0f,
            0.0f,
            1.0f);
    }
    if (type == "low_shelf") {
        return make_filter_effect(
            voxis::FilterKind::LowShelf,
            spec,
            sample_rate,
            channels,
            120.0f,
            0.70710678f,
            0.0f,
            1.0f);
    }
    if (type == "high_shelf") {
        return make_filter_effect(
            voxis::FilterKind::HighShelf,
            spec,
            sample_rate,
            channels,
            8'000.0f,
            0.70710678f,
            0.0f,
            1.0f);
    }
    if (type == "compressor") {
        return std::make_unique<voxis::CompressorEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "threshold_db", -18.0f),
            get_float(spec, "ratio", 4.0f),
            get_float(spec, "attack_ms", 10.0f),
            get_float(spec, "release_ms", 80.0f),
            get_float(spec, "makeup_db", 0.0f));
    }
    if (type == "upward_compression") {
        return std::make_unique<voxis::UpwardCompressorEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "threshold_db", -42.0f),
            get_float(spec, "ratio", 2.0f),
            get_float(spec, "attack_ms", 12.0f),
            get_float(spec, "release_ms", 120.0f),
            get_float(spec, "max_gain_db", 18.0f));
    }
    if (type == "limiter") {
        return std::make_unique<voxis::LimiterEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "ceiling_db", -1.0f),
            get_float(spec, "attack_ms", 1.0f),
            get_float(spec, "release_ms", 60.0f));
    }
    if (type == "expander") {
        return std::make_unique<voxis::ExpanderEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "threshold_db", -35.0f),
            get_float(spec, "ratio", 2.0f),
            get_float(spec, "attack_ms", 8.0f),
            get_float(spec, "release_ms", 80.0f),
            get_float(spec, "makeup_db", 0.0f));
    }
    if (type == "noise_gate") {
        return std::make_unique<voxis::NoiseGateEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "threshold_db", -45.0f),
            get_float(spec, "attack_ms", 3.0f),
            get_float(spec, "release_ms", 60.0f),
            get_float(spec, "floor_db", -80.0f));
    }
    if (type == "deesser") {
        return std::make_unique<voxis::DeEsserEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "frequency_hz", 6'500.0f),
            get_float(spec, "threshold_db", -28.0f),
            get_float(spec, "ratio", 4.0f),
            get_float(spec, "attack_ms", 2.0f),
            get_float(spec, "release_ms", 60.0f),
            get_float(spec, "amount", 1.0f));
    }
    if (type == "transient_shaper") {
        return std::make_unique<voxis::TransientShaperEffect>(
            static_cast<float>(sample_rate),
            channels,
            get_float(spec, "attack", 0.7f),
            get_float(spec, "sustain", 0.2f),
            get_float(spec, "attack_ms", 18.0f),
            get_float(spec, "release_ms", 120.0f));
    }
    if (type == "pan") {
        return std::make_unique<voxis::PanEffect>(get_float(spec, "position", 0.0f));
    }
    if (type == "stereo_width") {
        return std::make_unique<voxis::StereoWidthEffect>(get_float(spec, "width", 1.0f));
    }

    throw std::runtime_error("Unknown effect type: " + type);
}

py::array_t<float> process_pipeline(
    const py::array_t<float, py::array::c_style | py::array::forcecast>& input,
    int sample_rate,
    const py::list& specs,
    std::size_t block_size,
    unsigned int workers) {
    if (input.ndim() != 2) {
        throw std::runtime_error("Audio buffers must have exactly 2 dimensions: (frames, channels).");
    }

    if (sample_rate <= 0) {
        throw std::runtime_error("sample_rate must be positive.");
    }

    const auto frames = static_cast<std::size_t>(input.shape(0));
    const auto channels = static_cast<int>(input.shape(1));
    if (channels <= 0) {
        throw std::runtime_error("Audio buffers must have at least one channel.");
    }

    if (block_size == 0) {
        block_size = 2048;
    }
    if (workers == 0) {
        workers = 1;
    }

    py::array_t<float> output({input.shape(0), input.shape(1)});
    auto input_buffer = input.request();
    auto output_buffer = output.request();
    std::memcpy(output_buffer.ptr, input_buffer.ptr, static_cast<std::size_t>(input_buffer.size) * sizeof(float));

    std::vector<std::unique_ptr<voxis::Effect>> effects;
    effects.reserve(specs.size());
    for (const auto& spec_handle : specs) {
        effects.push_back(make_effect(py::cast<py::dict>(spec_handle), sample_rate, channels));
    }

    auto* data = static_cast<float*>(output_buffer.ptr);
    {
        py::gil_scoped_release release;
        for (auto& effect : effects) {
            effect->process(data, frames, channels, block_size, workers);
        }
    }

    return output;
}

}  // namespace

PYBIND11_MODULE(_voxis_core, module) {
    module.doc() = "Native DSP core for Voxis.";
    module.def(
        "process_pipeline",
        &process_pipeline,
        py::arg("input"),
        py::arg("sample_rate"),
        py::arg("specs"),
        py::arg("block_size") = 2048,
        py::arg("workers") = 1);
}


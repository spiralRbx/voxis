#pragma once

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <thread>
#include <vector>

namespace voxis {

constexpr float kPi = 3.14159265358979323846f;

inline float clamp_unit(float value) {
    return std::clamp(value, 0.0f, 1.0f);
}

inline float clamp_signed_unit(float value) {
    return std::clamp(value, -1.0f, 1.0f);
}

inline float db_to_linear(float db) {
    return std::pow(10.0f, db / 20.0f);
}

inline float positive_time_ms(float value) {
    return std::max(value, 0.001f);
}

inline float positive_q(float value) {
    return std::max(value, 0.001f);
}

inline float positive_slope(float value) {
    return std::max(value, 0.001f);
}

inline std::size_t wrap_index(long long index, std::size_t length) {
    const auto size = static_cast<long long>(length);
    long long wrapped = index % size;
    if (wrapped < 0) {
        wrapped += size;
    }
    return static_cast<std::size_t>(wrapped);
}

inline float advance_phase(float phase, float step) {
    phase += step;
    if (phase >= 2.0f * kPi) {
        phase -= 2.0f * kPi;
        if (phase >= 2.0f * kPi) {
            phase = std::fmod(phase, 2.0f * kPi);
        }
    }
    return phase;
}

inline float linear_read(const std::vector<float>& line, std::size_t write_index, float delay_samples) {
    const float read_position = static_cast<float>(write_index) - delay_samples;
    const float base_position = std::floor(read_position);
    const auto base_index = static_cast<long long>(base_position);
    const float fraction = read_position - base_position;
    const float newer = line[wrap_index(base_index, line.size())];
    const float older = line[wrap_index(base_index - 1, line.size())];
    return newer * (1.0f - fraction) + older * fraction;
}

template <typename Fn>
void parallel_for_channels(int channels, unsigned int workers, Fn&& fn) {
    if (channels <= 1 || workers <= 1) {
        fn(0, channels);
        return;
    }

    const unsigned int thread_count =
        std::min<unsigned int>(workers, static_cast<unsigned int>(channels));
    if (thread_count <= 1) {
        fn(0, channels);
        return;
    }

    std::vector<std::thread> threads;
    threads.reserve(thread_count);

    int start = 0;
    const int base = channels / static_cast<int>(thread_count);
    const int remainder = channels % static_cast<int>(thread_count);

    for (unsigned int thread_index = 0; thread_index < thread_count; ++thread_index) {
        const int width = base + (thread_index < static_cast<unsigned int>(remainder) ? 1 : 0);
        const int channel_begin = start;
        const int channel_end = channel_begin + width;
        start = channel_end;
        threads.emplace_back([&, channel_begin, channel_end]() { fn(channel_begin, channel_end); });
    }

    for (auto& thread : threads) {
        thread.join();
    }
}

struct BiquadCoefficients {
    float b0 = 1.0f;
    float b1 = 0.0f;
    float b2 = 0.0f;
    float a1 = 0.0f;
    float a2 = 0.0f;
};

struct BiquadState {
    float z1 = 0.0f;
    float z2 = 0.0f;

    float process(float sample, const BiquadCoefficients& coeffs) {
        const float out = coeffs.b0 * sample + z1;
        z1 = coeffs.b1 * sample - coeffs.a1 * out + z2;
        z2 = coeffs.b2 * sample - coeffs.a2 * out;
        return out;
    }
};

enum class FilterKind {
    Lowpass,
    Highpass,
    Bandpass,
    Notch,
    Peak,
    LowShelf,
    HighShelf,
};

inline BiquadCoefficients normalize_biquad(
    float b0,
    float b1,
    float b2,
    float a0,
    float a1,
    float a2) {
    BiquadCoefficients coeffs;
    coeffs.b0 = b0 / a0;
    coeffs.b1 = b1 / a0;
    coeffs.b2 = b2 / a0;
    coeffs.a1 = a1 / a0;
    coeffs.a2 = a2 / a0;
    return coeffs;
}

inline BiquadCoefficients make_filter_coefficients(
    FilterKind kind,
    float sample_rate,
    float frequency_hz,
    float q,
    float gain_db,
    float slope) {
    const float clamped_frequency =
        std::clamp(frequency_hz, 5.0f, std::max(5.0f, sample_rate * 0.499f));
    const float omega = 2.0f * kPi * clamped_frequency / sample_rate;
    const float sin_omega = std::sin(omega);
    const float cos_omega = std::cos(omega);
    const float safe_q = positive_q(q);
    const float safe_slope = positive_slope(slope);
    const float alpha = sin_omega / (2.0f * safe_q);
    const float a = std::pow(10.0f, gain_db / 40.0f);
    const float sqrt_a = std::sqrt(a);
    const float shelf_alpha =
        sin_omega * 0.5f * std::sqrt((a + 1.0f / a) * (1.0f / safe_slope - 1.0f) + 2.0f);

    switch (kind) {
        case FilterKind::Lowpass:
            return normalize_biquad(
                (1.0f - cos_omega) * 0.5f,
                1.0f - cos_omega,
                (1.0f - cos_omega) * 0.5f,
                1.0f + alpha,
                -2.0f * cos_omega,
                1.0f - alpha);

        case FilterKind::Highpass:
            return normalize_biquad(
                (1.0f + cos_omega) * 0.5f,
                -(1.0f + cos_omega),
                (1.0f + cos_omega) * 0.5f,
                1.0f + alpha,
                -2.0f * cos_omega,
                1.0f - alpha);

        case FilterKind::Bandpass:
            return normalize_biquad(
                alpha,
                0.0f,
                -alpha,
                1.0f + alpha,
                -2.0f * cos_omega,
                1.0f - alpha);

        case FilterKind::Notch:
            return normalize_biquad(
                1.0f,
                -2.0f * cos_omega,
                1.0f,
                1.0f + alpha,
                -2.0f * cos_omega,
                1.0f - alpha);

        case FilterKind::Peak:
            return normalize_biquad(
                1.0f + alpha * a,
                -2.0f * cos_omega,
                1.0f - alpha * a,
                1.0f + alpha / a,
                -2.0f * cos_omega,
                1.0f - alpha / a);

        case FilterKind::LowShelf:
            return normalize_biquad(
                a * ((a + 1.0f) - (a - 1.0f) * cos_omega + 2.0f * sqrt_a * shelf_alpha),
                2.0f * a * ((a - 1.0f) - (a + 1.0f) * cos_omega),
                a * ((a + 1.0f) - (a - 1.0f) * cos_omega - 2.0f * sqrt_a * shelf_alpha),
                (a + 1.0f) + (a - 1.0f) * cos_omega + 2.0f * sqrt_a * shelf_alpha,
                -2.0f * ((a - 1.0f) + (a + 1.0f) * cos_omega),
                (a + 1.0f) + (a - 1.0f) * cos_omega - 2.0f * sqrt_a * shelf_alpha);

        case FilterKind::HighShelf:
            return normalize_biquad(
                a * ((a + 1.0f) + (a - 1.0f) * cos_omega + 2.0f * sqrt_a * shelf_alpha),
                -2.0f * a * ((a - 1.0f) + (a + 1.0f) * cos_omega),
                a * ((a + 1.0f) + (a - 1.0f) * cos_omega - 2.0f * sqrt_a * shelf_alpha),
                (a + 1.0f) - (a - 1.0f) * cos_omega + 2.0f * sqrt_a * shelf_alpha,
                2.0f * ((a - 1.0f) - (a + 1.0f) * cos_omega),
                (a + 1.0f) - (a - 1.0f) * cos_omega - 2.0f * sqrt_a * shelf_alpha);
    }

    return {};
}

class Effect {
  public:
    virtual ~Effect() = default;
    virtual void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) = 0;
};

class GainEffect final : public Effect {
  public:
    explicit GainEffect(float db) : gain_(db_to_linear(db)) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        data[index] *= gain_;
                    }
                }
            }
        });
    }

  private:
    float gain_ = 1.0f;
};

class ClipEffect final : public Effect {
  public:
    explicit ClipEffect(float threshold) : threshold_(std::max(std::abs(threshold), 0.0001f)) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        data[index] = std::clamp(data[index], -threshold_, threshold_);
                    }
                }
            }
        });
    }

  private:
    float threshold_ = 0.98f;
};

class DistortionEffect final : public Effect {
  public:
    explicit DistortionEffect(float drive)
        : drive_(std::max(drive, 0.01f)), normalizer_(std::tanh(std::max(drive_, 1.0f))) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        data[index] = std::tanh(data[index] * drive_) / normalizer_;
                    }
                }
            }
        });
    }

  private:
    float drive_ = 1.0f;
    float normalizer_ = 1.0f;
};

class TremoloEffect final : public Effect {
  public:
    TremoloEffect(float sample_rate, int channels, float rate_hz, float depth)
        : phase_step_(2.0f * kPi * std::max(rate_hz, 0.01f) / sample_rate),
          depth_(clamp_unit(depth)),
          phases_(static_cast<std::size_t>(channels), 0.0f) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                float& phase = phases_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const float lfo = 0.5f * (std::sin(phase) + 1.0f);
                        const float amount = (1.0f - depth_) + depth_ * lfo;
                        const std::size_t index = (offset + frame) * channels + channel;
                        data[index] *= amount;

                        phase += phase_step_;
                        if (phase >= 2.0f * kPi) {
                            phase -= 2.0f * kPi;
                        }
                    }
                }
            }
        });
    }

  private:
    float phase_step_ = 0.0f;
    float depth_ = 0.0f;
    std::vector<float> phases_;
};

class DelayEffect final : public Effect {
  public:
    DelayEffect(
        float sample_rate,
        int channels,
        float delay_ms,
        float feedback,
        float mix)
        : feedback_(clamp_signed_unit(feedback)),
          mix_(clamp_unit(mix)),
          positions_(static_cast<std::size_t>(channels), 0) {
        const auto delay_samples = static_cast<std::size_t>(
            std::max(1.0f, static_cast<float>(std::round(sample_rate * delay_ms / 1000.0f))));
        lines_.resize(static_cast<std::size_t>(channels), std::vector<float>(delay_samples, 0.0f));
    }

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                auto& line = lines_[static_cast<std::size_t>(channel)];
                auto& position = positions_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float delayed = line[position];
                        const float input = data[index];
                        data[index] = input * (1.0f - mix_) + delayed * mix_;
                        line[position] = input + delayed * feedback_;
                        position = (position + 1) % line.size();
                    }
                }
            }
        });
    }

  private:
    float feedback_ = 0.35f;
    float mix_ = 0.2f;
    std::vector<std::vector<float>> lines_;
    std::vector<std::size_t> positions_;
};

class PingPongDelayEffect final : public Effect {
  public:
    PingPongDelayEffect(float sample_rate, int channels, float delay_ms, float feedback, float mix)
        : delay_samples_(std::max(1.0f, sample_rate * positive_time_ms(delay_ms) / 1000.0f)),
          feedback_(clamp_signed_unit(feedback)),
          mix_(clamp_unit(mix)) {
        const auto line_length = static_cast<std::size_t>(std::max(
            8.0f,
            std::ceil(delay_samples_) + 4.0f));
        lines_.resize(static_cast<std::size_t>(channels), std::vector<float>(line_length, 0.0f));
    }

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int /* workers */) override {
        std::vector<float> input_frame(static_cast<std::size_t>(channels), 0.0f);
        std::vector<float> delayed(static_cast<std::size_t>(channels), 0.0f);
        const float dry_mix = 1.0f - mix_;

        for (std::size_t offset = 0; offset < frames; offset += block_size) {
            const std::size_t chunk = std::min(block_size, frames - offset);
            for (std::size_t frame = 0; frame < chunk; ++frame) {
                const std::size_t base = (offset + frame) * channels;

                for (int channel = 0; channel < channels; ++channel) {
                    input_frame[static_cast<std::size_t>(channel)] = data[base + channel];
                    delayed[static_cast<std::size_t>(channel)] = linear_read(
                        lines_[static_cast<std::size_t>(channel)],
                        position_,
                        delay_samples_);
                }

                for (int channel = 0; channel < channels; ++channel) {
                    float wet = delayed[static_cast<std::size_t>(channel)];
                    if (channels >= 2 && channel < 2) {
                        wet = delayed[static_cast<std::size_t>(1 - channel)];
                    }
                    data[base + channel] =
                        input_frame[static_cast<std::size_t>(channel)] * dry_mix + wet * mix_;
                }

                for (int channel = 0; channel < channels; ++channel) {
                    float feedback_source = delayed[static_cast<std::size_t>(channel)];
                    if (channels >= 2 && channel < 2) {
                        feedback_source = delayed[static_cast<std::size_t>(1 - channel)];
                    }
                    lines_[static_cast<std::size_t>(channel)][position_] =
                        input_frame[static_cast<std::size_t>(channel)] + feedback_source * feedback_;
                }

                position_ += 1;
                if (position_ >= lines_.front().size()) {
                    position_ = 0;
                }
            }
        }
    }

  private:
    float delay_samples_ = 1.0f;
    float feedback_ = 0.55f;
    float mix_ = 0.3f;
    std::vector<std::vector<float>> lines_;
    std::size_t position_ = 0;
};

class ModulatedDelayEffect final : public Effect {
  public:
    ModulatedDelayEffect(
        float sample_rate,
        int channels,
        float base_delay_ms,
        float depth_ms,
        float rate_hz,
        float mix,
        float feedback,
        bool wet_only = false,
        float stereo_phase_offset = kPi * 0.5f)
        : sample_rate_(sample_rate),
          rate_hz_(std::max(rate_hz, 0.01f)),
          base_delay_samples_(std::max(1.0f, sample_rate * positive_time_ms(base_delay_ms) / 1000.0f)),
          depth_delay_samples_(sample_rate * depth_ms / 1000.0f),
          mix_(clamp_unit(mix)),
          feedback_(clamp_signed_unit(feedback)),
          wet_only_(wet_only),
          phase_offsets_(static_cast<std::size_t>(channels), 0.0f) {
        const auto line_length = static_cast<std::size_t>(std::max(
            8.0f,
            std::ceil(sample_rate * (positive_time_ms(base_delay_ms) + std::abs(depth_ms) + 10.0f) / 1000.0f)
                + 4.0f));
        lines_.resize(static_cast<std::size_t>(channels), std::vector<float>(line_length, 0.0f));
        for (int channel = 0; channel < channels; ++channel) {
            phase_offsets_[static_cast<std::size_t>(channel)] =
                static_cast<float>(channel) * stereo_phase_offset;
        }
    }

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int /* workers */) override {
        std::vector<float> input_frame(static_cast<std::size_t>(channels), 0.0f);
        std::vector<float> wet(static_cast<std::size_t>(channels), 0.0f);
        const float dry_mix = 1.0f - mix_;

        for (std::size_t offset = 0; offset < frames; offset += block_size) {
            const std::size_t chunk = std::min(block_size, frames - offset);
            for (std::size_t frame = 0; frame < chunk; ++frame) {
                const std::size_t base = (offset + frame) * channels;
                const float time_seconds = static_cast<float>(sample_index_) / sample_rate_;
                const float lfo_base = 2.0f * kPi * rate_hz_ * time_seconds;

                for (int channel = 0; channel < channels; ++channel) {
                    const auto channel_index = static_cast<std::size_t>(channel);
                    input_frame[channel_index] = data[base + channel];

                    const float lfo =
                        0.5f * (std::sin(lfo_base + phase_offsets_[channel_index]) + 1.0f);
                    const float delay_samples =
                        std::max(1.0f, base_delay_samples_ + depth_delay_samples_ * lfo);
                    wet[channel_index] = linear_read(lines_[channel_index], position_, delay_samples);
                }

                for (int channel = 0; channel < channels; ++channel) {
                    const auto channel_index = static_cast<std::size_t>(channel);
                    if (wet_only_) {
                        data[base + channel] = wet[channel_index];
                    } else {
                        data[base + channel] = input_frame[channel_index] * dry_mix + wet[channel_index] * mix_;
                    }
                    lines_[channel_index][position_] = input_frame[channel_index] + wet[channel_index] * feedback_;
                }

                position_ += 1;
                if (position_ >= lines_.front().size()) {
                    position_ = 0;
                }
                sample_index_ += 1;
            }
        }
    }

  private:
    float sample_rate_ = 48'000.0f;
    float rate_hz_ = 0.8f;
    float base_delay_samples_ = 1.0f;
    float depth_delay_samples_ = 0.0f;
    float mix_ = 0.35f;
    float feedback_ = 0.0f;
    bool wet_only_ = false;
    std::vector<std::vector<float>> lines_;
    std::vector<float> phase_offsets_;
    std::size_t position_ = 0;
    std::size_t sample_index_ = 0;
};

class AutoPanEffect final : public Effect {
  public:
    AutoPanEffect(float sample_rate, float rate_hz, float depth)
        : sample_rate_(sample_rate),
          rate_hz_(std::max(rate_hz, 0.01f)),
          depth_(clamp_unit(depth)) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int /* workers */) override {
        if (channels < 2) {
            return;
        }

        for (std::size_t offset = 0; offset < frames; offset += block_size) {
            const std::size_t chunk = std::min(block_size, frames - offset);
            for (std::size_t frame = 0; frame < chunk; ++frame) {
                const float time_seconds = static_cast<float>(sample_index_) / sample_rate_;
                const float lfo = std::sin(2.0f * kPi * rate_hz_ * time_seconds) * depth_;
                const float angle = (lfo + 1.0f) * (kPi * 0.25f);
                const float left_gain = std::cos(angle);
                const float right_gain = std::sin(angle);
                const std::size_t base = (offset + frame) * channels;
                data[base] *= left_gain;
                data[base + 1] *= right_gain;
                sample_index_ += 1;
            }
        }
    }

  private:
    float sample_rate_ = 48'000.0f;
    float rate_hz_ = 0.35f;
    float depth_ = 1.0f;
    std::size_t sample_index_ = 0;
};

struct AllPassState {
    float x1 = 0.0f;
    float y1 = 0.0f;
};

class PhaserEffect final : public Effect {
  public:
    PhaserEffect(
        float sample_rate,
        int channels,
        float rate_hz,
        float depth,
        float center_hz,
        float feedback,
        float mix,
        int stages)
        : sample_rate_(sample_rate),
          rate_hz_(std::max(rate_hz, 0.01f)),
          depth_(clamp_unit(depth)),
          center_hz_(std::max(center_hz, 80.0f)),
          feedback_(clamp_signed_unit(feedback)),
          mix_(clamp_unit(mix)),
          states_(
              static_cast<std::size_t>(channels),
              std::vector<AllPassState>(static_cast<std::size_t>(std::max(stages, 1)))),
          feedback_states_(static_cast<std::size_t>(channels), 0.0f),
          stages_(std::max(stages, 1)) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int /* workers */) override {
        const float dry_mix = 1.0f - mix_;
        const float max_sweep_hz = std::max(80.0f, sample_rate_ * 0.45f);

        for (std::size_t offset = 0; offset < frames; offset += block_size) {
            const std::size_t chunk = std::min(block_size, frames - offset);
            for (std::size_t frame = 0; frame < chunk; ++frame) {
                const float time_seconds = static_cast<float>(sample_index_) / sample_rate_;
                const float lfo = 0.5f * (std::sin(2.0f * kPi * rate_hz_ * time_seconds) + 1.0f);
                const float sweep_hz = std::clamp(
                    center_hz_ * (0.35f + depth_ * 1.65f * lfo),
                    80.0f,
                    max_sweep_hz);
                const float omega = kPi * sweep_hz / sample_rate_;
                const float tangent = std::tan(omega);
                const float coefficient = (1.0f - tangent) / std::max(1.0f + tangent, 1e-6f);
                const std::size_t base = (offset + frame) * channels;

                for (int channel = 0; channel < channels; ++channel) {
                    const auto channel_index = static_cast<std::size_t>(channel);
                    const float dry = data[base + channel];
                    float stage_input = dry + feedback_states_[channel_index] * feedback_;
                    auto& channel_states = states_[channel_index];

                    for (int stage = 0; stage < stages_; ++stage) {
                        auto& state = channel_states[static_cast<std::size_t>(stage)];
                        const float stage_output =
                            -coefficient * stage_input + state.x1 + coefficient * state.y1;
                        state.x1 = stage_input;
                        state.y1 = stage_output;
                        stage_input = stage_output;
                    }

                    feedback_states_[channel_index] = stage_input;
                    data[base + channel] = dry * dry_mix + stage_input * mix_;
                }

                sample_index_ += 1;
            }
        }
    }

  private:
    float sample_rate_ = 48'000.0f;
    float rate_hz_ = 0.35f;
    float depth_ = 0.75f;
    float center_hz_ = 900.0f;
    float feedback_ = 0.2f;
    float mix_ = 0.5f;
    std::vector<std::vector<AllPassState>> states_;
    std::vector<float> feedback_states_;
    int stages_ = 4;
    std::size_t sample_index_ = 0;
};

class FilterEffect final : public Effect {
  public:
    FilterEffect(
        FilterKind kind,
        float sample_rate,
        int channels,
        float frequency_hz,
        float q,
        float gain_db,
        float slope,
        int stages)
        : coeffs_(make_filter_coefficients(kind, sample_rate, frequency_hz, q, gain_db, slope)),
          states_(
              static_cast<std::size_t>(channels),
              std::vector<BiquadState>(static_cast<std::size_t>(std::max(stages, 1)))),
          stages_(std::max(stages, 1)) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                auto& stage_states = states_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        float sample = data[index];
                        for (int stage = 0; stage < stages_; ++stage) {
                            sample = stage_states[static_cast<std::size_t>(stage)].process(sample, coeffs_);
                        }
                        data[index] = sample;
                    }
                }
            }
        });
    }

  private:
    BiquadCoefficients coeffs_;
    std::vector<std::vector<BiquadState>> states_;
    int stages_ = 1;
};

class CompressorEffect final : public Effect {
  public:
    CompressorEffect(
        float sample_rate,
        int channels,
        float threshold_db,
        float ratio,
        float attack_ms,
        float release_ms,
        float makeup_db)
        : threshold_(db_to_linear(threshold_db)),
          ratio_(std::max(ratio, 1.0f)),
          attack_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(attack_ms) * sample_rate))),
          release_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(release_ms) * sample_rate))),
          makeup_gain_(db_to_linear(makeup_db)),
          envelopes_(static_cast<std::size_t>(channels), 0.0f) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                float& envelope = envelopes_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float input = data[index];
                        const float detector = std::abs(input);
                        const float coeff = detector > envelope ? attack_coeff_ : release_coeff_;
                        envelope = coeff * envelope + (1.0f - coeff) * detector;

                        float gain = 1.0f;
                        if (envelope > threshold_ && envelope > 0.0f) {
                            gain = std::pow(envelope / threshold_, 1.0f / ratio_ - 1.0f);
                        }

                        data[index] = input * gain * makeup_gain_;
                    }
                }
            }
        });
    }

  private:
    float threshold_ = 0.125f;
    float ratio_ = 4.0f;
    float attack_coeff_ = 0.9f;
    float release_coeff_ = 0.999f;
    float makeup_gain_ = 1.0f;
    std::vector<float> envelopes_;
};

class UpwardCompressorEffect final : public Effect {
  public:
    UpwardCompressorEffect(
        float sample_rate,
        int channels,
        float threshold_db,
        float ratio,
        float attack_ms,
        float release_ms,
        float max_gain_db)
        : threshold_(db_to_linear(threshold_db)),
          ratio_(std::max(ratio, 1.0f)),
          attack_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(attack_ms) * sample_rate))),
          release_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(release_ms) * sample_rate))),
          max_gain_(db_to_linear(max_gain_db)),
          envelopes_(static_cast<std::size_t>(channels), 0.0f) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                float& envelope = envelopes_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float input = data[index];
                        const float detector = std::abs(input);
                        const float coeff = detector > envelope ? attack_coeff_ : release_coeff_;
                        envelope = coeff * envelope + (1.0f - coeff) * detector;

                        float gain = 1.0f;
                        if (envelope > 0.0f && envelope < threshold_) {
                            gain = std::min(
                                max_gain_,
                                std::pow(
                                    threshold_ / std::max(envelope, 1e-6f),
                                    (ratio_ - 1.0f) / ratio_));
                        }

                        data[index] = input * gain;
                    }
                }
            }
        });
    }

  private:
    float threshold_ = 0.01f;
    float ratio_ = 2.0f;
    float attack_coeff_ = 0.99f;
    float release_coeff_ = 0.999f;
    float max_gain_ = 4.0f;
    std::vector<float> envelopes_;
};

class LimiterEffect final : public Effect {
  public:
    LimiterEffect(
        float sample_rate,
        int channels,
        float ceiling_db,
        float attack_ms,
        float release_ms)
        : ceiling_(db_to_linear(ceiling_db)),
          attack_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(attack_ms) * sample_rate))),
          release_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(release_ms) * sample_rate))),
          gain_states_(static_cast<std::size_t>(channels), 1.0f) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                float& gain_state = gain_states_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float input = data[index];
                        const float level = std::abs(input);
                        const float desired_gain = level > ceiling_ && level > 0.0f ? ceiling_ / level : 1.0f;
                        const float coeff = desired_gain < gain_state ? attack_coeff_ : release_coeff_;
                        gain_state = coeff * gain_state + (1.0f - coeff) * desired_gain;
                        data[index] = std::clamp(input * gain_state, -ceiling_, ceiling_);
                    }
                }
            }
        });
    }

  private:
    float ceiling_ = 1.0f;
    float attack_coeff_ = 0.5f;
    float release_coeff_ = 0.99f;
    std::vector<float> gain_states_;
};

class ExpanderEffect final : public Effect {
  public:
    ExpanderEffect(
        float sample_rate,
        int channels,
        float threshold_db,
        float ratio,
        float attack_ms,
        float release_ms,
        float makeup_db)
        : threshold_(db_to_linear(threshold_db)),
          ratio_(std::max(ratio, 1.0f)),
          attack_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(attack_ms) * sample_rate))),
          release_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(release_ms) * sample_rate))),
          makeup_gain_(db_to_linear(makeup_db)),
          envelopes_(static_cast<std::size_t>(channels), 0.0f) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                float& envelope = envelopes_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float input = data[index];
                        const float detector = std::abs(input);
                        const float coeff = detector > envelope ? attack_coeff_ : release_coeff_;
                        envelope = coeff * envelope + (1.0f - coeff) * detector;

                        float gain = 1.0f;
                        if (envelope < threshold_ && envelope > 0.0f) {
                            gain = std::pow(envelope / threshold_, ratio_ - 1.0f);
                        }

                        data[index] = input * gain * makeup_gain_;
                    }
                }
            }
        });
    }

  private:
    float threshold_ = 0.02f;
    float ratio_ = 2.0f;
    float attack_coeff_ = 0.99f;
    float release_coeff_ = 0.999f;
    float makeup_gain_ = 1.0f;
    std::vector<float> envelopes_;
};

class NoiseGateEffect final : public Effect {
  public:
    NoiseGateEffect(
        float sample_rate,
        int channels,
        float threshold_db,
        float attack_ms,
        float release_ms,
        float floor_db)
        : threshold_(db_to_linear(threshold_db)),
          floor_gain_(db_to_linear(floor_db)),
          attack_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(attack_ms) * sample_rate))),
          release_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(release_ms) * sample_rate))),
          envelopes_(static_cast<std::size_t>(channels), 0.0f),
          gain_states_(static_cast<std::size_t>(channels), floor_gain_) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                float& envelope = envelopes_[static_cast<std::size_t>(channel)];
                float& gain_state = gain_states_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float detector = std::abs(data[index]);
                        const float env_coeff = detector > envelope ? attack_coeff_ : release_coeff_;
                        envelope = env_coeff * envelope + (1.0f - env_coeff) * detector;

                        const float target_gain = envelope >= threshold_ ? 1.0f : floor_gain_;
                        const float gain_coeff = target_gain > gain_state ? attack_coeff_ : release_coeff_;
                        gain_state = gain_coeff * gain_state + (1.0f - gain_coeff) * target_gain;
                        data[index] *= gain_state;
                    }
                }
            }
        });
    }

  private:
    float threshold_ = 0.01f;
    float floor_gain_ = 0.0f;
    float attack_coeff_ = 0.99f;
    float release_coeff_ = 0.999f;
    std::vector<float> envelopes_;
    std::vector<float> gain_states_;
};

class DeEsserEffect final : public Effect {
  public:
    DeEsserEffect(
        float sample_rate,
        int channels,
        float frequency_hz,
        float threshold_db,
        float ratio,
        float attack_ms,
        float release_ms,
        float amount)
        : detector_coeffs_(
              make_filter_coefficients(FilterKind::Highpass, sample_rate, frequency_hz, 0.70710678f, 0.0f, 1.0f)),
          threshold_(db_to_linear(threshold_db)),
          ratio_(std::max(ratio, 1.0f)),
          attack_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(attack_ms) * sample_rate))),
          release_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(release_ms) * sample_rate))),
          amount_(clamp_unit(amount)),
          detector_states_(static_cast<std::size_t>(channels)),
          envelopes_(static_cast<std::size_t>(channels), 0.0f) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                auto& detector_state = detector_states_[static_cast<std::size_t>(channel)];
                float& envelope = envelopes_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float input = data[index];
                        const float sibilant = detector_state.process(input, detector_coeffs_);
                        const float detector = std::abs(sibilant);
                        const float coeff = detector > envelope ? attack_coeff_ : release_coeff_;
                        envelope = coeff * envelope + (1.0f - coeff) * detector;

                        float gain = 1.0f;
                        if (envelope > threshold_ && envelope > 0.0f) {
                            gain = std::pow(envelope / threshold_, 1.0f / ratio_ - 1.0f);
                        }

                        const float shaped_gain = 1.0f - amount_ * (1.0f - gain);
                        data[index] = input * shaped_gain;
                    }
                }
            }
        });
    }

  private:
    BiquadCoefficients detector_coeffs_;
    float threshold_ = 0.04f;
    float ratio_ = 4.0f;
    float attack_coeff_ = 0.99f;
    float release_coeff_ = 0.999f;
    float amount_ = 1.0f;
    std::vector<BiquadState> detector_states_;
    std::vector<float> envelopes_;
};

class TransientShaperEffect final : public Effect {
  public:
    TransientShaperEffect(
        float sample_rate,
        int channels,
        float attack,
        float sustain,
        float attack_ms,
        float release_ms)
        : attack_(std::clamp(attack, -1.0f, 2.0f)),
          sustain_(std::clamp(sustain, -1.0f, 2.0f)),
          fast_attack_coeff_(std::exp(-1.0f / (0.001f * 1.0f * sample_rate))),
          fast_release_coeff_(std::exp(-1.0f / (0.001f * 12.0f * sample_rate))),
          slow_attack_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(attack_ms) * sample_rate))),
          slow_release_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(release_ms) * sample_rate))),
          fast_env_(static_cast<std::size_t>(channels), 0.0f),
          slow_env_(static_cast<std::size_t>(channels), 0.0f) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                float& fast = fast_env_[static_cast<std::size_t>(channel)];
                float& slow = slow_env_[static_cast<std::size_t>(channel)];
                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);
                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float input = data[index];
                        const float detector = std::abs(input);

                        const float fast_coeff = detector > fast ? fast_attack_coeff_ : fast_release_coeff_;
                        const float slow_coeff = detector > slow ? slow_attack_coeff_ : slow_release_coeff_;
                        fast = fast_coeff * fast + (1.0f - fast_coeff) * detector;
                        slow = slow_coeff * slow + (1.0f - slow_coeff) * detector;

                        const float transient = fast - slow;
                        const float transient_ratio = transient / std::max(fast, 1e-6f);
                        float gain =
                            1.0f + attack_ * std::max(transient_ratio, 0.0f) - sustain_ * std::min(transient_ratio, 0.0f);
                        gain = std::clamp(gain, 0.15f, 4.0f);
                        data[index] = input * gain;
                    }
                }
            }
        });
    }

  private:
    float attack_ = 0.7f;
    float sustain_ = 0.2f;
    float fast_attack_coeff_ = 0.98f;
    float fast_release_coeff_ = 0.999f;
    float slow_attack_coeff_ = 0.995f;
    float slow_release_coeff_ = 0.999f;
    std::vector<float> fast_env_;
    std::vector<float> slow_env_;
};

class DynamicEQEffect final : public Effect {
  public:
    DynamicEQEffect(
        float sample_rate,
        int channels,
        float frequency_hz,
        float threshold_db,
        float cut_db,
        float q,
        float attack_ms,
        float release_ms)
        : sample_rate_(sample_rate),
          frequency_hz_(frequency_hz),
          threshold_(db_to_linear(threshold_db)),
          cut_db_(cut_db),
          q_(positive_q(q)),
          attack_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(attack_ms) * sample_rate))),
          release_coeff_(std::exp(-1.0f / (0.001f * positive_time_ms(release_ms) * sample_rate))),
          detector_coeffs_(
              make_filter_coefficients(
                  FilterKind::Bandpass,
                  sample_rate,
                  frequency_hz,
                  q_,
                  0.0f,
                  1.0f)),
          detector_states_(static_cast<std::size_t>(channels)),
          eq_states_(static_cast<std::size_t>(channels)),
          envelopes_(static_cast<std::size_t>(channels), 0.0f) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int workers) override {
        parallel_for_channels(channels, workers, [&](int begin, int end) {
            for (int channel = begin; channel < end; ++channel) {
                auto& detector_state = detector_states_[static_cast<std::size_t>(channel)];
                auto& eq_state = eq_states_[static_cast<std::size_t>(channel)];
                float& envelope = envelopes_[static_cast<std::size_t>(channel)];

                for (std::size_t offset = 0; offset < frames; offset += block_size) {
                    const std::size_t chunk = std::min(block_size, frames - offset);

                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        const float detected = detector_state.process(data[index], detector_coeffs_);
                        const float detector = std::abs(detected);
                        const float coeff = detector > envelope ? attack_coeff_ : release_coeff_;
                        envelope = coeff * envelope + (1.0f - coeff) * detector;
                    }

                    float intensity = 0.0f;
                    if (envelope > threshold_) {
                        intensity =
                            std::min(1.0f, (envelope - threshold_) / std::max(threshold_, 1e-6f));
                    }
                    const auto eq_coeffs = make_filter_coefficients(
                        FilterKind::Peak,
                        sample_rate_,
                        frequency_hz_,
                        q_,
                        cut_db_ * intensity,
                        1.0f);

                    for (std::size_t frame = 0; frame < chunk; ++frame) {
                        const std::size_t index = (offset + frame) * channels + channel;
                        data[index] = eq_state.process(data[index], eq_coeffs);
                    }
                }
            }
        });
    }

  private:
    float sample_rate_ = 48'000.0f;
    float frequency_hz_ = 2'800.0f;
    float threshold_ = 0.06f;
    float cut_db_ = -6.0f;
    float q_ = 1.2f;
    float attack_coeff_ = 0.99f;
    float release_coeff_ = 0.999f;
    BiquadCoefficients detector_coeffs_;
    std::vector<BiquadState> detector_states_;
    std::vector<BiquadState> eq_states_;
    std::vector<float> envelopes_;
};

class RotarySpeakerEffect final : public Effect {
  public:
    RotarySpeakerEffect(
        float sample_rate,
        int channels,
        float rate_hz,
        float depth,
        float mix,
        float crossover_hz)
        : phase_step_horn_(2.0f * kPi * std::max(rate_hz, 0.01f) / sample_rate),
          phase_step_bass_(2.0f * kPi * std::max(rate_hz * 0.62f, 0.01f) / sample_rate),
          depth_(clamp_unit(depth)),
          mix_(clamp_unit(mix)),
          crossover_coeffs_(
              make_filter_coefficients(
                  FilterKind::Lowpass,
                  sample_rate,
                  crossover_hz,
                  0.70710678f,
                  0.0f,
                  1.0f)),
          crossover_states_(static_cast<std::size_t>(std::max(channels, 1))) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int /* workers */) override {
        const float dry_mix = 1.0f - mix_;
        const bool stereo = channels >= 2;

        for (std::size_t offset = 0; offset < frames; offset += block_size) {
            const std::size_t chunk = std::min(block_size, frames - offset);
            for (std::size_t frame = 0; frame < chunk; ++frame) {
                const std::size_t base = (offset + frame) * channels;
                const float horn_pan = std::sin(horn_phase_) * depth_;
                const float horn_angle = (horn_pan + 1.0f) * (kPi * 0.25f);
                const float horn_left = std::cos(horn_angle);
                const float horn_right = std::sin(horn_angle);
                const float horn_gain = 0.78f + 0.22f * std::sin(horn_phase_ + kPi * 0.5f);
                const float bass_gain = 0.9f + 0.1f * std::sin(bass_phase_);
                const float mono_horn = 0.5f * (horn_left + horn_right) * horn_gain;

                if (stereo) {
                    const float dry_left = data[base];
                    const float dry_right = data[base + 1];
                    const float low_left =
                        crossover_states_[0].process(dry_left, crossover_coeffs_);
                    const float low_right =
                        crossover_states_[1].process(dry_right, crossover_coeffs_);
                    const float high_left = dry_left - low_left;
                    const float high_right = dry_right - low_right;

                    const float wet_left = low_left * bass_gain + high_left * horn_left * horn_gain;
                    const float wet_right = low_right * bass_gain + high_right * horn_right * horn_gain;
                    data[base] = dry_left * dry_mix + wet_left * mix_;
                    data[base + 1] = dry_right * dry_mix + wet_right * mix_;

                    for (int channel = 2; channel < channels; ++channel) {
                        const float dry = data[base + channel];
                        const float low = crossover_states_[static_cast<std::size_t>(channel)].process(
                            dry,
                            crossover_coeffs_);
                        const float high = dry - low;
                        const float wet = low * bass_gain + high * mono_horn;
                        data[base + channel] = dry * dry_mix + wet * mix_;
                    }
                } else {
                    const float dry = data[base];
                    const float low = crossover_states_[0].process(dry, crossover_coeffs_);
                    const float high = dry - low;
                    const float wet = low * bass_gain + high * mono_horn;
                    data[base] = dry * dry_mix + wet * mix_;
                }

                horn_phase_ = advance_phase(horn_phase_, phase_step_horn_);
                bass_phase_ = advance_phase(bass_phase_, phase_step_bass_);
            }
        }
    }

  private:
    float phase_step_horn_ = 0.0f;
    float phase_step_bass_ = 0.0f;
    float depth_ = 0.7f;
    float mix_ = 0.65f;
    float horn_phase_ = 0.0f;
    float bass_phase_ = 0.0f;
    BiquadCoefficients crossover_coeffs_;
    std::vector<BiquadState> crossover_states_;
};

class PanEffect final : public Effect {
  public:
    explicit PanEffect(float position) : position_(std::clamp(position, -1.0f, 1.0f)) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int /* workers */) override {
        if (channels < 2) {
            return;
        }

        const float angle = (position_ + 1.0f) * (kPi * 0.25f);
        const float left_gain = std::cos(angle);
        const float right_gain = std::sin(angle);

        for (std::size_t offset = 0; offset < frames; offset += block_size) {
            const std::size_t chunk = std::min(block_size, frames - offset);
            for (std::size_t frame = 0; frame < chunk; ++frame) {
                const std::size_t base = (offset + frame) * channels;
                data[base] *= left_gain;
                data[base + 1] *= right_gain;
            }
        }
    }

  private:
    float position_ = 0.0f;
};

class StereoWidthEffect final : public Effect {
  public:
    explicit StereoWidthEffect(float width) : width_(std::max(width, 0.0f)) {}

    void process(
        float* data,
        std::size_t frames,
        int channels,
        std::size_t block_size,
        unsigned int /* workers */) override {
        if (channels < 2) {
            return;
        }

        for (std::size_t offset = 0; offset < frames; offset += block_size) {
            const std::size_t chunk = std::min(block_size, frames - offset);
            for (std::size_t frame = 0; frame < chunk; ++frame) {
                const std::size_t base = (offset + frame) * channels;
                const float left = data[base];
                const float right = data[base + 1];
                const float mid = 0.5f * (left + right);
                const float side = 0.5f * (left - right) * width_;
                data[base] = mid + side;
                data[base + 1] = mid - side;
            }
        }
    }

  private:
    float width_ = 1.0f;
};

}  // namespace voxis


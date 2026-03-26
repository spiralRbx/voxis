from voxis import AudioClip, Pipeline, effects, effect_names, preset_names, compressor, delay, distortion, lowpass

clip = AudioClip.from_file("voice.mp3")

print(type(clip).__name__)
print(clip.sample_rate)
print(clip.channels)
print(clip.duration_seconds)
print(len(effect_names()))
print(preset_names())

pipeline = (
    Pipeline(sample_rate=clip.sample_rate, channels=clip.channels, block_size=2048)
    >> [
        distortion(drive=2.5),
        lowpass(frequency_hz=8000.0, stages=2),
        delay(delay_ms=135.0, feedback=0.32, mix=0.22),
        compressor(threshold_db=-18.0, ratio=3.5),
    ]
)

edited = (
    clip.fade_in(180.0)
    .trim(start_ms=50.0, end_ms=12000.0)
    .remove_silence(threshold_db=-50.0, min_silence_ms=90.0, padding_ms=15.0)
    .remove_dc_offset()
    .normalize(headroom_db=1.0)
)

processed = clip.apply(edited)
processed.export("output1.wav")
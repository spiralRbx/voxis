# Quick start
from voxis import AudioClip, Pipeline, effects

audio = AudioClip.from_file("example.mp3")

pipeline = (
    Pipeline(sample_rate=audio.sample_rate, channels=audio.channels, block_size=2048)
    >> [
        effects.noise_reduction(strength=10.0, fft_size=1024),
        effects.de_reverb(amount=1.0, tail_ms=50, fft_size=2048, hop_size=256)
    ]
)

processed = audio.apply_pipeline(pipeline)
processed.export("output-3.mp3")


class VoxisError(Exception):
    """Base exception for Voxis."""


class FFmpegError(VoxisError):
    """Raised when FFmpeg probing, decoding, or encoding fails."""

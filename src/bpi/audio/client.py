"""Audio operations sharing the SDK session and transport."""

from bpi._generated.audio_client import AudioReadMethods

from .actions import AudioActionMethods


class AudioClient(AudioReadMethods, AudioActionMethods):
    """Audio metadata, streams, collections, rankings and account actions."""

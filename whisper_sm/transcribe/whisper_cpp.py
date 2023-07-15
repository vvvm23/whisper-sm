from typing import BinaryIO, Union

from .api import TranscribeAPI, Transcript
from .config import TranscribeConfig


class WhisperCPP(TranscribeAPI):
    def __init__(self, config: TranscribeConfig):
        super().__init__(config)

    def transcribe(self, file: Union[str, BinaryIO], *args, **kwargs) -> Transcript:
        pass

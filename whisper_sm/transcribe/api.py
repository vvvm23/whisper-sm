import abc
from collections import namedtuple
from typing import BinaryIO, Optional, Union

import pandas as pd

from .config import TranscribeConfig

Transcript: Union[str, pd.DataFrame] = namedtuple("Transcript", "file df")

"""
Abstract base class for all transcription backends.
All backends must implement this API to work interchangeably with one another.
"""


class TranscribeAPI(abc.ABC):
    def __init__(self, config: TranscribeConfig, *args, **kwargs):
        self.config = config

    @abc.abstractmethod
    def transcribe(self, file: Union[str, BinaryIO], *args, **kwargs) -> Transcript:
        pass

    def save_transcript(self, transcript: Transcript, out_file: Union[str, BinaryIO]):
        in_file, df = transcript
        f = out_file if isinstance(out_file, BinaryIO) else open(out_file, mode="a")
        f.write(f"{in_file}\n")  # TODO: generate other metadata? version, whisper backend, settings, etc.
        df.to_csv(out_file, header=False, index=False, sep=self.config.sep)
        f.close()

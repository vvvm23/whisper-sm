from dataclasses import dataclass
from typing import Tuple


@dataclass
class CuecardConfig:
    sep: str = "\t"
    audio_offset: Tuple[float, float] = (0.0, 0.0)
    image_offset: float = 0.5

    # TODO: auto determine media path as it is very platform dependant
    media_path: str = "~/Library/Application\ Support/Anki2/User\ 1/collection.media"

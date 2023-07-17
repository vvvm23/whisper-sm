from dataclasses import dataclass
from typing import Tuple


@dataclass
class CuecardConfig:
    sep: str = "\t"
    audio_offset: Tuple[float, float] = (0.0, 0.0)
    image_offset: float = 0.5

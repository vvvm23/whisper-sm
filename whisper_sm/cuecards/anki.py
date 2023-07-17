import re
from typing import BinaryIO, List, Tuple, Union

import pinyin

from ..transcribe.api import Transcript
from .config import CuecardConfig


class AnkiCuecard:
    def __init__(self, config: CuecardConfig):
        self.config = config

    def _extract_and_replace_tag(self, sentence: str):
        match = r"\*(.+?)\*"
        replace = r"<b>\1</b>"

        new_sentence = re.sub(match, replace, sentence)
        words = re.findall(match, sentence)
        words = list(dict.fromkeys(words))

        return new_sentence, words

    def _df_apply_fn(self, row):
        sentence, definitions, _, _, audio, image = row

        new_sentence, words = self._extract_and_replace_tag(sentence)

        if len(words) != len(definitions):
            raise ValueError(
                f"Input transcript had {len(definitions)} definition(s) but only extracted {len(words)} from sentence.\nPlease check transcript file."
            )
        if len(words) > self.config.max_words:
            raise ValueError(
                f"Input transcript had {len(words)} words, but maximum supported words for this cuecard frontend is {self.config.max_words}."
            )

        word_data = list(zip(words, [pinyin.get(w) for w in words], definitions))

        if len(word_data) < self.config.max_words:
            delta = self.config.max_words - len(word_data)
            word_data.extend(delta * [("", "", "")])

        first_word, *word_data = word_data

        transformed_row = {
            "sentence": new_sentence,
            "word1": first_word[0],
            "reading1": first_word[1],
            "definition1": first_word[2],
            "audio": audio,
            "image": image,
        }
        for i, (word, reading, definition) in enumerate(word_data):
            i = i + 1
            transformed_row.update(
                {
                    f"word{i}": word,
                    f"reading{i}": reading,
                    f"definition{i}": definition,
                }
            )

        return transformed_row

    def _extract_audio(self, file: Union[str, BinaryIO], times: List[Tuple[float, float]]):
        pass

    def _extract_screenshot(self, file: Union[str, BinaryIO], times: List[float]):
        pass

    def create_cuecards(self, transcript: Transcript, out_file: Union[str, BinaryIO]):
        in_file, df = transcript

        df["audio"] = self._extract_audio(in_file, list(zip(df["start_time"], df["end_time"])))
        df["image"] = self._extract_screenshot(in_file, list(df["start_time"]))

        out_df = df.apply(self._df_apply_fn, axis=1)
        out_df.to_csv(
            out_file,
            sep=self.config.sep,
            header=False,
            index=False,
        )

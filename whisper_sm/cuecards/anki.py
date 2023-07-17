import re
from pathlib import Path
from typing import BinaryIO, List, Optional, Tuple, Union

import ffmpeg
import pinyin
from slugify import slugify

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

        # TODO: replace all with arbitrary field names on output
        transformed_row = {
            "sentence": new_sentence,
            "word1": first_word[0],
            "reading1": first_word[1],
            "definition1": first_word[2],
            "audio": audio,
            "image": image,
        }
        for i, (word, reading, definition) in enumerate(word_data):
            transformed_row.update(
                {
                    f"word{i+1}": word,
                    f"reading{i+1}": reading,
                    f"definition{i+1}": definition,
                }
            )

        return transformed_row

    # TODO: batch processing?
    # TODO: progress bar / logging
    def _extract_audio(
        self, in_file: Union[str, BinaryIO], out_prefix: str, times: List[Tuple[float, float]], out_format: str = "mp3"
    ):
        out_files = []
        for i, (st, et) in enumerate(times):
            out_file = f"{out_prefix}_{i:03}.{out_format}"
            out_files.append(out_file)

            length = et - st + self.config.audio_offset[1]
            stream = ffmpeg.input(in_file, ss=st - self.config.audio_offset[0], t=length)  # TODO: clip to minimum
            stream = ffmpeg.output(stream, out_file, **{"q:a": 0, "map": "a"})

        return out_files

    # TODO: batch processing?
    # TODO: progress bar / logging
    def _extract_screenshot(
        self, in_file: Union[str, BinaryIO], out_prefix: str, times: List[float], out_format: str = "jpg"
    ):
        out_files = []
        for i, t in enumerate(times):
            out_file = f"{out_prefix}_{i:03}.{out_format}"
            out_files.append(out_file)

            stream = ffmpeg.input(in_file, ss=t + self.config.image_offset)  # TODO: clip to maximum
            stream = ffmpeg.output(stream, out_file, vframes=1)
            ffmpeg.run(stream)

        return out_files

    # TODO: progress bar / logging
    def _copy_to_collection(self, files: List[str], collections_path: Union[str, Path]):
        if isinstance(collections_path, str):
            collections_path = Path(collections_path)

        for f in files:
            f = Path(f)
            target_f = collections_path / f
            f.rename(target_f)

    # TODO: use some nice logging
    def create_cuecards(self, transcript: Transcript, out_file: Optional[Union[str, BinaryIO]] = None):
        if out_file is None:
            out_file = slugify(Path(in_file).stem, allow_unicode=True, lowercase=False) + ".csv"

        in_file, df = transcript

        media_prefix = slugify(Path(in_file).stem, allow_unicode=True, lowercase=False)
        audio_paths = self._extract_audio(in_file, media_prefix, list(zip(df["start_time"], df["end_time"])))
        image_paths = self._extract_screenshot(in_file, media_prefix, list(df["start_time"]))

        self._copy_to_collection(audio_paths, self.config.media_dir)
        self._copy_to_collection(image_paths, self.config.media_dir)

        df["audio"] = audio_paths
        df["image"] = image_paths

        out_df = df.apply(self._df_apply_fn, axis=1)
        out_df.to_csv(
            out_file,
            sep=self.config.sep,
            header=False,
            index=False,
        )

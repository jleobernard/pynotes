import pandas as pd
import numpy as np
import logging
import os
from typing import List
from pathlib import Path

from utils.service_utils import Singleton

logger = logging.getLogger(__name__)


class SentenceElement:
    value: str
    type: str

    def __init__(self, value: str, type: str):
        self.value = value
        self.type = type


class SubsDbEntry():
    video_name: str
    subs: str
    from_ts: int
    to_ts: int
    tags: List[SentenceElement]

    def __init__(self, video_name: str, subs: str, from_ts: int, to_ts: int, tags: List[SentenceElement]) -> None:
        self.video_name = video_name
        self.subs = subs
        self.from_ts = from_ts
        self.to_ts = to_ts
        self.tags = tags


class SubsClient(metaclass=Singleton):

    def __init__(self) -> None:
        logger.info("Creating SubsClient")

    def load_subs(self) -> None:
        logger.info("Loading subtitles...")
        subs_store_path = os.getenv("SUBS_STORE_PATH")
        logger.info(f"Loading subtitles from {subs_store_path}")
        subs_directories = os.listdir(subs_store_path)
        logger.debug(subs_directories)
        for subs_directory in subs_directories:
            if subs_directory[0] != '.':
                csv_file = f"{subs_store_path}/{subs_directory}/{subs_directory}.csv"
                self.__load_subs_entries(csv_file)

    def __load_subs_entries(self, csv_file) -> List[SubsDbEntry]:
        logger.info(f"Loading csv file {csv_file}")
        entries: List[SubsDbEntry] = []
        if os.path.exists(csv_file):
            pth = Path(csv_file)
            prefix: str = pth.stem
            df: pd.DataFrame = pd.read_csv(csv_file)
            nb_columns = len(df)
            print(nb_columns)
            for _, row in df.iterrows():
                tags: List[SentenceElement] = []
                for i in range(3, len(row), 2):
                    value: str = row[i]
                    if value is np.nan:
                        break
                    else:
                        type: str = row[i + 1]
                        tags.append(SentenceElement(value, type))
                entries.append(SubsDbEntry(prefix, row['subs'], row['start'], row['end'], tags))
            logger.info(f"{csv_file} loaded")
        else:
            logger.warning(f"Nothing to load in file {csv_file}")
        return entries

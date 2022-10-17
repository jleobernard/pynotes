import datetime
import logging
import os
from threading import Lock, RLock
from typing import Optional, List
import time
import aiohttp
from pydantic import parse_obj_as

from models.notes import NoteReferential
from services.singleton import Singleton

logger = logging.getLogger(__name__)


class NotesReferenceDAO(metaclass=Singleton):
    note_backend_url: str
    max_retries: int
    sleep_timeout: int
    _jwt_token: str
    _expires: int
    _pwd: str
    _login: str
    _lock: RLock
    _nb_retries: int

    def __init__(self, max_retries: int = 5, sleep_timeout: int = 1):
        self._expires = -1
        self.max_retries = max_retries
        self.sleep_timeout = sleep_timeout
        self._nb_retries = 0
        self._jwt_token = ""
        self.note_backend_url = os.getenv('NOTES_BE_URL')
        self._pwd = os.getenv('NOTES_BE_PASSSWORD')
        self._login = os.getenv('NOTES_BE_LOGIN')
        for key in ['NOTES_BE_URL', 'NOTES_BE_LOGIN', 'NOTES_BE_PASSSWORD']:
            if not os.getenv(key):
                raise RuntimeError(f"Set {key} environment variable")
        self._lock = RLock()

    async def authenticate(self, force: bool = False):
        with self._lock:
            if force or datetime.datetime.now().timestamp() >= self._expires:
                async with aiohttp.ClientSession() as session:
                    payload = {"username": self._login, "password": self._pwd}
                    async with session.post(f'{self.note_backend_url}/api/login', json=payload) as response:
                        if response.status == 200:
                            answer: dict = await response.json()
                            self._jwt_token = answer["accessToken"]
                        elif response.status == 401:
                            self._jwt_token = ''
                            logger.error(f"Supplied credentials cannot be used to authenticate user")
                            raise ConnectionError(
                                f"Error while trying to connect as {self._login} to {self.note_backend_url}")
                        else:
                            logger.error(f"Error {response.status} while trying to connect as {self._login} to"
                                         f" {self.note_backend_url}")
                            body = await response.read()
                            logger.error(f"Response body is {body}")
                            if self._nb_retries <= self.max_retries:
                                time.sleep(self.sleep_timeout)
                                self._nb_retries += 1
                                await self.authenticate(force=force)
                            else:
                                raise ConnectionError(
                                    f"Error while trying to connect as {self._login} to {self.note_backend_url}")

    async def fetch_note_by_uri(self, note_uri: str) -> Optional[NoteReferential]:
        await self.authenticate()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.note_backend_url}/api/notes/{note_uri}',
                                   headers={
                                       'authorization': f"Bearer {self._jwt_token}"
                                   }) as response:
                if response.status == 401 and self._nb_retries <= self.max_retries:
                    self._nb_retries += 1
                    return await self.fetch_note_by_uri(note_uri=note_uri)
                elif response.status == 200:
                    answer: dict = await response.json()
                    return NoteReferential(**answer)
                else:
                    raise ConnectionError(f"An error occurred while searching note {note_uri} ")

    async def fetch_notes(self, count: int, offset: int) -> List[NoteReferential]:
        await self.authenticate()
        params = {'count': count, 'offset': offset}
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.note_backend_url}/api/notes',
                                   headers={
                                       'authorization': f"Bearer {self._jwt_token}"
                                   }, params=params) as response:
                if response.status == 401 and self._nb_retries <= self.max_retries:
                    self._nb_retries += 1
                elif response.status == 200:
                    answer: dict = await response.json()
                    return parse_obj_as(List[NoteReferential], answer)
                else:
                    raise ConnectionError(f"An error occurred while searching notes with count = {count} and offset = {offset} ")

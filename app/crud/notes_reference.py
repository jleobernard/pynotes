import datetime
import logging
import os
from threading import Lock
from typing import Optional, List

import aiohttp
from pydantic import parse_obj_as

from models.notes import NoteReferential
from services.singleton import Singleton

logger = logging.getLogger(__name__)


class NotesReferenceDAO(metaclass=Singleton):
    note_backend_url: str
    jwt_token: str
    expires: int
    pwd: str
    login: str
    _lock: Lock

    def __init__(self):
        self.expires = -1
        self.jwt_token = ""
        self.note_backend_url = os.getenv('NOTES_BE_URL')
        self.pwd = os.getenv('NOTES_BE_PASSSWORD')
        self.login = os.getenv('NOTES_BE_LOGIN')
        for key in ['NOTES_BE_URL', 'NOTES_BE_LOGIN', 'NOTES_BE_PASSSWORD']:
            if not os.getenv(key):
                raise RuntimeError(f"Set {key} environment variable")
        self._lock = Lock()

    async def authenticate(self, force: bool = False):
        with self._lock:
            if force or datetime.datetime.now().timestamp() >= self.expires:
                async with aiohttp.ClientSession() as session:
                    payload = {"username": self.login, "password": self.pwd}
                    async with session.post(f'{self.note_backend_url}/api/login', json=payload) as response:
                        if response.status == 200:
                            answer: dict = await response.json()
                            self.jwt_token = answer["accessToken"]
                        else:
                            logger.error(f"Error {response.status} while trying to connect as {self.login} to"
                                         f" {self.note_backend_url}")
                            body = await response.read()
                            logger.error(f"Response body is {body}")
                            raise ConnectionError(
                                f"Error while trying to connect as {self.login} to {self.note_backend_url}")

    async def fetch_note_by_uri(self, note_uri: str) -> Optional[NoteReferential]:
        await self.authenticate()
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.note_backend_url}/api/notes/{note_uri}',
                                   headers={
                                       'authorization': f"Bearer {self.jwt_token}"
                                   }) as response:
                answer: dict = await response.json()
                return NoteReferential(**answer)

    async def fetch_notes(self, count: int, offset: int) -> List[NoteReferential]:
        await self.authenticate()
        params = {'count': count, 'offset': offset}
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{self.note_backend_url}/api/notes',
                                   headers={
                                       'authorization': f"Bearer {self.jwt_token}"
                                   }, params=params) as response:
                answer: dict = await response.json()
                return parse_obj_as(List[NoteReferential], answer)

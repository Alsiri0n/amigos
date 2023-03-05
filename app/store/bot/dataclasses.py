from dataclasses import dataclass
from typing import Optional


@dataclass
class UpdateObject:
    user_id: int
    # Для того, чтобы ответить на коллбэк нужен eventid из коллбэка,
    # иначе будет крутиться колесико.
    event_id: str
    peer_id: Optional[int] = None
    message: Optional[str] = None


@dataclass
class Update:
    type: str
    group_id: int
    object: UpdateObject


@dataclass
class Message:
    user_id: int
    text: str

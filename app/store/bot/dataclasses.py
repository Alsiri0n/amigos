from dataclasses import dataclass
from enum import Enum


class KeyboardType(Enum):
    DEFAULT = "keyboard_default"
    START = "keyboard_in_game"


class UpdateType(str, Enum):
    TEXT = "message_new"
    EVENT = "message_event"
    JOIN = "group_join"


class EventType(Enum):
    RULES = "rules"
    START = "start"
    FINISH = "end"
    FIRST = '"command":"start"'

@dataclass
class UpdateObject:
    user_id: int
    # Для того, чтобы ответить на коллбэк нужен eventid из коллбэка,
    # иначе будет крутиться колесико.
    event_id: str
    peer_id: int | None = None
    message: str | None = None
    payload: EventType | None = None


@dataclass
class Update:
    type: "UpdateType"
    group_id: int
    object: UpdateObject


@dataclass
class Message:
    user_id: int
    text: str



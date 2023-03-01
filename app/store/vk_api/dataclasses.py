from dataclasses import dataclass


@dataclass
class UpdateObject:
    id_: int
    user_id: int
    peer_id: int


@dataclass
class UpdateObjectMessageNew(UpdateObject):
    text: str


@dataclass
class UpdateObjectMessageEvent(UpdateObject):
    event_id: str
    payload: str


@dataclass
class Update:
    type: str
    object: UpdateObject
    #object_message_new: UpdateObjectMessageNew | None
    #object_message_event: UpdateObjectMessageEvent | None


@dataclass
class Message:
    # user_id: int
    text: str
    keyboard_type: str
    peer_id: int
    method: str


@dataclass
class MessageEvent:
    user_id: int
    event_id: str
    peer_id: int
    message: str
    method: str

@dataclass
class JoinEvent:
    user_id: int
    group_id: int

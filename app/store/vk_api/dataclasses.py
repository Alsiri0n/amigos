from dataclasses import dataclass


@dataclass
class UpdateObject:
    message: str
    # id_: int
    # user_id: int
    # peer_id: int | None

"""
{'ts': '607', 
'updates': [{
    'group_id': 1111111,
    'type': 'message_new',
    'event_id': '8844c6687fa30a3a794f03df17ea4f61b87d3714',
    'v': '5.131', 
    'object': {
        'message': {
            'date': 1677947433,
            'from_id': 111111,
            'id': 0,
            'out': 0,
            'attachments': [],
            'conversation_message_id': 958,
            'fwd_messages': [],
            'important': False,
            'is_hidden': False,
            'peer_id': 2000000004,
            'random_id': 0,
            'text': 'йййй'},
        'client_info': {
            'button_actions': [
                'text', 'vkpay',
                'open_app',
                'location',
                'open_link',
                'callback',
                'intent_subscribe',
                'intent_unsubscribe'],
        'keyboard': True,
            'inline_keyboard': True,
            'carousel': True,
            'lang_id': 0
            }}}]}
"""
@dataclass
class UpdateObjectMessageNew(UpdateObject):
    text: str


"""
{'ts': '608',
 'updates': [{
    'group_id': 1111111,
    'type': 'message_event',
    'event_id': '969cbfe2c41c4b0d81e0f04a5088d5f61eda84d7',
    'v': '5.131', 

    'object': {
        'user_id': 111111,
        'peer_id': 2000000004,
        'event_id': '28da64185c3b',
        'payload': {
            'game': 'rules'}
        }}]}
"""

"""
[{
'group_id': 111111111,
'type': 'group_join',
'event_id': '35bdb89ab11d1639befcb525f9cd7d8310901dc4',
'v': '5.131',
'object': {
    'user_id': 1111111,
    'join_type': 'join'}}]}
"""
@dataclass
class UpdateObjectMessageEvent(UpdateObject):
    event_id: str
    payload: str



@dataclass
class Update:
    group_id: int
    type: str
    object: UpdateObject


@dataclass
class Message:
    # user_id: int
    text: str
    keyboard_type: str
    peer_id: int


@dataclass
class MessageEvent:
    user_id: int
    event_id: str
    peer_id: int
    message: str


@dataclass
class JoinEvent:
    user_id: int
    group_id: int


@dataclass
class RawUser:
    id_: int
    first_name: str
    last_name: str

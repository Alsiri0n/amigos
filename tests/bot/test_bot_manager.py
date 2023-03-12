from app.store.vk_api.dataclasses import Message, Update, UpdateObjectMessageNew, MessageEvent
from app.web.config import Config


class TestHandleUpdates:
    async def test_no_messages(self, store):
        await store.bots_manager.handle_updates(response={})
        assert store.vk_api.send_message.called is False

    async def test_new_message(self, store, config: Config):
        await store.bots_manager.handle_updates(
            response={
                'group_id': 11, 'type': 'message_new', 'event_id': '6c2a50ec496387d05f98dc0f13fe35b9f438d8e3',
                 'v': '5.131', 'object': {
                    'message': {'date': 1678648199, 'from_id': config.admin.vk_id, 'id': 0, 'out': 0, 'attachments': [],
                                'conversation_message_id': 586, 'fwd_messages': [], 'important': False,
                                'is_hidden': False, 'peer_id': 2000000002, 'random_id': 0, 'text': '!startbot42'},
                    'client_info': {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link', 'callback',
                                                       'intent_subscribe', 'intent_unsubscribe'], 'keyboard': True,
                                    'inline_keyboard': True, 'carousel': True, 'lang_id': 0}}

            }
        )
        assert store.vk_api.send_message.call_count == 1
        message: Message = store.vk_api.send_message.mock_calls[0].args[0]
        assert message.peer_id == 2000000002
        assert message.text

    async def test_get_rules(self, store, config: Config):
        await store.bots_manager.handle_updates(
            response={
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
                        }
            }
        )
        assert store.vk_api.send_event.call_count == 1
        message_event: MessageEvent = store.vk_api.send_event.mock_calls[0].args[0]
        assert message_event.peer_id == 2000000004
        assert message_event.message == "Первое правило бойцовского клуба."
        assert message_event.event_id == "28da64185c3b"

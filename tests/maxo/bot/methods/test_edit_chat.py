from maxo.bot.methods.chats.edit_chat import EditChat
from maxo.serialization import get_retort


def test_edit_chat_dumps_description() -> None:
    retort = get_retort()

    assert retort.dump(EditChat(chat_id=-42, description="Новое описание")) == {
        "path": {"chat_id": -42},
        "body": {"description": "Новое описание"},
    }

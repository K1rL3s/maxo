from maxo.bot.methods.chats.edit_chat import EditChat
from maxo.serialization import create_retort


def test_edit_chat_dumps_description() -> None:
    retort = create_retort(warming_up=False)

    assert retort.dump(EditChat(chat_id=-42, description="Новое описание")) == {
        "path": {"chat_id": -42},
        "body": {"description": "Новое описание"},
    }

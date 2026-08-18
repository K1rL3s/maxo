from maxo.bot.methods import DeleteAdmins
from maxo.serialization import create_retort
from maxo.types import SimpleQueryResult


def test_wire_contract() -> None:
    assert DeleteAdmins.__url__ == "chats/{chat_id}/members/admins/{user_id}"
    assert DeleteAdmins.__method__ == "delete"
    assert DeleteAdmins.__returning__ is SimpleQueryResult


def test_dump() -> None:
    retort = create_retort(warming_up=False)

    assert retort.dump(DeleteAdmins(chat_id=-42, user_id=7)) == {
        "path": {"chat_id": -42, "user_id": 7},
    }

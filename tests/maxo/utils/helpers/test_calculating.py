import pytest

from maxo.enums import ChatType
from maxo.omit import Omittable, Omitted
from maxo.utils.helpers.calculating import calculate_chat_id_and_user_id


@pytest.mark.parametrize(
    ("chat_type", "chat_id", "user_id", "expected_chat_id", "expected_user_id"),
    [
        (ChatType.CHAT, 123, 456, 123, Omitted()),
        (ChatType.CHAT, None, 456, Omitted(), Omitted()),
        (ChatType.CHAT, Omitted(), 456, Omitted(), Omitted()),
        (ChatType.DIALOG, 123, 456, 123, 456),
        (ChatType.DIALOG, None, 456, Omitted(), 456),
        (ChatType.DIALOG, 123, None, 123, Omitted()),
        (ChatType.DIALOG, Omitted(), 456, Omitted(), 456),
        (ChatType.DIALOG, 123, Omitted(), 123, Omitted()),
        (ChatType.CHANNEL, 123, 456, 123, Omitted()),
        (ChatType.CHANNEL, None, 456, Omitted(), Omitted()),
        (ChatType.CHANNEL, Omitted(), 456, Omitted(), Omitted()),
    ],
)
def test_calculate_chat_id_and_user_id(
    chat_type: ChatType,
    chat_id: Omittable[int | None],
    user_id: Omittable[int | None],
    expected_chat_id: Omittable[int],
    expected_user_id: Omittable[int],
) -> None:
    result_chat_id, result_user_id = calculate_chat_id_and_user_id(
        chat_type=chat_type,
        chat_id=chat_id,
        user_id=user_id,
    )
    assert result_chat_id == expected_chat_id
    assert result_user_id == expected_user_id

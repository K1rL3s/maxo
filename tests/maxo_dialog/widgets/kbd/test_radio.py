import operator
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, Mock

from maxo.dialogs import DialogManager
from maxo.dialogs.api.entities import ChatEvent
from maxo.dialogs.widgets.kbd import Radio
from maxo.dialogs.widgets.text import Format


async def test_check_radio(mock_manager: DialogManager) -> None:
    radio: Radio[Any] = Radio(
        Format("🔘 {item[1]}"),
        Format("⚪️ {item[1]}"),
        id="fruit",
        item_id_getter=operator.itemgetter(0),
        items=[("1", "Apple"), ("2", "Banana"), ("3", "Orange")],
    )

    current_checked_fruit = radio.get_checked(mock_manager)
    assert current_checked_fruit is None

    await radio.set_checked(cast(ChatEvent, Mock()), "2", mock_manager)

    assert radio.is_checked("2", mock_manager)


async def test_validation_radio(mock_manager: DialogManager) -> None:
    def validate_datetime(text: str) -> datetime:
        return datetime.fromtimestamp(int(text), tz=UTC)

    radio: Radio[Any] = Radio(
        Format("🔘 {item[1]}"),
        Format("⚪️ {item[1]}"),
        id="datetime",
        item_id_getter=operator.itemgetter(0),
        type_factory=validate_datetime,
        items=[
            (
                int(datetime(2024, 5, 26, tzinfo=UTC).timestamp()),
                datetime(2024, 5, 26, tzinfo=UTC),
            ),
            (
                int(datetime(2024, 5, 30, tzinfo=UTC).timestamp()),
                datetime(2024, 5, 30, tzinfo=UTC),
            ),
            (
                int(datetime(2022, 3, 11, tzinfo=UTC).timestamp()),
                datetime(2022, 3, 11, tzinfo=UTC),
            ),
        ],
    )

    current_checked_date = radio.get_checked(mock_manager)
    assert current_checked_date is None

    await radio.set_checked(
        cast(ChatEvent, Mock()),
        int(datetime(2024, 5, 30, tzinfo=UTC).timestamp()),
        mock_manager,
    )

    assert radio.is_checked(
        int(datetime(2024, 5, 30, tzinfo=UTC).timestamp()),
        mock_manager,
    )

    current_checked_date = radio.get_checked(mock_manager)
    assert current_checked_date == datetime(2024, 5, 30, tzinfo=UTC)


async def test_on_state_changed_radio(mock_manager: DialogManager) -> None:
    on_state_changed = AsyncMock()
    radio: Radio[Any] = Radio(
        Format("🔘 {item[1]}"),
        Format("⚪️ {item[1]}"),
        id="fruit",
        item_id_getter=operator.itemgetter(0),
        items=[("1", "Apple"), ("2", "Banana"), ("3", "Orange")],
        on_state_changed=on_state_changed,
    )

    await radio.set_checked(cast(ChatEvent, Mock()), "2", mock_manager)

    on_state_changed.assert_called_once()

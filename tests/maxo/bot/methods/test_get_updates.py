from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from adaptix.load_error import LoadError
from unihttp.http import HTTPResponse

from maxo.bot.methods import GetUpdates
from maxo.routing.updates import MessageCreated
from maxo.types import Message
from maxo.types.update_list import UpdateList


def test_make_response_skips_malformed_update() -> None:
    get_updates = GetUpdates()

    raw_response = {
        "marker": 123,
        "updates": [
            {
                "update_type": "message_created",
                "update": {"message": {"body": {"mid": "1"}}, "timestamp": 123},
            },  # Valid
            {"update_type": "invalid_update", "update": {}},  # Malformed
        ],
    }
    mock_response = MagicMock(spec=HTTPResponse)
    mock_response.data = raw_response
    mock_response.status = 200

    mock_loader = MagicMock()
    mock_message = MagicMock(spec=Message)
    valid_update = MessageCreated(message=mock_message, timestamp=datetime.now(tz=UTC))
    mock_loader.load.side_effect = [
        valid_update,
        LoadError("Item level error"),
    ]

    with (
        patch(
            "maxo.bot.methods.base.MaxoMethod.make_response",
            side_effect=LoadError("Top level error"),
        ),
        patch(
            "maxo.bot.methods.subscriptions.get_updates.loggers.methods",
        ) as mock_logger,
    ):
        result = get_updates.make_response(mock_response, mock_loader)

        assert isinstance(result, UpdateList)
        assert result.marker == 123
        assert len(result.updates) == 1
        assert result.updates[0] == valid_update

        mock_logger.warning.assert_called_once_with(
            "Пропуск незагружаемого апдейта. Сообщите об этой ошибке в "
            "https://github.com/K1rL3s/maxo/issues. Тело апдейта: %s",
            {"update_type": "invalid_update", "update": {}},
            exc_info=True,
        )
        assert mock_loader.load.call_count == 2

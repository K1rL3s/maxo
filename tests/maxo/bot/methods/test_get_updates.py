from http.cookies import SimpleCookie
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from adaptix.load_error import LoadError
from multidict import CIMultiDict
from unihttp.http import HTTPResponse

from maxo.bot.methods import GetUpdates
from maxo.serialization import get_retort
from maxo.types import MessageCreated, UpdateList

UPDATE = {
    "update_type": "message_created",
    "timestamp": 1700000000000,
    "message": {
        "timestamp": 1700000000000,
        "sender": {
            "user_id": 1,
            "first_name": "a",
            "is_bot": False,
            "last_activity_time": 1700000000000,
        },
        "recipient": {"chat_type": "dialog"},
        "body": {"mid": "m", "seq": 1, "text": "hi"},
    },
}
UNKNOWN_UPDATE = {"update_type": "something_new", "timestamp": 1700000000000}


def make_response(data: Any) -> UpdateList:
    response = HTTPResponse(
        status_code=200,
        data=data,
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )
    return GetUpdates().make_response(response, get_retort())


def test_make_response_loads_updates_and_marker() -> None:
    result = make_response({"updates": [UPDATE], "marker": 123})

    assert result.marker == 123
    assert [type(update) for update in result.updates] == [MessageCreated]


def test_make_response_skips_unloadable_update() -> None:
    with patch(
        "maxo.bot.methods.subscriptions.get_updates.loggers.methods",
    ) as logger:
        result = make_response(
            {"updates": [UPDATE, UNKNOWN_UPDATE, UPDATE], "marker": 123},
        )

    assert result.marker == 123
    assert len(result.updates) == 2
    logger.warning.assert_called_once()
    assert logger.warning.call_args.args[1] == UNKNOWN_UPDATE


@pytest.mark.parametrize(
    "data",
    [b"<html>", {"updates": [], "marker": "not-a-number"}],
)
def test_make_response_raises_on_broken_list(data: Any) -> None:
    with pytest.raises(LoadError):
        make_response(data)

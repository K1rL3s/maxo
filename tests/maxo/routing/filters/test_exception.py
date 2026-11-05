import re

import pytest

from maxo import Ctx
from maxo.enums import ChatType
from maxo.routing.filters.exception import ExceptionMessageFilter, ExceptionTypeFilter
from maxo.routing.signals import MaxoUpdate
from maxo.types import ErrorEvent, Message, MessageBody, MessageCreated, Recipient
from tests.constants import NOW


class ParentError(Exception):
    pass


class ChildError(ParentError):
    pass


def make_error_event(error: Exception) -> ErrorEvent[Exception, MessageCreated]:
    return ErrorEvent(
        exception=error,
        update=MaxoUpdate(
            update=MessageCreated(
                timestamp=NOW,
                message=Message(
                    body=MessageBody(mid="mid", seq=1, text="text"),
                    recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
                    timestamp=NOW,
                ),
            ),
        ),
    )


async def test_exception_type_filter_matches_subclasses_by_default() -> None:
    event = make_error_event(ChildError("failed"))

    assert await ExceptionTypeFilter(ParentError)(event, Ctx({})) is True


async def test_exception_type_filter_can_match_exact_type() -> None:
    event = make_error_event(ChildError("failed"))

    exact_filter: ExceptionTypeFilter[ParentError, MessageCreated] = (
        ExceptionTypeFilter(ParentError, use_subclass=False)
    )

    assert await exact_filter(event, Ctx({})) is False


async def test_exception_message_filter_stores_match() -> None:
    ctx = Ctx({})
    event = make_error_event(ValueError("code=42"))
    message_filter: ExceptionMessageFilter[ValueError, MessageCreated] = (
        ExceptionMessageFilter(re.compile(r"code=(\d+)"))
    )

    assert str(message_filter).startswith("ExceptionMessageFilter(")
    assert await message_filter(event, ctx) is True
    assert ctx["match_exception"].group(1) == "42"


async def test_exception_message_filter_returns_false_on_miss() -> None:
    event = make_error_event(ValueError("other"))

    assert await ExceptionMessageFilter("code")(event, Ctx({})) is False


def test_exception_type_filter_requires_errors() -> None:
    with pytest.raises(ValueError, match="At least one exception type is required"):
        ExceptionTypeFilter()

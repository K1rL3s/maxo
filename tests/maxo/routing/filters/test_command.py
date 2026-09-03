import re
from typing import Any, cast

import pytest

from maxo import Bot, Ctx
from maxo.enums import ChatType
from maxo.routing.filters.command import Command, CommandException, CommandObject
from maxo.types import BotCommand, Message, MessageBody, MessageCreated, Recipient
from tests.constants import NOW


class BotInfoStub:
    username = "maxobot"


class BotStub:
    info = BotInfoStub()


def make_bot() -> Bot:
    return cast(Bot, BotStub())


def make_message_update(text: str | None) -> MessageCreated:
    return MessageCreated(
        timestamp=NOW,
        message=Message(
            body=MessageBody(mid="mid", seq=1, text=text),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
            timestamp=NOW,
        ),
    )


def test_command_object_text_and_mention() -> None:
    command = CommandObject(
        prefix="/",
        command="start",
        mention="maxobot",
        args="payload",
    )

    assert command.mentioned is True
    assert command.text == "/start@maxobot payload"


def test_command_rejects_empty_commands() -> None:
    with pytest.raises(ValueError, match="At least one command"):
        Command()


def test_command_rejects_invalid_commands_container() -> None:
    invalid_commands = cast(Any, object())

    with pytest.raises(TypeError, match="Command filter only supports"):
        Command(commands=invalid_commands)


def test_command_rejects_invalid_command_item() -> None:
    with pytest.raises(TypeError, match="Command filter only supports"):
        Command(cast(BotCommand, object()))


async def test_command_call_stores_command_in_ctx() -> None:
    ctx = Ctx({"bot": make_bot()})
    command_filter = Command("start")

    assert await command_filter(make_message_update("/start payload"), ctx) is True
    assert ctx["command"] == CommandObject(
        prefix="/",
        command="start",
        args="payload",
    )


async def test_command_call_returns_false_for_missing_text() -> None:
    ctx = Ctx({"bot": make_bot()})

    assert await Command("start")(make_message_update(None), ctx) is False
    assert "command" not in ctx


async def test_command_validates_case_prefix_mention_and_regex() -> None:
    command_filter = Command(
        "start",
        re.compile(r"item_(\d+)"),
        commands=BotCommand(name="help"),
        prefix="/!",
        ignore_case=True,
    )

    assert str(command_filter).startswith("Command(")

    command = await command_filter.parse_command("/START@maxobot", make_bot())
    assert command.command == "START"

    regex_command = await command_filter.parse_command("!item_42", make_bot())
    assert regex_command.regexp_match is not None
    assert regex_command.regexp_match.group(1) == "42"

    help_command = await command_filter.parse_command("/HELP", make_bot())
    assert help_command.command == "HELP"


async def test_command_rejects_wrong_prefix_mention_and_name() -> None:
    command_filter = Command("start")

    with pytest.raises(CommandException, match="Invalid command prefix"):
        await command_filter.parse_command("!start", make_bot())

    with pytest.raises(CommandException, match="Mention did not match"):
        await command_filter.parse_command("/start@otherbot", make_bot())

    with pytest.raises(CommandException, match="Command did not match"):
        await command_filter.parse_command("/help", make_bot())


async def test_command_can_ignore_mention() -> None:
    command = await Command("start", ignore_mention=True).parse_command(
        "/start@otherbot",
        make_bot(),
    )

    assert command.mention == "otherbot"

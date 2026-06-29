"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/filters/command.py.

Original code licensed under MIT by aiogram contributors

The MIT License (MIT)

Copyright (c) 2017 - present Alex Root Junior

Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so, subject to the
following conditions:

The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
OR OTHER DEALINGS IN THE SOFTWARE.
"""

import re
from collections.abc import Iterable, Sequence
from dataclasses import field, replace
from re import Match, Pattern
from typing import cast

from maxo import Bot, Ctx
from maxo.omit import is_defined
from maxo.routing.filters import BaseFilter
from maxo.routing.updates import MessageCreated
from maxo.types.base import MaxoType
from maxo.types.bot_command import BotCommand

CommandPatternType = str | re.Pattern[str] | BotCommand


class CommandException(Exception):
    pass


class CommandObject(MaxoType):
    prefix: str = "/"
    command: str = ""
    mention: str | None = None
    args: str | None = field(repr=False, default=None)
    regexp_match: Match[str] | None = field(repr=False, default=None)

    @property
    def mentioned(self) -> bool:
        return bool(self.mention)

    @property
    def text(self) -> str:
        line = self.prefix + self.command
        if self.mention:
            line += "@" + self.mention
        if self.args:
            line += " " + self.args
        return line


class Command(BaseFilter[MessageCreated]):
    __slots__ = ("commands", "ignore_case", "ignore_mention", "magic", "prefix")

    def __init__(
        self,
        *values: CommandPatternType,
        commands: Sequence[CommandPatternType] | CommandPatternType | None = None,
        prefix: str = "/",
        ignore_case: bool = False,
        ignore_mention: bool = False,
    ) -> None:
        if commands is None:
            commands = []
        if isinstance(commands, (str, re.Pattern, BotCommand)):
            commands = [commands]

        if not isinstance(commands, Iterable):
            raise TypeError(
                "Command filter only supports str, re.Pattern, BotCommand object"
                " or their Iterable",
            )

        items = []
        for command in (*values, *commands):
            if isinstance(command, BotCommand):
                command = command.name
            if not isinstance(command, (str, re.Pattern)):
                raise TypeError(
                    "Command filter only supports str, re.Pattern, BotCommand object"
                    " or their Iterable",
                )
            if ignore_case and isinstance(command, str):
                command = command.casefold()
            items.append(command)

        if not items:
            raise ValueError("At least one command should be specified")

        self.commands = tuple(items)
        self.prefix = prefix
        self.ignore_case = ignore_case
        self.ignore_mention = ignore_mention

    def __str__(self) -> str:
        return self._signature_to_string(
            *self.commands,
            prefix=self.prefix,
            ignore_case=self.ignore_case,
            ignore_mention=self.ignore_mention,
        )

    async def __call__(
        self,
        message: MessageCreated,
        ctx: Ctx,
    ) -> bool:
        if message.message.body.text:
            text = message.message.body.text
        elif is_defined(link := message.message.link) and link.message.text:
            text = link.message.text
        else:
            text = None

        if not text:
            return False

        try:
            command = await self.parse_command(text=text, bot=ctx["bot"])
        except CommandException:
            return False

        ctx["command"] = command
        return True

    def extract_command(self, text: str) -> CommandObject:
        try:
            full_command, *args = text.split(maxsplit=1)
        except ValueError as e:
            raise CommandException("not enough values to unpack") from e

        prefix, (command, _, mention) = full_command[0], full_command[1:].partition("@")
        return CommandObject(
            prefix=prefix,
            command=command,
            mention=mention or None,
            args=args[0] if args else None,
        )

    def validate_prefix(self, command: CommandObject) -> None:
        if command.prefix not in self.prefix:
            raise CommandException("Invalid command prefix")

    async def validate_mention(self, bot: Bot, command: CommandObject) -> None:
        if command.mention and not self.ignore_mention:
            me = bot.state.info
            if me.username and command.mention.lower() != me.username.lower():
                raise CommandException("Mention did not match")

    def validate_command(self, command: CommandObject) -> CommandObject:
        for allowed_command in cast(Sequence[CommandPatternType], self.commands):
            if isinstance(allowed_command, Pattern):
                result = allowed_command.match(command.command)
                if result:
                    return replace(command, regexp_match=result)

            command_name = command.command
            if self.ignore_case:
                command_name = command_name.casefold()

            if command_name == allowed_command:
                return command
        raise CommandException("Command did not match pattern")

    async def parse_command(self, text: str, bot: Bot) -> CommandObject:
        command = self.extract_command(text)
        self.validate_prefix(command=command)
        await self.validate_mention(bot=bot, command=command)
        return self.validate_command(command)


class CommandStart(Command):
    def __init__(self, ignore_case: bool = False, ignore_mention: bool = False) -> None:
        super().__init__(
            "start",
            prefix="/",
            ignore_case=ignore_case,
            ignore_mention=ignore_mention,
        )

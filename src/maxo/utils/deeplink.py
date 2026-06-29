"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/utils/deep_linking.py.

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

__all__ = (
    "create_deep_link",
    "create_max_http_link",
    "create_start_link",
    "create_startapp_link",
    "decode_payload",
    "encode_payload",
)

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Literal, cast

from maxo.utils.link import create_max_http_link
from maxo.utils.payload import decode_payload, encode_payload

if TYPE_CHECKING:
    from maxo import Bot

BAD_PATTERN = re.compile(r"[^a-zA-Z0-9-_]")

PAYLOAD_MAX_LEN = 128


def create_start_link(
    bot: "Bot",
    payload: str,
    encode: bool = False,
    encoder: Callable[[bytes], bytes] | None = None,
) -> str:
    return create_deep_link(
        username=cast(str, bot.state.info.username),
        link_type="start",
        payload=payload,
        encode=encode,
        encoder=encoder,
    )


def create_startapp_link(
    bot: "Bot",
    payload: str,
    encode: bool = False,
    app_name: str | None = None,
    encoder: Callable[[bytes], bytes] | None = None,
) -> str:
    return create_deep_link(
        username=cast(str, bot.state.info.username),
        link_type="startapp",
        payload=payload,
        app_name=app_name,
        encode=encode,
        encoder=encoder,
    )


def create_deep_link(
    username: str,
    link_type: Literal["start", "startgroup", "startapp"],
    payload: str,
    app_name: str | None = None,
    encode: bool = False,
    encoder: Callable[[bytes], bytes] | None = None,
) -> str:
    if encode or encoder:
        payload = encode_payload(payload, encoder=encoder)

    if re.search(BAD_PATTERN, payload):
        raise ValueError(
            "Wrong payload! Only A-Z, a-z, 0-9, _ and - are allowed. "
            "Pass `encode=True` or encode payload manually.",
        )

    if len(payload) > PAYLOAD_MAX_LEN:
        raise ValueError(f"Payload must be up to {PAYLOAD_MAX_LEN} characters long.")

    if not app_name:
        deep_link = create_max_http_link(username, **{cast(str, link_type): payload})
    else:
        deep_link = create_max_http_link(
            username,
            app_name,
            **{cast(str, link_type): payload},
        )

    return deep_link

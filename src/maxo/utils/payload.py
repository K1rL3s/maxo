"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/utils/payload.py.

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

from base64 import b64decode, urlsafe_b64encode
from collections.abc import Callable

from maxo.errors import InvalidPayloadError


def encode_payload(
    payload: str,
    encoder: Callable[[bytes], bytes] | None = None,
) -> str:
    payload_bytes = payload.encode("utf-8")
    if encoder is not None:
        payload_bytes = encoder(payload_bytes)

    return _encode_b64(payload_bytes)


def decode_payload(
    payload: str,
    decoder: Callable[[bytes], bytes] | None = None,
) -> str:
    """
    Декодирует payload, закодированный через `encode_payload`.

    Args:
        payload: Строка base64url, паддинг `=` необязателен.
        decoder: Функция, обратная `encoder` из `encode_payload`. Её
            исключения пробрасываются как есть.

    Raises:
        InvalidPayloadError: Если payload не является корректным base64
            или результат не декодируется из UTF-8.

    """
    payload_bytes = _decode_b64(payload)
    if decoder is not None:
        payload_bytes = decoder(payload_bytes)

    try:
        return payload_bytes.decode()
    except UnicodeDecodeError as e:
        raise InvalidPayloadError(payload) from e


def _encode_b64(payload: bytes) -> str:
    bytes_payload: bytes = urlsafe_b64encode(payload)
    str_payload = bytes_payload.decode()
    return str_payload.replace("=", "")


def _decode_b64(payload: str) -> bytes:
    padded = payload + "=" * (-len(payload) % 4)
    try:
        return b64decode(padded, altchars=b"-_", validate=True)
    except ValueError as e:
        raise InvalidPayloadError(payload) from e

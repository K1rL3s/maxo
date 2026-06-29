"""
https://github.com/aiogram/aiogram/blob/dev-3.x/aiogram/utils/link.py.

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

import base64
from typing import Any
from urllib.parse import urlencode, urljoin


def _format_url(
    url: str,
    *path: str,
    fragment_: str | None = None,
    **query: Any,
) -> str:
    url = urljoin(url, "/".join(path), allow_fragments=True)
    if query:
        url += "?" + urlencode(query)
    if fragment_:
        url += "#" + fragment_
    return url


def create_max_link(link: str, **kwargs: Any) -> str:
    return _format_url(f"max://{link}", **kwargs)


def create_max_http_link(*path: str, **kwargs: Any) -> str:
    return _format_url("https://max.ru", *path, **kwargs)


"""
Based on реверс-инженере генерируемых ссылок на клиенте в группах и каналах.

Ссылки работают только для групп и каналов, для диалогов ссылка будет выдавать 404
"""


def id_to_message_url(sequence_id: int, chat_id: int) -> str:
    """Преобразует числовой ID сообщения в ссылку на сообщение."""
    # Преобразуем число в 8 байт в формате big-endian
    bytes_data = sequence_id.to_bytes(8, byteorder="big")

    # Кодируем в base64
    base64_std = base64.b64encode(bytes_data).decode("ascii")

    # Делаем URL-safe: удаляем padding и заменяем символы
    base64_url = base64_std.rstrip("=").replace("+", "-").replace("/", "_")

    return create_max_http_link("c", str(chat_id), base64_url)


def url_to_message_id(url: str) -> int:
    """Обратное преобразование: из URL-safe base64 в числовой ID."""
    # Извлекаем последнюю часть URL (после последнего /)
    base64_url = url.strip("/").split("/")[-1]

    # Восстанавливаем стандартный base64
    base64_std = base64_url.replace("-", "+").replace("_", "/")

    # Восстанавливаем padding
    padding = (4 - len(base64_std) % 4) % 4
    if padding:
        base64_std += "=" * padding

    # Декодируем
    bytes_data = base64.b64decode(base64_std)
    return int.from_bytes(bytes_data, byteorder="big")

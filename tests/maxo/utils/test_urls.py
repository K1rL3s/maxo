import re

import pytest

from maxo.enums import MessageLinkType
from maxo.types import LinkedMessage, MessageBody
from maxo.utils.link import id_to_message_url, url_to_message_id


def test_id_to_message_url() -> None:
    url = id_to_message_url(sequence_id=116341337478799028, chat_id=-71196681472709)
    assert url == "https://max.ru/c/-71196681472709/AZ1T1H0eHrQ"


def test_url_to_message_id() -> None:
    sequence_id = url_to_message_id("https://max.ru/c/-71196681472709/AZ1T1H0eHrQ")
    assert sequence_id == 116341337478799028


def test_url_to_message_id_ignores_query_and_fragment() -> None:
    sequence_id = url_to_message_id(
        "https://max.ru/c/-71196681472709/AZ1T1H0eHrQ?x=1#frag",
    )
    assert sequence_id == 116341337478799028


def test_url_to_message_id_ignores_trailing_slash() -> None:
    sequence_id = url_to_message_id("https://max.ru/c/-71196681472709/AZ1T1H0eHrQ/")
    assert sequence_id == 116341337478799028


def test_url_to_message_id_rejects_garbage_characters() -> None:
    url = "https://max.ru/c/1/!!!!!!!!"
    expected = f"^{re.escape(f'Invalid message URL: {url!r}')}$"
    with pytest.raises(ValueError, match=expected):
        url_to_message_id(url)


def test_url_to_message_id_rejects_wrong_decoded_length() -> None:
    url = "https://max.ru/c/1/AAAA?x=1"
    expected = f"^{re.escape(f'Invalid message URL: {url!r}')}$"
    with pytest.raises(ValueError, match=expected):
        url_to_message_id(url)


def test_url_to_message_id_rejects_malformed_netloc() -> None:
    url = "https://[::1"
    expected = f"^{re.escape(f'Invalid message URL: {url!r}')}$"
    with pytest.raises(ValueError, match=expected):
        url_to_message_id(url)


def test_url_to_message_id_rejects_non_ascii_segment() -> None:
    url = "https://max.ru/c/1/\xe9"
    expected = f"^{re.escape(f'Invalid message URL: {url!r}')}$"
    with pytest.raises(ValueError, match=expected):
        url_to_message_id(url)


def test_linked_message_generated_url() -> None:
    linked_message = LinkedMessage(
        message=MessageBody(mid="mid:edren_baton", seq=116341337478799028),
        chat_id=-71196681472709,
        type=MessageLinkType.FORWARD,
    )
    assert (
        linked_message.generated_url == "https://max.ru/c/-71196681472709/AZ1T1H0eHrQ"
    )


def test_linked_message_generated_url_no_chat_id() -> None:
    linked_message = LinkedMessage(
        message=MessageBody(mid="mid:edren_baton", seq=116341337478799028),
        type=MessageLinkType.FORWARD,
    )
    assert linked_message.generated_url is None

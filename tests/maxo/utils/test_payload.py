import pytest

from maxo.errors import InvalidPayloadError
from maxo.utils.payload import decode_payload, encode_payload


@pytest.mark.parametrize(
    "payload",
    ["hello world", "привет", "🦀👍", *("a" * length for length in range(9))],
)
def test_round_trip(payload: str) -> None:
    assert decode_payload(encode_payload(payload)) == payload


def test_round_trip_with_custom_coder() -> None:
    def reverse(data: bytes) -> bytes:
        return data[::-1]

    encoded = encode_payload("привет", encoder=reverse)

    assert decode_payload(encoded, decoder=reverse) == "привет"


@pytest.mark.parametrize(
    ("payload", "expected"),
    [("aGk=", "hi"), ("Pj4+", ">>>"), ("Pz8/", "???")],
)
def test_decode_padded_and_standard_alphabet(payload: str, expected: str) -> None:
    assert decode_payload(payload) == expected


@pytest.mark.parametrize(
    "payload",
    ["!!!", "a", "_w", "aGk==", "абвг"],
)
def test_decode_invalid_payload(payload: str) -> None:
    with pytest.raises(InvalidPayloadError) as exc_info:
        decode_payload(payload)

    assert exc_info.value.payload == payload


def test_decode_non_utf8_decoder_result() -> None:
    with pytest.raises(InvalidPayloadError):
        decode_payload("aGk", decoder=lambda _: b"\xff")

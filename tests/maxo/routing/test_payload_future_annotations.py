from __future__ import annotations

from enum import Enum

from maxo.routing.filters.payload import Payload


class Level(Enum):
    LOW = "low"
    HIGH = "high"


class FutureAnnotationsPayload(Payload, prefix="future"):
    num: int
    flag: bool
    level: Level
    optional: int | None


def test_unpack_resolves_string_annotations() -> None:
    original = FutureAnnotationsPayload(
        num=42,
        flag=False,
        level=Level.HIGH,
        optional=None,
    )

    unpacked = FutureAnnotationsPayload.unpack(original.pack())

    assert unpacked == original
    assert type(unpacked.num) is int
    assert unpacked.flag is False


def test_unpack_resolves_string_optional_annotation() -> None:
    unpacked = FutureAnnotationsPayload.unpack("future:1:1:low:7")

    assert unpacked.optional == 7

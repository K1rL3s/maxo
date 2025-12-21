import dataclasses
from decimal import Decimal
from enum import Enum, auto
from fractions import Fraction
from typing import Optional, Union
from uuid import UUID, uuid4

import pytest
from magic_filter import F

from maxo.integrations.magic_filter import MagicFilter
from maxo.routing.filters.payload import Payload, _check_field_is_nullable
from maxo.types import User


class MyIntEnum(Enum):
    FOO = auto()


class MyStringEnum(str, Enum):
    FOO = "FOO"


class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


class MyPayload(Payload, prefix="test"):
    foo: str
    bar: int


class FullPayload(Payload, prefix="full"):
    int_field: int
    str_field: str
    float_field: float
    bool_field: bool
    decimal_field: Decimal
    fraction_field: Fraction
    uuid_field: UUID
    enum_field: Color
    none_field: str | None = None
    default_field: int = 42


class OptionalPayload(Payload, prefix="opt"):
    optional_int: int | None
    optional_with_default: str | None = "default"


class SimplePayload(Payload, prefix="simple"):
    name: str
    age: int


class TestPayload:
    def test_bool_encoding(self) -> None:
        class BoolPayload(Payload, prefix="bool"):
            flag: bool

        assert BoolPayload(flag=True).pack() == "bool:1"
        assert BoolPayload(flag=False).pack() == "bool:0"

        unpacked_true = BoolPayload.unpack("bool:1")
        unpacked_false = BoolPayload.unpack("bool:0")
        assert unpacked_true.flag is True
        assert unpacked_false.flag is False

    def test_uuid_hex_encoding(self) -> None:
        uuid_val = UUID("123e4567-e89b-12d3-a456-426614174000")

        class UuidPayload(Payload, prefix="uuid"):
            id: UUID

        packed = UuidPayload(id=uuid_val).pack()
        assert packed == "uuid:123e4567e89b12d3a456426614174000"

        unpacked = UuidPayload.unpack(packed)
        assert unpacked.id == uuid_val
        assert isinstance(unpacked.id, UUID)

    def test_enum_encoding(self) -> None:
        class EnumPayload(Payload, prefix="enum"):
            color: Color

        packed = EnumPayload(color=Color.BLUE).pack()
        assert packed == "enum:blue"

        unpacked = EnumPayload.unpack("enum:blue")
        assert unpacked.color is Color.BLUE

    def test_wrong_prefix(self) -> None:
        with pytest.raises(ValueError, match="Bad prefix"):
            FullPayload.unpack("wrong:123:hello:3.14:1:12.34:1/3:...")

    def test_pack_unpack_full_cycle(self) -> None:
        uuid_val = uuid4()
        data = FullPayload(
            int_field=123,
            str_field="hello",
            float_field=3.14,
            bool_field=True,
            decimal_field=Decimal("12.34"),
            fraction_field=Fraction(1, 3),
            uuid_field=uuid_val,
            enum_field=Color.GREEN,
            none_field=None,
            default_field=100,  # переопределяем default
        )

        packed = data.pack()
        unpacked = FullPayload.unpack(packed)

        assert unpacked == data
        assert isinstance(unpacked.int_field, int)
        assert isinstance(unpacked.str_field, str)
        assert isinstance(unpacked.float_field, float)
        assert isinstance(unpacked.bool_field, bool)
        assert isinstance(unpacked.decimal_field, Decimal)
        assert isinstance(unpacked.fraction_field, Fraction)
        assert isinstance(unpacked.uuid_field, UUID)
        assert isinstance(unpacked.enum_field, Color)
        assert unpacked.none_field is None
        assert unpacked.default_field == 100

    def test_wrong_number_of_parts(self) -> None:
        with pytest.raises(TypeError):
            FullPayload.unpack("full:1:2:3")

    def test_invalid_value_type(self) -> None:
        with pytest.raises(ValueError, match="Cannot decode"):
            FullPayload.unpack(
                "full:not_int:hello:3.14:1:12.34:1/3:123e4567-e89b-12d3-a456-426614174000:green::42",
            )

    def test_separator_in_value(self) -> None:

        class BadPayload(Payload, prefix="bad"):
            field: str

        with pytest.raises(ValueError, match="Separator symbol"):
            BadPayload(field="hello:world").pack()

    def test_separator_in_prefix_forbidden(self) -> None:
        with pytest.raises(ValueError, match="can not be used inside prefix"):

            class InvalidPrefix(Payload, prefix="bad:prefix"):
                field: str

    def test_no_prefix_given(self) -> None:
        with pytest.raises(ValueError, match="prefix required"):

            class NoPrefix(Payload):
                field: str

    def test_custom_separator(self) -> None:

        class CustomSep(Payload, prefix="custom", sep="|"):
            a: int
            b: str

        data = CustomSep(a=10, b="test")
        packed = data.pack()
        assert packed == "custom|10|test"

        unpacked = CustomSep.unpack(packed)
        assert unpacked == data

    def test_too_long_payload(self) -> None:
        long_str = "a" * 2000

        class LongPayload(Payload, prefix="long"):
            data: str

        with pytest.raises(ValueError, match="Resulted callback data is too long"):
            LongPayload(data=long_str).pack()

    def test_unsupported_type_in_pack(self) -> None:

        class UnsupportedPayload(Payload, prefix="uns"):
            data: list[int]

        with pytest.raises(ValueError, match="can not be packed"):
            UnsupportedPayload(data=[1, 2, 3]).pack()

    def test_nullable_check_helper(self) -> None:

        class TestNullable(Payload, prefix="test"):
            required: float
            optional: int | None = None
            with_default: str = "hello"

        fields = dataclasses.fields(TestNullable)
        assert _check_field_is_nullable(fields[0]) is False  # required
        assert _check_field_is_nullable(fields[1]) is True  # optional
        assert _check_field_is_nullable(fields[2]) is True  # with_default

    def test_simple_roundtrip(self) -> None:
        original = SimplePayload(name="Alice", age=30)
        packed = original.pack()
        unpacked = SimplePayload.unpack(packed)

        assert unpacked.name == "Alice"
        assert unpacked.age == 30
        assert isinstance(unpacked.age, int)

    def test_init_subclass_prefix_required(self) -> None:
        assert MyPayload.__prefix__ == "test"

        with pytest.raises(ValueError, match="prefix required.+"):

            class MyInvalidPayload(Payload):
                pass

    def test_init_subclass_sep_validation(self) -> None:
        assert MyPayload.__separator__ == ":"

        class MyPayload2(Payload, prefix="test2", sep="@"):
            pass

        assert MyPayload2.__separator__ == "@"

        with pytest.raises(ValueError, match="Separator symbol '@' .+ 'sp@m'"):

            class MyInvalidPayload(Payload, prefix="sp@m", sep="@"):
                pass

    @pytest.mark.parametrize(
        "value,expected",
        [
            [None, ""],
            [True, "1"],
            [False, "0"],
            [42, "42"],
            ["test", "test"],
            [9.99, "9.99"],
            [Decimal("9.99"), "9.99"],
            [Fraction("3/2"), "3/2"],
            [
                UUID("123e4567-e89b-12d3-a456-426655440000"),
                "123e4567e89b12d3a456426655440000",
            ],
            [MyIntEnum.FOO, "1"],
            [MyStringEnum.FOO, "FOO"],
        ],
    )
    def test_encode_value_positive(self, value, expected):
        callback = MyPayload(foo="test", bar=42)
        assert callback._encode_value("test", value) == expected

    @pytest.mark.parametrize(
        "value",
        [
            ...,
            object,
            object(),
            User(user_id=42, is_bot=False, first_name="test", last_activity_time=0),
        ],
    )
    def test_encode_value_negative(self, value):
        callback = MyPayload(foo="test", bar=42)
        with pytest.raises(ValueError):
            callback._encode_value("test", value)

    def test_pack(self) -> None:
        with pytest.raises(ValueError, match="Separator symbol .+"):
            assert MyPayload(foo="te:st", bar=42).pack()

        with pytest.raises(ValueError, match=".+is too long.+"):
            assert MyPayload(foo="test" * 256, bar=42).pack()

        assert MyPayload(foo="test", bar=42).pack() == "test:test:42"

    def test_pack_uuid(self) -> None:

        class MyPayloadWithUUID(Payload, prefix="test"):
            foo: str
            bar: UUID

        callback = MyPayloadWithUUID(
            foo="test",
            bar=UUID("123e4567-e89b-12d3-a456-426655440000"),
        )

        assert callback.pack() == "test:test:123e4567e89b12d3a456426655440000"

    def test_pack_optional(self) -> None:

        class MyPayload1(Payload, prefix="test1"):
            foo: str
            bar: int | None = None

        assert MyPayload1(foo="spam").pack() == "test1:spam:"
        assert MyPayload1(foo="spam", bar=42).pack() == "test1:spam:42"

        class MyPayload2(Payload, prefix="test2"):
            foo: str | None = None
            bar: int

        assert MyPayload2(bar=42).pack() == "test2::42"
        assert MyPayload2(foo="spam", bar=42).pack() == "test2:spam:42"

        class MyPayload3(Payload, prefix="test3"):
            foo: str | None = "experiment"
            bar: int

        assert MyPayload3(bar=42).pack() == "test3:experiment:42"
        assert MyPayload3(foo="spam", bar=42).pack() == "test3:spam:42"

    def test_unpack(self) -> None:
        with pytest.raises(TypeError, match=".+ takes 2 arguments but 3 were given"):
            MyPayload.unpack("test:test:test:test")

        with pytest.raises(ValueError, match="Bad prefix .+"):
            MyPayload.unpack("spam:test:test")

        assert MyPayload.unpack("test:test:42") == MyPayload(foo="test", bar=42)

    def test_unpack_optional(self) -> None:
        with pytest.raises(ValueError):
            assert MyPayload.unpack("test:test:")

        class MyPayload1(Payload, prefix="test1"):
            foo: str
            bar: int | None = None

        assert MyPayload1.unpack("test1:spam:") == MyPayload1(foo="spam")
        assert MyPayload1.unpack("test1:spam:42") == MyPayload1(foo="spam", bar=42)

        class MyPayload2(Payload, prefix="test2"):
            foo: str | None = None
            bar: int

        assert MyPayload2.unpack("test2::42") == MyPayload2(bar=42)
        assert MyPayload2.unpack("test2:spam:42") == MyPayload2(foo="spam", bar=42)

        class MyPayload3(Payload, prefix="test3"):
            foo: str | None = "experiment"
            bar: int

        assert MyPayload3.unpack("test3:experiment:42") == MyPayload3(bar=42)
        assert MyPayload3.unpack("test3:spam:42") == MyPayload3(foo="spam", bar=42)

        class MyPayload4(Payload, prefix="test4"):
            foo: str | None = ""
            bar: str | None = None

        assert MyPayload4.unpack("test4::") == MyPayload4(foo="", bar=None)
        assert MyPayload4.unpack("test4::") == MyPayload4()

    @pytest.mark.parametrize(
        "hint",
        [
            Union[int, None],
            Optional[int],
            int | None,
        ],
    )
    def test_unpack_optional_wo_default(self, hint):
        """Test Payload without default optional."""

        class TgData(Payload, prefix="tg"):
            chat_id: int
            thread_id: hint

        assert TgData.unpack("tg:123:") == TgData(chat_id=123, thread_id=None)

    def test_unpack_optional_wo_default_union_type(self) -> None:
        """Test Payload without default optional."""

        class TgData(Payload, prefix="tg"):
            chat_id: int
            thread_id: int | None

        assert TgData.unpack("tg:123:") == TgData(chat_id=123, thread_id=None)

    def test_build_filter(self) -> None:
        filter_object = MyPayload.filter(MagicFilter(F.foo == "test"))
        assert isinstance(filter_object.filter, MagicFilter)
        assert filter_object.payload is MyPayload

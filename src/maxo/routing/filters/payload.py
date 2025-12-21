import dataclasses
import types
import typing
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from typing import Any, ClassVar, Self, TypeVar, get_args, get_origin
from uuid import UUID

from maxo import Ctx
from maxo.routing.filters import BaseFilter
from maxo.routing.interfaces import Filter
from maxo.routing.updates import MessageCallback
from maxo.types import MaxoType

T = TypeVar("T", bound="Payload")

MAX_PAYLOAD_LENGTH: int = 1024


_UNION_TYPES = {typing.Union, types.UnionType}


class PayloadException(Exception):
    pass


class Payload(MaxoType, slots=False):
    __separator__: ClassVar[str]
    __prefix__: ClassVar[str]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        if (
            getattr(cls, "__separator__", None) is not None
            and getattr(cls, "__prefix__", None) is not None
        ):
            # https://github.com/K1rL3s/maxo/issues/22
            # Уверен, можно лучше
            super().__init_subclass__(**kwargs)
            return

        if "prefix" not in kwargs:
            raise ValueError(
                f"prefix required, usage example: "
                f"`class {cls.__name__}(Payload, prefix='my_callback'): ...`",
            )

        cls.__separator__ = kwargs.pop("sep", ":")
        cls.__prefix__ = kwargs.pop("prefix")

        if cls.__separator__ in cls.__prefix__:
            raise ValueError(
                f"Separator symbol {cls.__separator__!r} "
                f"can not be used inside prefix {cls.__prefix__!r}",
            )

        super().__init_subclass__(**kwargs)

    def _encode_value(self, key: str, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, Enum):
            return str(value.value)
        if isinstance(value, UUID):
            return value.hex
        if isinstance(value, bool):
            return str(int(value))
        if isinstance(value, (int, str, float, Decimal, Fraction)):
            return str(value)
        msg = (
            f"Attribute {key}={value!r} of type {type(value).__name__!r}"
            f" can not be packed to callback data"
        )
        raise ValueError(msg)

    def pack(self) -> str:
        result = [self.__prefix__]
        for key, value in dataclasses.asdict(self).items():
            encoded = self._encode_value(key, value)
            if self.__separator__ in encoded:
                msg = (
                    f"Separator symbol {self.__separator__!r} can not be used "
                    f"in value {key}={encoded!r}"
                )
                raise ValueError(msg)
            result.append(encoded)
        payload = self.__separator__.join(result)
        if len(payload.encode()) > MAX_PAYLOAD_LENGTH:
            msg = (
                f"Resulted callback data is too long! "
                f"len({payload!r}.encode()) > {MAX_PAYLOAD_LENGTH}"
            )
            raise ValueError(msg)
        return payload

    @classmethod
    def _decode_value(cls, field: dataclasses.Field, raw_value: str) -> Any:
        is_empty = raw_value == ""

        if is_empty:
            if _check_field_is_nullable(field):
                if field.default is not dataclasses.MISSING:
                    return field.default
                if field.default_factory is not dataclasses.MISSING:
                    return field.default_factory()
                return None
            raise ValueError(f"Empty value for non-nullable field {field.name}")

        field_type = field.type
        origin = get_origin(field_type)
        args = get_args(field_type)

        if origin in _UNION_TYPES and type(None) in args:
            non_none_types = [t for t in args if t is not type(None)]
            if len(non_none_types) == 1:
                field_type = non_none_types[0]
            else:
                field_type = str

        if field_type is int:
            return int(raw_value)
        if field_type is float:
            return float(raw_value)
        if field_type is bool:
            return raw_value == "1"
        if field_type is Decimal:
            return Decimal(raw_value)
        if field_type is Fraction:
            return Fraction(raw_value)
        if field_type is UUID:
            return UUID(hex=raw_value)
        if issubclass(field_type, Enum):
            return field_type(raw_value)

        return raw_value

    @classmethod
    def unpack(cls, value: str) -> Self:
        prefix, *parts = value.split(cls.__separator__)
        fields = dataclasses.fields(cls)

        if prefix != cls.__prefix__:
            msg = f"Bad prefix ({prefix!r} != {cls.__prefix__!r})"
            raise ValueError(msg)
        if len(parts) != len(fields):
            msg = (
                f"Callback data {cls.__name__!r} takes {len(fields)} arguments "
                f"but {len(parts)} were given"
            )
            raise TypeError(msg)

        payload = {}
        for field, raw in zip(fields, parts, strict=True):
            try:
                decoded = cls._decode_value(field, raw)
            except Exception as e:
                raise ValueError(
                    f"Cannot decode {field.name}={raw!r} to {field.type}",
                ) from e
            payload[field.name] = decoded

        return cls(**payload)

    @classmethod
    def filter(
        cls,
        filter: Filter[MessageCallback] | None = None,
    ) -> "MessageCallbackFilter":
        return MessageCallbackFilter(payload=cls, filter=filter)


class MessageCallbackFilter(BaseFilter[MessageCallback]):
    __slots__ = (
        "filter",
        "payload",
    )

    def __init__(
        self,
        *,
        payload: type[Payload],
        filter: Filter[MessageCallback] | None,
    ) -> None:
        self.payload = payload
        self.filter = filter

    def __str__(self) -> str:
        return self._signature_to_string(
            payload=self.payload,
            filter=self.filter,
        )

    async def __call__(
        self,
        update: MessageCallback,
        ctx: Ctx,
    ) -> bool:
        if not isinstance(update, MessageCallback) or not update.payload:
            return False
        try:
            payload = self.payload.unpack(update.payload)
        except (TypeError, ValueError):
            return False

        ctx["payload"] = payload

        if self.filter is None:
            return True

        result = False
        try:
            result = await self.filter(update, ctx)
        finally:
            if not result:
                ctx.pop("payload", None)

        return result


def _check_field_is_nullable(field: dataclasses.Field) -> bool:
    if (
        field.default is not dataclasses.MISSING
        or field.default_factory is not dataclasses.MISSING
    ):
        return True

    origin = get_origin(field.type)
    if origin in _UNION_TYPES or origin is typing.Union:
        args = get_args(field.type)
        return type(None) in args

    return False

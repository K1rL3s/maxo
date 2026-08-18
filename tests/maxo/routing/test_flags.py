from typing import Any

import pytest

import maxo
from maxo.routing.ctx import Ctx
from maxo.routing.flags import (
    FLAG_ATTR_NAME,
    HANDLER_KEY,
    AttrDict,
    Flag,
    FlagDecorator,
    FlagGenerator,
    extract_flags,
    extract_flags_from_object,
    flags,
    get_flag,
)
from maxo.types import MessageCreated
from tests.factories import make_flagged_handler


@pytest.fixture
def flag() -> Flag:
    return Flag("test", True)


@pytest.fixture
def flag_decorator(flag: Flag) -> FlagDecorator:
    return FlagDecorator(flag)


class TestExports:
    def test_flags_exported_from_top_level(self) -> None:
        assert maxo.flags is flags

    def test_flags_is_generator(self) -> None:
        assert isinstance(flags, FlagGenerator)


class TestFlagDecorator:
    def test_with_value(self, flag_decorator: FlagDecorator) -> None:
        new_decorator = flag_decorator._with_value("value")

        assert new_decorator is not flag_decorator
        assert new_decorator.flag is not flag_decorator.flag
        assert new_decorator.flag.name == "test"
        assert new_decorator.flag.value == "value"

    @pytest.mark.parametrize("value", [True, False, 0])
    def test_value_and_kwargs_together_is_error(
        self,
        value: Any,
        flag_decorator: FlagDecorator,
    ) -> None:
        with pytest.raises(ValueError, match="вместе"):
            flag_decorator(value, test=True)  # type: ignore[call-overload]

    def test_call_with_function(self, flag_decorator: FlagDecorator) -> None:
        async def func(update: MessageCreated) -> None:
            pass

        decorated = flag_decorator(func)

        assert decorated is func
        assert getattr(decorated, FLAG_ATTR_NAME) == {"test": True}

    def test_call_with_arg(self, flag_decorator: FlagDecorator) -> None:
        new_decorator = flag_decorator("hello")

        assert new_decorator is not flag_decorator
        assert new_decorator.flag.value == "hello"

    def test_call_with_none(self, flag_decorator: FlagDecorator) -> None:
        new_decorator = flag_decorator(None)

        assert new_decorator.flag.value is None

    def test_call_without_args(self, flag_decorator: FlagDecorator) -> None:
        new_decorator = flag_decorator()

        assert new_decorator.flag.value == {}

    def test_call_with_kwargs(self, flag_decorator: FlagDecorator) -> None:
        new_decorator = flag_decorator(spam=True)

        assert new_decorator is not flag_decorator
        assert isinstance(new_decorator.flag.value, AttrDict)
        assert new_decorator.flag.value["spam"] is True
        assert new_decorator.flag.value.spam is True

    def test_decorators_stack(self) -> None:
        @flags.first
        @flags.second("value")
        async def func(update: MessageCreated) -> None:
            pass

        assert extract_flags_from_object(func) == {"first": True, "second": "value"}


class TestFlagGenerator:
    def test_getattr_returns_new_decorators(self) -> None:
        generator = FlagGenerator()

        assert isinstance(generator.foo, FlagDecorator)
        assert isinstance(generator.bar, FlagDecorator)
        assert generator.foo is not generator.foo
        assert generator.foo is not generator.bar

    def test_flag_name_and_default_value(self) -> None:
        decorator = FlagGenerator().foo

        assert decorator.flag == Flag("foo", True)

    def test_underscore_name_is_forbidden(self) -> None:
        generator = FlagGenerator()

        with pytest.raises(AttributeError):
            generator._something  # noqa: B018


class TestExtractFlagsFromObject:
    def test_object_without_flags(self) -> None:
        async def func(update: MessageCreated) -> None:
            pass

        assert extract_flags_from_object(func) == {}

    def test_object_with_flags(self) -> None:
        async def func(update: MessageCreated) -> None:
            pass

        setattr(func, FLAG_ATTR_NAME, {"test": True})

        assert extract_flags_from_object(func) == {"test": True}


class TestExtractFlags:
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            (None, {}),
            ({}, {}),
            ({"handler": None}, {}),
            ({"spam": "eggs"}, {}),
        ],
    )
    def test_without_flags(self, source: Any, expected: dict[str, Any]) -> None:
        assert extract_flags(source) == expected

    def test_from_handler(self) -> None:
        handler = make_flagged_handler(test=True)

        assert extract_flags(handler) == {"test": True}

    def test_from_ctx(self) -> None:
        ctx = Ctx({HANDLER_KEY: make_flagged_handler(test=True)})

        assert extract_flags(ctx) == {"test": True}


class TestGetFlag:
    @pytest.mark.parametrize(
        ("source", "name", "default", "expected"),
        [
            (None, "test", None, None),
            (None, "test", 42, 42),
            ({}, "test", None, None),
            ({}, "test", 42, 42),
            ({"handler": None}, "test", None, None),
            ({"handler": None}, "test", 42, 42),
        ],
    )
    def test_default(
        self,
        source: Any,
        name: str,
        default: Any,
        expected: Any,
    ) -> None:
        assert get_flag(source, name, default=default) == expected

    def test_existing_flag(self) -> None:
        ctx = Ctx({HANDLER_KEY: make_flagged_handler(test=True)})

        assert get_flag(ctx, "test") is True

    def test_missing_flag_with_default(self) -> None:
        ctx = Ctx({HANDLER_KEY: make_flagged_handler(test=True)})

        assert get_flag(ctx, "spam") is None
        assert get_flag(ctx, "spam", default=42) == 42

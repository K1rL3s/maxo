import inspect
from unittest.mock import MagicMock

from adaptix import Retort

from maxo.bot import Bot, methods
from maxo.bot.methods.base import MaxoMethod
from maxo.bot.warming_up import _METHOD_ROOTS, WarmingUpType, warming_up_retort
from maxo.serialization import create_retort, create_retort_with_bot
from maxo.types import Updates


def _exported_methods() -> set[type[MaxoMethod[object]]]:
    exported = (getattr(methods, name) for name in methods.__all__)
    return {
        value
        for value in exported
        if inspect.isclass(value)
        and issubclass(value, MaxoMethod)
        and value is not MaxoMethod
    }


def test_every_exported_method_is_a_warming_up_root() -> None:
    missing = _exported_methods() - set(_METHOD_ROOTS)

    assert not missing, sorted(method.__name__ for method in missing)


def test_warming_up_roots_are_exported_methods() -> None:
    extra = set(_METHOD_ROOTS) - _exported_methods()

    assert not extra, sorted(method.__name__ for method in extra)


def test_retort_builds_with_warming_up() -> None:
    create_retort(warming_up=True)
    create_retort_with_bot(MagicMock(spec=Bot), warming_up=True)


def test_warming_up_builds_serializers_of_api_calls() -> None:
    retort = MagicMock(spec=Retort)

    warming_up_retort(retort, WarmingUpType.TYPES)
    warming_up_retort(retort, WarmingUpType.METHOD)

    loaded = {call.args[0] for call in retort.get_loader.call_args_list}
    dumped = {call.args[0] for call in retort.get_dumper.call_args_list}
    exported = _exported_methods()
    assert {Updates, *(method.__returning__ for method in exported)} <= loaded
    assert exported <= dumped

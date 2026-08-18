"""Полнота регистрации апдейтов: union -> observers -> фасады.

Тест параметризован по `Updates`, поэтому новый апдейт попадает под проверку
сам. Ловит два тихих пропуска, которые иначе доживают до рантайма: забытый
observer в `Router` и забытую запись в `_FACADES_MAP`.

Регистрацию в `TAG_PROVIDERS` он не покрывает - на каждый новый апдейт всё ещё
нужен свой тест «сырой JSON -> retort -> тип».
"""

import typing
from typing import Any

import pytest

from maxo import Router
from maxo.routing.facades.middleware import _FACADES_MAP
from maxo.types import Updates

UPDATE_TYPES: tuple[Any, ...] = typing.get_args(Updates)


@pytest.mark.parametrize("update_tp", UPDATE_TYPES, ids=lambda tp: tp.__name__)
def test_update_has_observer(update_tp: Any) -> None:
    assert update_tp in Router().observers


@pytest.mark.parametrize("update_tp", UPDATE_TYPES, ids=lambda tp: tp.__name__)
def test_update_has_facade(update_tp: Any) -> None:
    assert update_tp in _FACADES_MAP


@pytest.mark.parametrize("update_tp", UPDATE_TYPES, ids=lambda tp: tp.__name__)
def test_update_type_is_unique(update_tp: Any) -> None:
    same_type = [tp for tp in UPDATE_TYPES if tp.type is update_tp.type]

    assert same_type == [update_tp]

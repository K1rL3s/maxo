"""Полнота регистрации апдейтов: union -> observers.

Тест параметризован по `Updates`, поэтому новый апдейт попадает под проверку
сам. Ловит тихий пропуск, который иначе доживает до рантайма: забытый
observer в `Router`.
"""

import typing
from typing import Any

import pytest

from maxo import Router
from maxo.types import Updates

UPDATE_TYPES: tuple[Any, ...] = typing.get_args(Updates)


@pytest.mark.parametrize("update_tp", UPDATE_TYPES, ids=lambda tp: tp.__name__)
def test_update_has_observer(update_tp: Any) -> None:
    assert update_tp in Router().observers


@pytest.mark.parametrize("update_tp", UPDATE_TYPES, ids=lambda tp: tp.__name__)
def test_update_type_is_unique(update_tp: Any) -> None:
    same_type = [tp for tp in UPDATE_TYPES if tp.type is update_tp.type]

    assert same_type == [update_tp]

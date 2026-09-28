"""Регрессионный тест на issue #241.

`Omitted` - синглтон через `SingletonMeta.__call__`, но `copy`, `deepcopy`
и `pickle` создают объект в обход метакласса (`cls.__new__(cls)`), а
`Omitted` не определяет ни `__eq__`, ни `__reduce__`/`__copy__`/`__deepcopy__`.
Из-за этого копия синглтона не равна оригиналу, и любой `MaxoType` с
`Omittable`-полем теряет `==` после `copy`/`deepcopy`/pickle-round-trip,
хотя видимые (не-`Omitted`) поля совпадают.

Правильный фикс - в upstream `unihttp` (правило `butcher/AGENTS.md`:
«проблема в генераторе - чини в upstream»). Этот тест фиксирует текущее
(баговое) поведение, чтобы апстрим-фикс не прошёл незамеченным: как только
`unihttp` добавит `Omitted.__eq__`/`__reduce__`, эти assert'ы начнут падать
и станет сигналом обновить/удалить тест.
"""

import copy
import pickle

from maxo.omit import Omitted
from maxo.types.upload_endpoint import UploadEndpoint


def test_omitted_copy_breaks_identity() -> None:
    original = Omitted()

    copied = copy.copy(original)

    assert copied is not original


def test_omitted_deepcopy_breaks_identity_and_equality() -> None:
    original = Omitted()

    copied = copy.deepcopy(original)

    assert copied is not original
    assert copied != original


def test_omitted_pickle_roundtrip_breaks_identity_and_equality() -> None:
    original = Omitted()

    restored = pickle.loads(pickle.dumps(original))  # noqa: S301

    assert restored is not original
    assert restored != original


def test_omitted_is_still_falsy_and_reprs_the_same_after_copy() -> None:
    # is_omitted()/bool() keep working after copy - только identity/equality
    # ломаются, потому что они завязаны на isinstance, а не на `is`/`==`.
    original = Omitted()

    copied = copy.deepcopy(original)

    assert bool(copied) is False
    assert repr(copied) == repr(original) == "<Omitted>"


def test_maxo_type_with_omittable_field_loses_equality_after_deepcopy() -> None:
    endpoint = UploadEndpoint(url="https://example.com/upload")

    copied = copy.deepcopy(endpoint)

    # Видимое поле совпадает...
    assert copied.url == endpoint.url
    # ...но Omittable-поле и весь датакласс - нет, хотя оба всё ещё
    # печатаются как <Omitted> и выглядят идентично.
    assert copied.token != endpoint.token
    assert copied != endpoint


def test_maxo_type_with_omittable_field_loses_equality_after_pickle() -> None:
    endpoint = UploadEndpoint(url="https://example.com/upload")

    restored = pickle.loads(pickle.dumps(endpoint))  # noqa: S301

    assert restored.url == endpoint.url
    assert restored.token != endpoint.token
    assert restored != endpoint

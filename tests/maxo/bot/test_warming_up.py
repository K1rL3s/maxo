import gc
import linecache
import re
from collections.abc import Iterator
from typing import Any

import pytest

from maxo import Bot
from maxo.bot.warming_up import eager_cycle_collection
from maxo.routing.updates import MessageCreated
from maxo.types import UpdateList

TOKEN = "token"  # noqa: S105

_GENERATED_PREFIX = "<adaptix generated "
_LOADER_PREFIX = "<adaptix generated model_loader_"
_UNIQUE_SUFFIX = re.compile(r" \d+>$")


def _drop_generated() -> None:
    for filename in tuple(linecache.cache):
        if filename.startswith(_GENERATED_PREFIX):
            linecache.cache.pop(filename, None)


def _generated(prefix: str = _GENERATED_PREFIX) -> list[str]:
    return [name for name in linecache.cache if name.startswith(prefix)]


@pytest.fixture
def keep_generated_sources(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """
    Оставляет исходники adaptix в `linecache`, чтобы посчитать кодогенерацию.

    Прогрев чистит их сам, поэтому иначе считать нечего.
    """
    monkeypatch.setattr("maxo.bot.warming_up._drop_generated_sources", lambda: None)
    _drop_generated()
    yield
    _drop_generated()


def test_warming_up_drops_generated_sources() -> None:
    Bot(token=TOKEN)

    assert _generated() == []


@pytest.mark.usefixtures("keep_generated_sources")
def test_warming_up_compiles_every_loader_once() -> None:
    """
    Каждая модель получает ровно один сгенерированный загрузчик.

    Chained-провайдеры maxo (теги, дефолты, привязка бота) раньше отдавали новую
    функцию-композицию на каждый запрос и промахивались мимо кеша кодогенерации
    adaptix, из-за чего одна и та же модель компилировалась до 26 раз.
    """
    Bot(token=TOKEN)

    compiled = _generated(_LOADER_PREFIX)
    distinct = {_UNIQUE_SUFFIX.sub(">", name) for name in compiled}

    assert len(compiled) == len(distinct)


def test_eager_cycle_collection_restores_gc_state() -> None:
    assert gc.get_freeze_count() == 0

    with eager_cycle_collection():
        assert gc.get_freeze_count() > 0

    assert gc.get_freeze_count() == 0


def test_eager_cycle_collection_unfreezes_on_error() -> None:
    with pytest.raises(RuntimeError), eager_cycle_collection():
        raise RuntimeError

    assert gc.get_freeze_count() == 0


def test_eager_cycle_collection_keeps_foreign_freeze() -> None:
    """
    Чужую заморозку (preload перед `fork`) трогать нельзя.

    `gc.unfreeze()` вернул бы объекты в обычные поколения и сломал бы
    copy-on-write у gunicorn или uwsgi.
    """
    gc.freeze()
    try:
        with eager_cycle_collection():
            pass

        assert gc.get_freeze_count() > 0
    finally:
        gc.unfreeze()


def test_eager_cycle_collection_skips_disabled_gc() -> None:
    gc.disable()
    try:
        with eager_cycle_collection():
            assert gc.get_freeze_count() == 0
    finally:
        gc.enable()

    assert gc.get_freeze_count() == 0


def test_warmed_bot_binds_itself_to_nested_types() -> None:
    bot = Bot(token=TOKEN)
    payload: dict[str, Any] = {
        "marker": 1,
        "updates": [
            {
                "update_type": "message_created",
                "timestamp": 1700000000000,
                "message": {
                    "timestamp": 1700000000000,
                    "recipient": {"chat_type": "dialog", "user_id": 1},
                    "body": {"mid": "mid", "seq": 1, "text": "hi"},
                },
            },
        ],
    }

    update = bot.retort.load(payload, UpdateList).updates[0]

    assert isinstance(update, MessageCreated)
    assert update.bot is bot
    assert update.message.bot is bot
    assert update.message.body.bot is bot

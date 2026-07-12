from unittest.mock import MagicMock

from magic_filter import F as OriginF, MagicFilter as OriginMagicFilter
from magic_filter.operations import CallOperation, SelectorOperation

from maxo import Ctx
from maxo.dialogs.integrations.magic_filter import DialogMagic
from maxo.dialogs.widgets.common import Whenable
from maxo.enums import ChatType
from maxo.integrations.magic_filter import F, MagicData, MagicFilter
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.filters import AlwaysFalseFilter, AlwaysTrueFilter
from maxo.routing.filters.logic import AndFilter, OrFilter
from maxo.routing.sentinels import UNHANDLED
from maxo.types import Message, MessageBody, MessageCreated, Recipient, User
from tests.constants import NOW
from tests.factories import make_bot


def make_update(text: str | None = "hi") -> MessageCreated:
    return MessageCreated(
        message=Message(
            body=MessageBody(mid="test", seq=1, text=text),
            recipient=Recipient(chat_type=ChatType.DIALOG, chat_id=1),
            timestamp=NOW,
            sender=User(
                user_id=1,
                first_name="Test",
                is_bot=False,
                last_activity_time=NOW,
            ),
        ),
        timestamp=NOW,
    )


async def test_magic_data_custom_cast() -> None:
    magic_data = MagicData(F["item"].cast(str), result_key="result")

    ctx = Ctx({"item": 42})
    result = await magic_data(None, ctx)

    assert result is True
    assert ctx["result"] == "42"
    assert isinstance(ctx["result"], str)


def test_every_magic_node_is_a_maxo_filter() -> None:
    assert isinstance(F, MagicFilter)
    assert isinstance(F.text, MagicFilter)
    assert isinstance(F.text == "hi", MagicFilter)
    assert isinstance(F.text.casefold(), MagicFilter)
    assert isinstance(F.text.in_({"a"}), MagicFilter)
    assert isinstance(F["item"], MagicFilter)

    # И при этом остается магией `magic_filter`
    assert isinstance(F.text, OriginMagicFilter)
    assert F is not OriginF


async def test_bare_magic_works_as_filter() -> None:
    ctx = Ctx({})
    has_text = F.message.body.text

    assert await has_text(make_update("hi"), ctx) is True
    assert await has_text(make_update(None), ctx) is False


async def test_predicate_resolves() -> None:
    ctx = Ctx({})
    magic_filter = F.text == "hi"

    assert await magic_filter(make_update("hi"), ctx) is True
    assert await magic_filter(make_update("bye"), ctx) is False


async def test_method_call_in_chain_is_not_a_filter_call() -> None:
    # `F.text.casefold()` должен строить магию, а не звать фильтр
    chain = F.text.casefold()

    assert isinstance(chain._operations[-1], CallOperation)
    assert await (chain == "отмена")(make_update("ОТМЕНА"), Ctx({})) is True


async def test_magic_combines_with_magic_as_magic() -> None:
    ctx = Ctx({})

    ored = (F.text == "a") | (F.text == "b")
    inverted = ~F.message.body.text

    assert isinstance(ored, MagicFilter)
    assert isinstance(inverted, MagicFilter)

    assert await ored(make_update("b"), ctx) is True
    assert await ored(make_update("c"), ctx) is False
    assert await inverted(make_update(None), ctx) is True
    assert await inverted(make_update("hi"), ctx) is False


async def test_magic_combines_with_maxo_filter_as_logic_filter() -> None:
    ctx = Ctx({})

    anded = (F.text == "hi") & AlwaysTrueFilter()
    reversed_anded = AlwaysTrueFilter() & (F.text == "hi")
    ored = (F.text == "hi") | AlwaysFalseFilter()

    assert isinstance(anded, AndFilter)
    assert isinstance(reversed_anded, AndFilter)
    assert isinstance(ored, OrFilter)

    assert await anded(make_update("hi"), ctx) is True
    assert await anded(make_update("bye"), ctx) is False
    assert await reversed_anded(make_update("hi"), ctx) is True
    assert await ored(make_update("hi"), ctx) is True


def test_nested_selector_stays_magic() -> None:
    selector = F.items[F.price > 100]
    origin_selector = OriginF.items[OriginF.price > 100]

    assert [type(op) for op in selector._operations] == [
        type(op) for op in origin_selector._operations
    ]
    assert isinstance(selector._operations[-1], SelectorOperation)


async def test_result_key_puts_value_into_ctx() -> None:
    ctx = Ctx({})
    magic_filter = MagicFilter(F.message.body.text, result_key="text")

    assert await magic_filter(make_update("hello"), ctx) is True
    assert ctx["text"] == "hello"


async def test_result_key_is_not_set_when_filter_fails() -> None:
    ctx = Ctx({})
    magic_filter = MagicFilter(F.message.body.text, result_key="text")

    assert await magic_filter(make_update(None), ctx) is False
    assert "text" not in ctx


def test_magic_is_dialog_magic() -> None:
    assert isinstance(F.text, DialogMagic)
    assert isinstance(F.text == "hi", DialogMagic)


def test_magic_works_in_dialog_when() -> None:
    manager = MagicMock()

    predicate = Whenable(when=F["count"] > 1)
    assert predicate.is_({"count": 2}, manager) is True
    assert predicate.is_({"count": 0}, manager) is False

    truthy = Whenable(when=F["selected"])
    assert truthy.is_({"selected": ["a"]}, manager) is True
    assert truthy.is_({"selected": []}, manager) is False

    inverted = Whenable(when=~F["selected"])
    assert inverted.is_({"selected": []}, manager) is True


async def test_magic_works_as_handler_filter() -> None:
    dp = Dispatcher()
    handled: list[str] = []

    @dp.message_created(F.message.body.text == "hi")
    async def handler(update: MessageCreated) -> str:
        handled.append(update.message.body.text or "")
        return "ok"

    bot = make_bot()

    assert await dp.feed_update(make_update("hi"), bot) == "ok"
    assert await dp.feed_update(make_update("bye"), bot) is UNHANDLED
    assert handled == ["hi"]


async def test_result_key_reaches_handler() -> None:
    dp = Dispatcher()
    seen: list[str] = []

    @dp.message_created(MagicFilter(F.message.body.text, result_key="text"))
    async def handler(update: MessageCreated, text: str) -> str:
        seen.append(text)
        return "ok"

    assert await dp.feed_update(make_update("hello"), make_bot()) == "ok"
    assert seen == ["hello"]

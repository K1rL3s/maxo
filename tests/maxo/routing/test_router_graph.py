import pytest

from maxo import Router
from maxo.errors import CycleRoutersError, RouterAlreadyIncludedError
from maxo.errors.state import StateError
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.signals import BeforeStartup
from maxo.routing.utils.validate_router_graph import validate_router_graph
from maxo.types import MessageCallback, MessageCreated, MessageEdited


def test_include_many_routers() -> None:
    router = Router("root")
    child1 = Router("child1")
    child2 = Router("child2")

    router.include(child1, child2)

    assert list(router.children_routers) == [child1, child2]


def test_aiogram_compatible_include_aliases() -> None:
    router = Router("root")
    child1 = Router("child1")
    child2 = Router("child2")

    router.include_router(child1)
    router.include_routers(child2)

    assert list(router.children_routers) == [child1, child2]


def test_router_observers_and_aliases_are_configured() -> None:
    router = Router("root")

    assert router.observers[MessageCreated] is router.message_created
    assert router.observers[MessageCallback] is router.message_callback
    assert router.observers[MessageEdited] is router.message_edited
    assert router.message is router.message_created
    assert router.callback_query is router.message_callback
    assert router.edited_message is router.message_edited
    assert router.exception is router.exceptions
    assert router.exception is router.error
    assert router.exception is router.errors


def test_validate_router_graph_accepts_tree() -> None:
    router = Router("root")
    child = Router("child")
    grandchild = Router("grandchild")

    router.include(child)
    child.include(grandchild)

    validate_router_graph(router)


def test_validate_router_graph_rejects_self_reference() -> None:
    router = Router("root")
    router.include(router)

    with pytest.raises(CycleRoutersError) as exc_info:
        validate_router_graph(router)

    assert exc_info.value.routers == [router]
    assert "Cycle routers detected" in str(exc_info.value)


def test_validate_router_graph_rejects_deep_cycle() -> None:
    router = Router("root")
    child = Router("child")
    grandchild = Router("grandchild")

    router.include(child)
    child.include(grandchild)
    grandchild.include(router)

    with pytest.raises(CycleRoutersError) as exc_info:
        validate_router_graph(router)

    assert exc_info.value.routers == [router, child, grandchild]


async def test_dispatcher_validates_router_graph_on_startup() -> None:
    dp = Dispatcher()
    child = Router("child")

    dp.include(child)
    child.include(dp)

    with pytest.raises(CycleRoutersError):
        await dp.feed_signal(BeforeStartup())


async def test_router_cannot_include_children_after_startup() -> None:
    dp = Dispatcher()

    await dp.feed_signal(BeforeStartup())

    with pytest.raises(StateError, match="Routers cannot be include after startup"):
        dp.include(Router("late"))


async def test_observer_cannot_be_modified_after_startup() -> None:
    dp = Dispatcher()

    await dp.feed_signal(BeforeStartup())

    async def handler(_: MessageCreated) -> None:
        return None

    with pytest.raises(StateError, match="Can't add handler after startup"):
        dp.message_created.handler(handler)


def test_include_sets_parent_router() -> None:
    root = Router("root")
    child = Router("child")
    grandchild = Router("grandchild")

    root.include(child)
    child.include(grandchild)

    assert root.parent_router is None
    assert child.parent_router is root
    assert grandchild.parent_router is child


def test_include_rejects_router_with_another_parent() -> None:
    dp = Dispatcher()
    a = Router("a")
    b = Router("b")
    c = Router("c")
    dp.include(a, b)
    a.include(c)

    with pytest.raises(RouterAlreadyIncludedError) as exc_info:
        b.include(c)

    assert exc_info.value.router is c
    assert exc_info.value.parent_router is a
    assert str(exc_info.value) == "<Router 'c'> is already included into <Router 'a'>"
    assert list(b.children_routers) == []

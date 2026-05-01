"""Тесты отложенного render в manager.start/done из callback - закрывает п.3 issue #110."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.dialogs.manager.manager import ManagerImpl


@pytest.mark.asyncio
async def test_start_inside_callback_defers_show() -> None:
    """_start_normal в режиме defer не зовёт show, ставит _pending_show=True."""
    mgr = MagicMock(spec=ManagerImpl)
    mgr._defer_show = True
    mgr._pending_show = False
    mgr.show = AsyncMock()
    mgr.has_context = MagicMock(return_value=False)
    mgr._registry = MagicMock()
    mgr._registry.find_dialog = MagicMock(return_value=MagicMock(launch_mode=MagicMock()))
    mgr._process_launch_mode = AsyncMock()
    mgr._ctx = {}

    stack = MagicMock()
    stack.empty = MagicMock(return_value=True)
    stack.access_settings = None
    new_ctx = MagicMock()
    new_ctx.id = "ctx_id"
    stack.push = MagicMock(return_value=new_ctx)
    mgr.current_stack = MagicMock(return_value=stack)
    mgr.dialog = MagicMock(return_value=MagicMock(process_start=AsyncMock()))
    mgr._current_context_unsafe = MagicMock(return_value=new_ctx)

    await ManagerImpl._start_normal(mgr, state=MagicMock(), data=None, access_settings=None)

    mgr.show.assert_not_called()
    assert mgr._pending_show is True


@pytest.mark.asyncio
async def test_start_outside_callback_renders_immediately() -> None:
    """_start_normal вне callback (defer_show=False) рендерит сразу через show()."""
    mgr = MagicMock(spec=ManagerImpl)
    mgr._defer_show = False
    mgr._pending_show = False
    mgr.show = AsyncMock()
    mgr.has_context = MagicMock(return_value=False)
    mgr._registry = MagicMock()
    mgr._registry.find_dialog = MagicMock(return_value=MagicMock(launch_mode=MagicMock()))
    mgr._process_launch_mode = AsyncMock()
    mgr._ctx = {}
    mgr.storage = MagicMock(return_value=AsyncMock())

    stack = MagicMock()
    stack.empty = MagicMock(return_value=True)
    stack.access_settings = None
    new_ctx = MagicMock()
    new_ctx.id = "ctx_id"
    stack.push = MagicMock(return_value=new_ctx)
    mgr.current_stack = MagicMock(return_value=stack)
    mgr.dialog = MagicMock(return_value=MagicMock(process_start=AsyncMock()))
    mgr._current_context_unsafe = MagicMock(return_value=new_ctx)

    await ManagerImpl._start_normal(mgr, state=MagicMock(), data=None, access_settings=None)

    mgr.show.assert_awaited_once()
    assert mgr._pending_show is False


@pytest.mark.asyncio
async def test_done_inside_callback_defers_show() -> None:
    """done() из callback (defer_show=True) тоже откладывает show."""
    mgr = MagicMock(spec=ManagerImpl)
    mgr._defer_show = True
    mgr._pending_show = False
    mgr.show = AsyncMock()
    mgr.show_mode = MagicMock()
    mgr.check_disabled = MagicMock()
    mgr.mark_closed = AsyncMock()

    old_context = MagicMock()
    old_context.id = "old_id"
    old_context.start_data = None
    same_context = MagicMock()
    same_context.id = "old_id"

    mgr.current_context = MagicMock(return_value=old_context)
    mgr._current_context_unsafe = MagicMock(return_value=same_context)
    mgr.dialog = MagicMock(return_value=MagicMock(
        process_close=AsyncMock(),
        process_result=AsyncMock(),
    ))

    await ManagerImpl.done(mgr, result=None, show_mode=None)

    mgr.show.assert_not_called()
    assert mgr._pending_show is True


@pytest.mark.asyncio
async def test_done_outside_callback_renders_immediately() -> None:
    """done() вне callback (defer_show=False) рендерит сразу."""
    mgr = MagicMock(spec=ManagerImpl)
    mgr._defer_show = False
    mgr._pending_show = False
    mgr.show = AsyncMock()
    mgr.show_mode = MagicMock()
    mgr.check_disabled = MagicMock()
    mgr.mark_closed = AsyncMock()

    old_context = MagicMock()
    old_context.id = "old_id"
    old_context.start_data = None
    same_context = MagicMock()
    same_context.id = "old_id"

    mgr.current_context = MagicMock(return_value=old_context)
    mgr._current_context_unsafe = MagicMock(return_value=same_context)
    mgr.dialog = MagicMock(return_value=MagicMock(
        process_close=AsyncMock(),
        process_result=AsyncMock(),
    ))

    await ManagerImpl.done(mgr, result=None, show_mode=None)

    mgr.show.assert_awaited_once()
    assert mgr._pending_show is False

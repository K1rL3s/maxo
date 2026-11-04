import asyncio
from collections.abc import Coroutine
from typing import Any

from maxo.loggers import webhook_tasks


class TaskTracker:
    __slots__ = ("_tasks",)

    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[Any]] = set()

    def spawn(self, coro: Coroutine[Any, Any, Any]) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._on_task_done)

    def _on_task_done(self, task: asyncio.Task[Any]) -> None:
        self._tasks.discard(task)
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            webhook_tasks.error(
                "Необработанное исключение в фоновой задаче вебхука",
                exc_info=exc,
            )

    async def close(self, timeout: float | None) -> None:
        if not self._tasks:
            return

        _, pending = await asyncio.wait(self._tasks, timeout=timeout)
        if not pending:
            return

        webhook_tasks.warning(
            "Фоновые задачи вебхука не завершились за %s с, отменено задач: %d",
            timeout,
            len(pending),
        )
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)

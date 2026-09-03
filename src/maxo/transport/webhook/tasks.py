import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

from maxo.loggers import webhook_tasks

TaskResultT = TypeVar("TaskResultT")


class TaskTracker:
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task[Any]] = set()

    def spawn(
        self,
        coro: Coroutine[Any, Any, TaskResultT],
    ) -> asyncio.Task[TaskResultT]:
        """
        Start a coroutine in the background and track it.

        :param coro: Coroutine to execute.
        :return: The created asyncio Task.
        """
        task = asyncio.create_task(coro)
        self._tasks.add(task)

        task.add_done_callback(self._on_task_done)
        return task

    def _on_task_done(self, task: asyncio.Task[Any]) -> None:
        """Remove the task from the set and log unhandled exceptions."""
        self._tasks.discard(task)

        if not task.cancelled():
            exc = task.exception()
            if exc:
                webhook_tasks.error(
                    "Unhandled exception in background task: %s",
                    exc,
                    exc_info=(type(exc), exc, exc.__traceback__),
                )

    async def close(self, timeout: float | None = 10.0) -> None:
        """
        Gracefully wait for all tracked tasks to complete.

        Cancel remaining tasks if the timeout is reached.

        :param timeout: Maximum time (in seconds) to wait before canceling.
        """
        if not self._tasks:
            return

        _done, pending = await asyncio.wait(
            self._tasks,
            timeout=timeout,
            return_when=asyncio.ALL_COMPLETED,
        )

        if pending:
            webhook_tasks.warning(
                "Timeout reached. Cancelling %s pending tasks.",
                len(pending),
            )
            for task in pending:
                task.cancel()

            # Wait for cancellations to process
            await asyncio.gather(*pending, return_exceptions=True)

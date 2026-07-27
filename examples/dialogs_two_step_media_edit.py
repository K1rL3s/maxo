"""
Баг iOS-клиента MAX: при edit_message "медиа -> медиа" рассинхронизируются
превью и файл. Обход - флаг Window(two_step_media_edit=True).
https://github.com/K1rL3s/maxo/issues/156
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any

from maxo import Bot, Dispatcher, Router
from maxo.dialogs import (
    Dialog,
    DialogManager,
    ShowMode,
    StartMode,
    Window,
    setup_dialogs,
)
from maxo.dialogs.api.entities import MediaAttachment
from maxo.dialogs.widgets.kbd import Button, SwitchTo
from maxo.dialogs.widgets.media import DynamicMedia
from maxo.dialogs.widgets.text import Const, Format
from maxo.enums import AttachmentType
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import MemoryStorage, SimpleEventIsolation
from maxo.routing.filters import CommandStart
from maxo.transport.long_polling import LongPolling
from maxo.types import MessageCallback, MessageCreated

FILES = Path(__file__).parent / "files"
LOGO_URL = (
    "https://raw.githubusercontent.com/K1rL3s/maxo/refs/heads/master"
    "/docs/_static/maxo-logo.png"
)
WATERMELON_URL = (
    "https://encrypted-tbn0.gstatic.com/images"
    "?q=tbn:ANd9GcTnpf8QOalaqiNp0HhiTbg7sPJ9HxynKn0n0TCD6eBj-sI3Ei_vjQM3Yt8&s=10"
)
TRANSITION_URL = (
    "https://raw.githubusercontent.com/K1rL3s/maxo/refs/heads/master"
    "/docs/_static/transitions-example.png"
)


MEDIA = [
    (
        "Фото файлом - 1",
        MediaAttachment(AttachmentType.IMAGE, path=FILES / "watermelon.jpg"),
    ),
    (
        "Фото файлом - 2",
        MediaAttachment(AttachmentType.IMAGE, path=FILES / "low-watermelon.png"),
    ),
    (
        "Фото файлом - 3",
        MediaAttachment(AttachmentType.IMAGE, path=FILES / "naked-watermelon.png"),
    ),
    ("Фото по url - 1", MediaAttachment(AttachmentType.IMAGE, url=LOGO_URL)),
    ("Фото по url - 2", MediaAttachment(AttachmentType.IMAGE, url=WATERMELON_URL)),
    ("Фото по url - 3", MediaAttachment(AttachmentType.IMAGE, url=TRANSITION_URL)),
    (
        "Видео файлом - 1",
        MediaAttachment(AttachmentType.VIDEO, path=FILES / "watermelon.mp4"),
    ),
    (
        "Видео файлом - 2",
        MediaAttachment(AttachmentType.VIDEO, path=FILES / "watermelon-dog.mp4"),
    ),
    (
        "Видео файлом - 3",
        MediaAttachment(AttachmentType.VIDEO, path=FILES / "watermelon-zombie.mp4"),
    ),
]


class SG(StatesGroup):
    bug = State()
    fix = State()


async def get_media(dialog_manager: DialogManager, **__: Any) -> dict[str, Any]:
    index = dialog_manager.dialog_data.get("index", 0) % len(MEDIA)
    title, media = MEDIA[index]
    return {"media": [media], "title": title}


async def on_back_media(
    _: MessageCallback,
    __: Button,
    manager: DialogManager,
) -> None:
    manager.dialog_data["index"] = manager.dialog_data.get("index", 0) - 1


async def on_next_media(
    _: MessageCallback,
    __: Button,
    manager: DialogManager,
) -> None:
    manager.dialog_data["index"] = manager.dialog_data.get("index", 0) + 1


media_dialog = Dialog(
    Window(
        DynamicMedia("media"),
        Format("Без обхода: {title}\nНа iOS превью и файл рассинхронизируются"),
        Button(Const("⬅️ Назад"), id="back", on_click=on_back_media),
        Button(Const("➡️ Вперёд"), id="next", on_click=on_next_media),
        SwitchTo(Const("🕸️ Окно с обходом"), id="to_fix", state=SG.fix),
        state=SG.bug,
        getter=get_media,
    ),
    Window(
        DynamicMedia("media"),
        Format("С обходом: {title}\nСообщение мигает после изменения"),
        Button(Const("⬅️ Назад"), id="back", on_click=on_back_media),
        Button(Const("➡️ Вперёд"), id="next", on_click=on_next_media),
        SwitchTo(Const("🐛 Окно с багом"), id="to_bug", state=SG.bug),
        state=SG.fix,
        getter=get_media,
        two_step_media_edit=True,
    ),
)

router = Router()


@router.message_created(CommandStart())
async def start(_: MessageCreated, dialog_manager: DialogManager) -> None:
    await dialog_manager.start(
        state=SG.bug,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.SEND,
    )


async def main() -> None:
    bot = Bot(os.environ["TOKEN"], warming_up=not __debug__)

    key_builder = DefaultKeyBuilder(with_destiny=True)
    events_isolation = SimpleEventIsolation(key_builder=key_builder)
    dp = Dispatcher(
        storage=MemoryStorage(key_builder=key_builder),
        events_isolation=events_isolation,
        key_builder=key_builder,
    )

    dp.include(router, media_dialog)
    setup_dialogs(dp)

    await LongPolling(dp).start(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(main())

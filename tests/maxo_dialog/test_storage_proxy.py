from typing import Any

import pytest

from maxo.dialogs.api.entities import DEFAULT_STACK_ID, AccessSettings, Stack
from maxo.dialogs.api.exceptions import UnknownIntent, UnknownState
from maxo.dialogs.context.storage import StorageProxy
from maxo.dialogs.test_tools.bot_client import FakeBot
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.enums import ChatType
from maxo.fsm import State, StatesGroup
from maxo.fsm.key_builder import DefaultKeyBuilder
from maxo.fsm.storages.memory import SimpleEventIsolation
from maxo.types import (
    Attachments,
    AudioAttachment,
    CallbackButton,
    ContactAttachment,
    FileAttachment,
    InlineKeyboardAttachment,
    LocationAttachment,
    PhotoAttachment,
    ShareAttachment,
    StickerAttachment,
    VideoAttachment,
)


async def test_save_load_stack_with_all_attachments() -> None:
    bot = FakeBot()
    chat_id = 123
    user_id = 456
    key_builder = DefaultKeyBuilder(with_destiny=True)
    storage = JsonMemoryStorage()

    storage_proxy = StorageProxy(
        storage=storage,
        events_isolation=SimpleEventIsolation(key_builder=key_builder),
        user_id=user_id,
        chat_id=chat_id,
        chat_type=ChatType.DIALOG,
        bot=bot,
        state_groups={},
    )

    last_attachments: list[Attachments] = [
        PhotoAttachment.factory(
            photo_id=1,
            token="photo_token",  # noqa: S106
            url="https://example.com/photo.jpg",
        ),
        VideoAttachment.factory(
            url="https://example.com/video.mp4",
            token="video_token",  # noqa: S106
        ),
        AudioAttachment.factory(
            url="https://example.com/audio.mp3",
            token="audio_token",  # noqa: S106
        ),
        FileAttachment.factory(
            url="https://example.com/file.txt",
            token="file_token",  # noqa: S106
            filename="file.txt",
            size=123,
        ),
        StickerAttachment.factory(
            url="https://example.com/sticker.webp",
            code="sticker_code",
            width=128,
            height=128,
        ),
        ContactAttachment.factory(),
        InlineKeyboardAttachment.factory(
            buttons=[[CallbackButton(text="test", payload="test_payload")]],
        ),
        ShareAttachment.factory(
            url="https://example.com",
            token="share_token",  # noqa: S106
        ),
        LocationAttachment(latitude=55.7558, longitude=37.6173),
    ]
    original_stack = Stack(
        _id="test_stack",
        intents=["a", "b"],
        last_message_id="12345",
        last_sequence_id=1,
        last_attachments=last_attachments,
    )

    await storage_proxy.save_stack(original_stack)
    loaded_stack = await storage_proxy.load_stack("test_stack")

    assert loaded_stack is not None
    assert loaded_stack.id == original_stack.id
    assert loaded_stack.intents == original_stack.intents
    assert loaded_stack.last_message_id == original_stack.last_message_id
    assert loaded_stack.last_sequence_id == original_stack.last_sequence_id
    assert loaded_stack.last_attachments == original_stack.last_attachments

    # Check that last_attachments are correctly deserialized
    assert len(loaded_stack.last_attachments) == 9
    assert isinstance(loaded_stack.last_attachments[0], PhotoAttachment)
    assert isinstance(loaded_stack.last_attachments[1], VideoAttachment)
    assert isinstance(loaded_stack.last_attachments[2], AudioAttachment)
    assert isinstance(loaded_stack.last_attachments[3], FileAttachment)
    assert isinstance(loaded_stack.last_attachments[4], StickerAttachment)
    assert isinstance(loaded_stack.last_attachments[5], ContactAttachment)
    assert isinstance(loaded_stack.last_attachments[6], InlineKeyboardAttachment)
    assert isinstance(loaded_stack.last_attachments[7], ShareAttachment)
    assert isinstance(loaded_stack.last_attachments[8], LocationAttachment)

    assert loaded_stack.last_attachments[0].payload.token == "photo_token"  # noqa: S105
    assert loaded_stack.last_attachments[1].payload.token == "video_token"  # noqa: S105
    assert loaded_stack.last_attachments[2].payload.token == "audio_token"  # noqa: S105
    assert loaded_stack.last_attachments[3].payload.token == "file_token"  # noqa: S105
    assert loaded_stack.last_attachments[4].payload.code == "sticker_code"
    button = loaded_stack.last_attachments[6].payload.buttons[0][0]
    assert isinstance(button, CallbackButton)
    assert button.payload == "test_payload"
    assert loaded_stack.last_attachments[7].payload.token == "share_token"  # noqa: S105
    assert loaded_stack.last_attachments[8].latitude == 55.7558


def make_proxy(state_groups: dict[str, Any] | None = None) -> StorageProxy:
    return StorageProxy(
        storage=JsonMemoryStorage(),
        events_isolation=SimpleEventIsolation(
            key_builder=DefaultKeyBuilder(with_destiny=True),
        ),
        user_id=456,
        chat_id=123,
        chat_type=ChatType.DIALOG,
        bot=FakeBot(),
        state_groups=state_groups if state_groups is not None else {"SG": SG},
    )


class SG(StatesGroup):
    first = State()


async def test_remove_context_clears_data() -> None:
    proxy = make_proxy()
    stack = Stack()
    context = stack.push(SG.first, {})
    await proxy.save_context(context)

    await proxy.remove_context(context.id)

    with pytest.raises(UnknownIntent):
        await proxy.load_context(context.id)


async def test_remove_stack_clears_data() -> None:
    proxy = make_proxy()
    stack = Stack()
    stack.push(SG.first, {})
    await proxy.save_stack(stack)

    await proxy.remove_stack(stack.id)

    assert (await proxy.load_stack(stack.id)).empty()


async def test_save_stack_ignores_none() -> None:
    await make_proxy().save_stack(None)


async def test_save_context_ignores_none() -> None:
    await make_proxy().save_context(None)


def test_state_of_unknown_group() -> None:
    with pytest.raises(UnknownState, match="Unknown state group"):
        make_proxy(state_groups={})._state("Missing:first")


def test_state_of_unknown_state_in_known_group() -> None:
    with pytest.raises(UnknownState, match="Unknown state"):
        make_proxy()._state("SG:missing")


def test_state_of_known_state() -> None:
    assert make_proxy()._state("SG:first") == SG.first


def test_parse_access_settings_none() -> None:
    assert make_proxy()._parse_access_settings(None) is None


def test_parse_access_settings_fills_defaults() -> None:
    settings = make_proxy()._parse_access_settings({"custom": "x"})

    assert settings is not None
    assert settings.user_ids == []
    assert settings.custom == "x"


def test_dump_access_settings_none() -> None:
    assert make_proxy()._dump_access_settings(None) is None


def test_dump_access_settings_roundtrip() -> None:
    proxy = make_proxy()
    dumped = proxy._dump_access_settings(AccessSettings(user_ids=[1], custom="c"))

    assert dumped == {"user_ids": [1], "custom": "c"}
    parsed = proxy._parse_access_settings(dumped)
    assert parsed is not None
    assert parsed.user_ids == [1]


async def test_save_load_stack_keeps_access_settings() -> None:
    proxy = make_proxy()
    stack = Stack(_id="restricted", access_settings=AccessSettings(user_ids=[1]))
    stack.push(SG.first, {})

    await proxy.save_stack(stack)
    loaded = await proxy.load_stack("restricted")

    assert loaded.access_settings is not None
    assert loaded.access_settings.user_ids == [1]


async def test_load_stack_without_access_settings_uses_default() -> None:
    proxy = make_proxy()
    await proxy.storage.set_data(
        key=proxy._stack_key(DEFAULT_STACK_ID),
        data={
            "_id": DEFAULT_STACK_ID,
            "intents": ["a"],
            "last_message_id": None,
            "last_sequence_id": None,
            "last_attachments": [],
        },
    )

    loaded = await proxy.load_stack()

    assert loaded.intents == ["a"]
    assert loaded.access_settings is not None
    assert loaded.access_settings.user_ids == [456]

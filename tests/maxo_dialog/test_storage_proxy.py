from maxo.dialogs.api.entities import Stack
from maxo.dialogs.context.storage import StorageProxy
from maxo.dialogs.test_tools.bot_client import FakeBot
from maxo.dialogs.test_tools.memory_storage import JsonMemoryStorage
from maxo.enums import ChatType
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

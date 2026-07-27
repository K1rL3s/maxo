"""Тесты MessageManager - закрывают п.1 issue #110 (skip get_message_by_id в remove_inline_kbd)."""

from collections.abc import Sequence
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from maxo.dialogs.api.entities import (
    LinkPreviewOptions,
    MediaAttachment,
    MediaId,
    NewMessage,
    OldMessage,
    ShowMode,
)
from maxo.dialogs.api.protocols import MediaIdStorageProtocol, MessageNotModified
from maxo.dialogs.manager.message_manager import MessageManager
from maxo.enums import AttachmentRequestType, AttachmentType, ChatType, UploadType
from maxo.errors import MaxBotApiError, MaxBotBadRequestError
from maxo.omit import is_defined
from maxo.types import (
    Attachments,
    AttachmentsRequests,
    AudioAttachmentRequest,
    Callback,
    CallbackButton,
    FileAttachmentRequest,
    InlineKeyboardAttachment,
    Message,
    MessageBody,
    PhotoAttachment,
    PhotoAttachmentRequest,
    Recipient,
    SendMessageResult,
    User,
    VideoAttachmentRequest,
)
from maxo.utils.upload_media import FSInputFile
from tests.constants import NOW

IMAGE_MEDIA_ID = "image-id"
VIDEO_MEDIA_ID = "video-id"
AUDIO_MEDIA_ID = "audio-id"
FILE_MEDIA_ID = "file-id"
KEYBOARD_MEDIA_ID = "keyboard-id"


class StaticAttachmentsMessageManager(MessageManager):
    """Стаб _build_attachments; записывает медиа каждого рендера в built_media."""

    def __init__(self, media_id_storage: MediaIdStorageProtocol) -> None:
        super().__init__(media_id_storage)
        self.built_media: list[list[MediaAttachment]] = []

    async def _build_attachments(
        self,
        bot: object,
        keyboard: object,
        media: list[MediaAttachment],
    ) -> Sequence[AttachmentsRequests]:
        self.built_media.append(list(media))
        return []


def _make_old_message_with_kbd(mid: str = "55") -> OldMessage:
    return OldMessage(
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
        message_id=mid,
        sequence_id=int(mid),
        text="x",
        attachments=[InlineKeyboardAttachment.factory(buttons=[])],
    )


def _make_old_message(
    mid: str = "55",
    text: str | None = "old",
    attachments: list[Attachments] | None = None,
) -> OldMessage:
    return OldMessage(
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
        message_id=mid,
        sequence_id=int(mid),
        text=text,
        attachments=attachments or [],
    )


def _make_new_message(
    text: str | None = "new",
    show_mode: ShowMode = ShowMode.AUTO,
) -> NewMessage:
    return NewMessage(
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
        text=text,
        show_mode=show_mode,
    )


def _make_old_media_message(
    mid: str = "55",
    token: str = "old-token",  # noqa: S107
) -> OldMessage:
    return _make_old_message(
        mid=mid,
        text="old",
        attachments=[
            PhotoAttachment.factory(
                photo_id=1,
                token=token,
                url="http://e.com/old.png",
            ),
        ],
    )


def _make_new_media_message(
    show_mode: ShowMode = ShowMode.EDIT,
    two_step_media_edit: bool = True,
    media: list[MediaAttachment] | None = None,
) -> NewMessage:
    if media is None:
        media = [MediaAttachment(type=AttachmentType.IMAGE, url="http://e.com/new.png")]
    return NewMessage(
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
        text="new",
        show_mode=show_mode,
        two_step_media_edit=two_step_media_edit,
        media=media,
    )


def _media_with_token(
    token: str,
    media_type: AttachmentType = AttachmentType.IMAGE,
) -> MediaAttachment:
    return MediaAttachment(media_type, media_id=MediaId(token=token))


def _make_message(mid: str = "77", text: str | None = "sent") -> Message:
    return Message(
        body=MessageBody(mid=mid, seq=int(mid), text=text, attachments=[]),
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
        timestamp=NOW,
    )


def _make_callback() -> Callback:
    return Callback(
        callback_id="cb",
        timestamp=NOW,
        user=User(
            user_id=1,
            first_name="User",
            is_bot=False,
            last_activity_time=NOW,
        ),
    )


def _bad_request(message: str) -> MaxBotBadRequestError:
    return MaxBotBadRequestError(code="400", error="bad_request", message=message)


async def test_remove_inline_kbd_skips_refetch() -> None:
    """remove_inline_kbd не делает get_message_by_id после edit."""
    bot = AsyncMock()
    bot.edit_message = AsyncMock()
    bot.get_message_by_id = AsyncMock()
    mgr = MessageManager(media_id_storage=AsyncMock())

    result = await mgr.remove_inline_kbd(bot, _make_old_message_with_kbd(mid="55"))  # type: ignore[func-returns-value]

    bot.edit_message.assert_awaited_once()
    bot.get_message_by_id.assert_not_called()
    assert result is None


async def test_remove_kbd_no_update_returns_none() -> None:
    """remove_kbd с ShowMode.NO_UPDATE возвращает None."""
    mgr = MessageManager(media_id_storage=AsyncMock())
    result = await mgr.remove_kbd(  # type: ignore[func-returns-value]
        bot=AsyncMock(),
        show_mode=ShowMode.NO_UPDATE,
        old_message=None,
    )
    assert result is None


async def test_answer_callback_ignores_invalid_query_id() -> None:
    bot = AsyncMock()
    bot.answer_on_callback = AsyncMock(
        side_effect=MaxBotApiError(
            code="400",
            error="bad_request",
            message="query is too old and response timeout expired or query id is invalid",
        ),
    )
    mgr = MessageManager(media_id_storage=AsyncMock())

    await mgr.answer_callback(bot, _make_callback())

    bot.answer_on_callback.assert_awaited_once_with(
        callback_id="cb",
        notification="",
    )


async def test_answer_callback_reraises_other_api_errors() -> None:
    bot = AsyncMock()
    bot.answer_on_callback = AsyncMock(
        side_effect=MaxBotApiError(
            code="500",
            error="server",
            message="boom",
        ),
    )
    mgr = MessageManager(media_id_storage=AsyncMock())

    with pytest.raises(MaxBotApiError):
        await mgr.answer_callback(bot, _make_callback())


async def test_show_message_no_update_raises_not_modified() -> None:
    mgr = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())

    with pytest.raises(MessageNotModified, match="ShowMode is NO_UPDATE"):
        await mgr.show_message(
            bot=AsyncMock(),
            new_message=_make_new_message(show_mode=ShowMode.NO_UPDATE),
            old_message=None,
        )


async def test_show_message_send_combines_bot_result() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(
        return_value=SendMessageResult(message=_make_message(mid="77", text="new")),
    )
    mgr = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())

    old = await mgr.show_message(
        bot=bot,
        new_message=_make_new_message(text="new", show_mode=ShowMode.SEND),
        old_message=_make_old_message(text="old"),
    )

    assert old.message_id == "77"
    assert old.sequence_id == 77
    assert old.text == "new"


async def test_show_message_unchanged_returns_old_message() -> None:
    bot = AsyncMock()
    mgr = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())
    old_message = _make_old_message(text="same")

    result = await mgr.show_message(
        bot=bot,
        new_message=_make_new_message(text="same"),
        old_message=old_message,
    )

    assert result is old_message
    bot.send_message.assert_not_called()


async def test_show_message_delete_and_send_removes_old_message() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(
        return_value=SendMessageResult(message=_make_message(mid="88", text="new")),
    )
    mgr = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())

    result = await mgr.show_message(
        bot=bot,
        new_message=_make_new_message(text="new", show_mode=ShowMode.DELETE_AND_SEND),
        old_message=_make_old_message(text="old"),
    )

    bot.delete_message.assert_awaited_once_with(message_id="55")
    assert result.message_id == "88"


async def test_remove_inline_kbd_ignores_expected_bad_request_errors() -> None:
    mgr = MessageManager(media_id_storage=AsyncMock())
    old_message = _make_old_message_with_kbd()

    for message in (
        "message is not modified",
        "message can't be edited",
        "message to edit not found",
        "MESSAGE_ID_INVALID",
    ):
        bot = AsyncMock()
        bot.edit_message = AsyncMock(
            side_effect=MaxBotBadRequestError(
                code="400",
                error="bad_request",
                message=message,
            ),
        )

        await mgr.remove_inline_kbd(bot, old_message)


async def test_remove_inline_kbd_reraises_unexpected_bad_request() -> None:
    bot = AsyncMock()
    bot.edit_message = AsyncMock(
        side_effect=MaxBotBadRequestError(
            code="400",
            error="bad_request",
            message="different error",
        ),
    )
    mgr = MessageManager(media_id_storage=AsyncMock())

    with pytest.raises(MaxBotBadRequestError):
        await mgr.remove_inline_kbd(bot, _make_old_message_with_kbd())


async def test_remove_message_safe_falls_back_to_remove_keyboard() -> None:
    bot = AsyncMock()
    bot.delete_message = AsyncMock(
        side_effect=MaxBotBadRequestError(
            code="400",
            error="bad_request",
            message="message can't be deleted",
        ),
    )
    bot.edit_message = AsyncMock()
    mgr = MessageManager(media_id_storage=AsyncMock())

    await mgr.remove_message_safe(bot, _make_old_message_with_kbd(), None)

    bot.edit_message.assert_awaited_once()


async def test_edit_message_safe_sends_new_message_when_edit_not_found() -> None:
    bot = AsyncMock()
    bot.edit_message = AsyncMock(
        side_effect=MaxBotBadRequestError(
            code="400",
            error="bad_request",
            message="message to edit not found",
        ),
    )
    bot.send_message = AsyncMock(
        return_value=SendMessageResult(message=_make_message(mid="99", text="new")),
    )
    mgr = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())

    message = await mgr.edit_message_safe(
        bot,
        _make_new_message(text="new"),
        _make_old_message(text="old"),
    )

    assert message.body.mid == "99"


async def test_send_message_passes_link_preview_flag() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(
        return_value=SendMessageResult(message=_make_message(mid="77", text="new")),
    )
    mgr = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())

    await mgr.send_message(
        bot,
        NewMessage(
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
            text="new",
            link_preview_options=LinkPreviewOptions(is_disabled=True, url=None),
        ),
    )

    assert bot.send_message.await_args.kwargs["disable_link_preview"] is True


async def test_send_message_omits_link_preview_flag_when_options_absent() -> None:
    bot = AsyncMock()
    bot.send_message = AsyncMock(
        return_value=SendMessageResult(message=_make_message(mid="77", text="new")),
    )
    mgr = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())

    await mgr.send_message(bot, _make_new_message(text="new"))

    assert not is_defined(bot.send_message.await_args.kwargs["disable_link_preview"])


def test_convert_media_from_media_id_for_all_supported_types() -> None:
    mgr = MessageManager(media_id_storage=AsyncMock())

    image = mgr._convert_media(
        MediaAttachment(AttachmentType.IMAGE, media_id=MediaId(token=IMAGE_MEDIA_ID)),
    )
    video = mgr._convert_media(
        MediaAttachment(AttachmentType.VIDEO, media_id=MediaId(token=VIDEO_MEDIA_ID)),
    )
    audio = mgr._convert_media(
        MediaAttachment(AttachmentType.AUDIO, media_id=MediaId(token=AUDIO_MEDIA_ID)),
    )
    file = mgr._convert_media(
        MediaAttachment(AttachmentType.FILE, media_id=MediaId(token=FILE_MEDIA_ID)),
    )

    assert image is not None
    assert isinstance(image, PhotoAttachmentRequest)
    assert image.type == AttachmentRequestType.IMAGE
    assert isinstance(video, VideoAttachmentRequest)
    assert video.payload.token == VIDEO_MEDIA_ID
    assert isinstance(audio, AudioAttachmentRequest)
    assert audio.payload.token == AUDIO_MEDIA_ID
    assert isinstance(file, FileAttachmentRequest)
    assert file.payload.token == FILE_MEDIA_ID


def test_convert_media_from_url_and_path() -> None:
    mgr = MessageManager(media_id_storage=AsyncMock())

    image = mgr._convert_media(
        MediaAttachment(AttachmentType.IMAGE, url="https://example.com/image.png"),
    )
    file = mgr._convert_media(MediaAttachment(AttachmentType.FILE, path="file.txt"))

    assert image is not None
    assert isinstance(image, PhotoAttachmentRequest)
    assert image.payload.url == "https://example.com/image.png"
    assert isinstance(file, FSInputFile)
    assert file.path == "file.txt"
    assert file.type == UploadType.FILE


def test_convert_media_rejects_unsupported_url_type() -> None:
    mgr = MessageManager(media_id_storage=AsyncMock())

    with pytest.raises(ValueError, match="URL is supported only for IMAGE"):
        mgr._convert_media(
            MediaAttachment(AttachmentType.VIDEO, url="https://example.com/video.mp4"),
        )


def test_convert_media_warns_for_unknown_media_type() -> None:
    mgr = MessageManager(media_id_storage=AsyncMock())
    media = MediaAttachment(
        AttachmentType.INLINE_KEYBOARD,
        media_id=MediaId(token=KEYBOARD_MEDIA_ID),
    )

    with pytest.warns(RuntimeWarning, match="Unknown media attachment type"):
        assert mgr._convert_media(media) is None


class TestMessageChanged:
    def test_text_changed(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())

        assert manager._message_changed(_make_new_message("new"), _make_old_message())

    def test_keyboard_forces_change(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        new = _make_new_message("old")
        new.keyboard = [[CallbackButton(text="b", payload="p")]]

        assert manager._message_changed(new, _make_old_message(text="old"))

    def test_link_preview_forces_change(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        new = _make_new_message("old")
        new.link_preview_options = LinkPreviewOptions(is_disabled=True, url=None)

        assert manager._message_changed(new, _make_old_message(text="old"))

    def test_media_appeared(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        new = _make_new_message("old")
        new.media = [MediaAttachment(type=AttachmentType.IMAGE, url="http://e.com/a")]

        assert manager._message_changed(new, _make_old_message(text="old"))

    def test_nothing_changed(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())

        assert not manager._message_changed(
            _make_new_message("old"),
            _make_old_message(text="old"),
        )

    def test_media_present_is_always_a_change(self) -> None:
        # Токены не сравниваем (payload.token уникален на отправку) -> любое
        # медиа в новом сообщении считаем изменением, даже при том же тексте.
        manager = MessageManager(media_id_storage=AsyncMock())
        new = _make_new_message("old")
        new.media = [_media_with_token("tok")]
        old = _make_old_media_message()  # старое тоже с медиа

        assert manager._message_changed(new, old)

    def test_media_removed_is_a_change(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        new = _make_new_message("old")  # без медиа
        old = _make_old_media_message()  # раньше было медиа

        assert manager._message_changed(new, old)

    def test_can_edit_is_always_true(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())

        assert manager._can_edit(_make_new_message(), _make_old_message())


class TestShowMessage:
    async def test_edits_when_message_changed(self) -> None:
        manager = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        bot.edit_message = AsyncMock()
        bot.get_message_by_id = AsyncMock(return_value=_make_message("55", "new"))

        result = await manager.show_message(
            bot,
            _make_new_message("new"),
            _make_old_message("55", text="old"),
        )

        bot.edit_message.assert_awaited_once()
        assert result.text == "new"


class TestRemoveKbd:
    async def test_delete_and_send_removes_message(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()

        await manager.remove_kbd(bot, ShowMode.DELETE_AND_SEND, _make_old_message())

        bot.delete_message.assert_awaited_once()

    async def test_delete_and_send_without_old_message(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()

        await manager.remove_kbd(bot, ShowMode.DELETE_AND_SEND, None)

        bot.delete_message.assert_not_awaited()


class TestRemoveMessageSafe:
    async def test_ignores_missing_message(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        bot.delete_message = AsyncMock(
            side_effect=_bad_request("message to delete not found"),
        )

        await manager.remove_message_safe(bot, _make_old_message(), None)

    async def test_reraises_unknown_error(self) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        bot.delete_message = AsyncMock(side_effect=_bad_request("boom"))

        with pytest.raises(MaxBotBadRequestError):
            await manager.remove_message_safe(bot, _make_old_message(), None)


class TestEditMessageSafe:
    async def test_not_modified_maps_to_message_not_modified(self) -> None:
        manager = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        bot.edit_message = AsyncMock(
            side_effect=_bad_request("message is not modified"),
        )

        with pytest.raises(MessageNotModified):
            await manager.edit_message_safe(
                bot,
                _make_new_message(),
                _make_old_message(),
            )

    async def test_reraises_unknown_error(self) -> None:
        manager = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        bot.edit_message = AsyncMock(side_effect=_bad_request("boom"))

        with pytest.raises(MaxBotBadRequestError):
            await manager.edit_message_safe(
                bot,
                _make_new_message(),
                _make_old_message(),
            )

    async def test_edit_message_refetches_result(self) -> None:
        manager = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        expected = _make_message("55", "edited")
        bot.get_message_by_id = AsyncMock(return_value=expected)

        result = await manager.edit_message(
            bot,
            _make_new_message(),
            _make_old_message(),
        )

        assert result is expected


class TestTwoStepMediaEdit:
    """Двойной рендер медиа при редактировании на iOS. См. issue #156."""

    async def test_two_step_when_flag_and_edit_and_media_to_media(self) -> None:
        manager = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        bot.get_message_by_id = AsyncMock(return_value=_make_message("55", "new"))

        await manager.edit_message(
            bot,
            _make_new_media_message(),
            _make_old_media_message(),
        )

        assert bot.edit_message.await_count == 2
        assert manager.built_media[0] == []  # шаг 1 - без медиа
        assert len(manager.built_media[1]) == 1  # шаг 2 - медиа вернулось

    @pytest.mark.parametrize(
        ("new_message", "old_message"),
        [
            (
                _make_new_media_message(two_step_media_edit=False),
                _make_old_media_message(),
            ),
            (_make_new_media_message(), _make_old_message()),
            (_make_new_media_message(media=[]), _make_old_media_message()),
        ],
    )
    async def test_single_step_otherwise(
        self,
        new_message: NewMessage,
        old_message: OldMessage,
    ) -> None:
        manager = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        bot.get_message_by_id = AsyncMock(return_value=_make_message("55", "new"))

        await manager.edit_message(
            bot,
            new_message,
            old_message,
        )

        assert bot.edit_message.await_count == 1

    async def test_show_message_triggers_two_step_in_auto_mode(self) -> None:
        manager = StaticAttachmentsMessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        bot.get_message_by_id = AsyncMock(return_value=_make_message("55", "new"))
        new = _make_new_media_message(show_mode=ShowMode.AUTO)
        new.text = "old"

        await manager.show_message(
            bot,
            new,
            _make_old_media_message(),
        )

        assert bot.edit_message.await_count == 2

class TestSaveMediaIds:
    """Кэширование payload-токена из отправленного сообщения для path и url."""

    def _sent_with_photo(self, token: str, url: str) -> Message:
        return Message(
            body=MessageBody(
                mid="1",
                seq=1,
                text="new",
                attachments=[PhotoAttachment.factory(photo_id=1, token=token, url=url)],
            ),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
            timestamp=NOW,
        )

    async def test_caches_payload_token_by_url(self) -> None:
        storage = AsyncMock()
        manager = MessageManager(media_id_storage=storage)
        new = _make_new_media_message(
            media=[MediaAttachment(AttachmentType.IMAGE, url="http://e.com/a.png")],
        )

        await manager._save_media_ids(
            new,
            self._sent_with_photo("server-tok", "http://e.com/a.png"),
        )

        storage.save_media_id.assert_awaited_once_with(
            path=None,
            url="http://e.com/a.png",
            type=AttachmentType.IMAGE,
            media_id=MediaId(token="server-tok"),  # noqa: S106
        )

    async def test_skips_media_without_path_or_url(self) -> None:
        # media_id-only медиа нельзя ключевать по path/url -> не кэшируем
        storage = AsyncMock()
        manager = MessageManager(media_id_storage=storage)
        new = _make_new_media_message(media=[_media_with_token("explicit")])

        await manager._save_media_ids(
            new,
            self._sent_with_photo("server-tok", "http://e.com/a.png"),
        )

        storage.save_media_id.assert_not_awaited()

    async def test_send_message_caches_media_id(self) -> None:
        storage = AsyncMock()
        manager = StaticAttachmentsMessageManager(media_id_storage=storage)
        bot = AsyncMock()
        bot.send_message = AsyncMock(
            return_value=SendMessageResult(
                message=self._sent_with_photo("srv", "http://e.com/new.png"),
            ),
        )

        await manager.send_message(bot, _make_new_media_message())

        storage.save_media_id.assert_awaited_once()

    async def test_caches_by_request_order_for_mixed_album(self) -> None:
        storage = AsyncMock()
        manager = MessageManager(media_id_storage=storage)
        path_media = MediaAttachment(AttachmentType.IMAGE, path="pic.png")
        url_media = MediaAttachment(AttachmentType.IMAGE, url="http://e.com/u.png")
        new = _make_new_media_message(media=[path_media, url_media])
        sent = Message(
            body=MessageBody(
                mid="1",
                seq=1,
                text="new",
                attachments=[
                    PhotoAttachment.factory(2, "path-tok", "http://e.com/p.png"),
                    PhotoAttachment.factory(1, "url-tok", "http://e.com/u.png"),
                ],
            ),
            recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1, chat_id=1),
            timestamp=NOW,
        )

        await manager._save_media_ids(new, sent)

        cached = {
            call.kwargs["url"] or call.kwargs["path"]: call.kwargs["media_id"].token
            for call in storage.save_media_id.await_args_list
        }
        assert cached["http://e.com/u.png"] == "url-tok"
        assert cached["pic.png"] == "path-tok"


class TestBuildAttachments:
    async def test_preserves_media_order(self, tmp_path: Path) -> None:
        manager = MessageManager(media_id_storage=AsyncMock())
        bot = AsyncMock()
        media = [
            MediaAttachment(
                type=AttachmentType.IMAGE,
                media_id=MediaId(token="tok"),  # noqa: S106
            ),
            MediaAttachment(type=AttachmentType.IMAGE, path=tmp_path / "pic.png"),
            MediaAttachment(type=AttachmentType.IMAGE, url="http://e.com/a.png"),
        ]

        with patch(
            "maxo.dialogs.manager.message_manager.AttachmentsFacade",
        ) as facade_cls:
            facade_cls.return_value.build_attachments = AsyncMock(return_value=[])
            await manager._build_attachments(bot, keyboard=None, media=media)

        kwargs = facade_cls.return_value.build_attachments.await_args.kwargs
        assert kwargs["base"] == []
        assert isinstance(kwargs["files"][0], PhotoAttachmentRequest)
        assert isinstance(kwargs["files"][1], FSInputFile)
        assert isinstance(kwargs["files"][2], PhotoAttachmentRequest)

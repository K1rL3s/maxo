from datetime import UTC, datetime
from typing import cast

import pytest

from maxo import Bot
from maxo.enums import (
    AttachmentType,
    ChatAdminPermission,
    ChatStatus,
    ChatType,
    MarkupElementType,
    MessageLinkType,
    TextFormat,
)
from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.types import (
    AudioAttachment,
    BotCommand,
    BotInfo,
    BotStopped,
    Callback,
    CallbackButton,
    Chat,
    ChatAdmin,
    ChatAdminsList,
    ChatList,
    ChatMember,
    CommentLinkedMessage,
    CommentMessage,
    CommentMessageBody,
    CommentRemoved,
    ContactAttachment,
    ContactAttachmentPayload,
    ContactAttachmentRequest,
    ContactAttachmentRequestPayload,
    DialogCleared,
    DialogMuted,
    DialogRemoved,
    DialogUnmuted,
    FailedUserDetails,
    FileAttachment,
    GetPinnedMessageResult,
    Image,
    InlineKeyboardAttachment,
    Keyboard,
    LinkedMessage,
    LocationAttachment,
    MarkupElement,
    MediaAttachmentPayload,
    Message,
    MessageBody,
    MessageButton,
    MessageCallback,
    MessageEdited,
    MessageRemoved,
    MessageStat,
    ModifyMembersResult,
    NewCommentBody,
    NewMessageBody,
    NewMessageLink,
    OpenAppButton,
    PhotoAttachment,
    PhotoAttachmentPayload,
    PhotoAttachmentRequest,
    PhotoAttachmentRequestPayload,
    PhotoToken,
    Recipient,
    RequestGeoLocationButton,
    ShareAttachment,
    ShareAttachmentPayload,
    SimpleQueryResult,
    StickerAttachment,
    Subscription,
    UpdateContext,
    UpdateList,
    UploadEndpoint,
    UploadMediaResult,
    UploadedInfo,
    User,
    UserAddedToChat,
    UserMentionMarkup,
    UserRemovedFromChat,
    UserWithPhoto,
    VideoAttachment,
    VideoAttachmentDetails,
    VideoThumbnail,
    VideoUrls,
)
from tests.constants import NOW

from .conftest import make_callback, make_message, make_user

TOKEN = "attachment-token"  # noqa: S105
PHOTO_ID = "photo-token"
PHOTO_ATTACHMENT_ID = "photo-attachment"
SHARE_ID = "share-token"
UPLOAD_ID = "upload-token"
UPLOADED_ID = "uploaded-token"
VIDEO_ID = "video-token"
DETAILS_ID = "details-token"


def make_chat(**kwargs: object) -> Chat:
    data = {
        "chat_id": 10,
        "is_public": True,
        "last_event_time": NOW,
        "participants_count": 2,
        "status": ChatStatus.ACTIVE,
        "type": ChatType.CHAT,
    }
    data.update(kwargs)
    return Chat(**data)  # type: ignore[arg-type]


def test_user_accessors() -> None:
    user = make_user()

    assert user.id == 1
    assert user.fullname == "Alice Tester"
    assert user.full_name == "Alice Tester"
    assert user.unsafe_last_activity_time == NOW
    assert user.unsafe_last_name == "Tester"
    assert user.unsafe_name == "Alice T."
    assert user.unsafe_username == "alice"


def test_user_unsafe_accessors_raise_for_omitted_fields() -> None:
    user = User(
        user_id=1,
        first_name="Alice",
        is_bot=False,
    )

    assert not is_defined(user.last_activity_time)
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_last_activity_time
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_last_name
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_name
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_username


def test_bot_info_commands_accessor() -> None:
    commands = [BotCommand(name="start", description="Start")]
    info = BotInfo(
        user_id=1,
        first_name="Bot",
        username="bot",
        is_bot=True,
        last_activity_time=NOW,
        commands=commands,
    )

    assert info.unsafe_commands is commands


def test_bot_info_commands_accessor_raises_for_omitted_value() -> None:
    info = BotInfo(
        user_id=1,
        first_name="Bot",
        username="bot",
        is_bot=True,
        last_activity_time=NOW,
    )

    with pytest.raises(AttributeIsEmptyError):
        _ = info.unsafe_commands


def test_chat_accessors_for_defined_values() -> None:
    icon = Image(url="https://example.com/icon.png")
    user = make_user()
    message = make_message()
    participants = {"1": {"last_activity_time": 1}}
    chat = make_chat(
        chat_message_id="button-message",
        description="chat",
        dialog_with_user=user,
        icon=icon,
        link="https://max.ru/join",
        messages_count=3,
        owner_id=1,
        participants=participants,
        pinned_message=message,
        title="Chat",
    )

    assert chat.id == 10
    assert chat.unsafe_chat_message_id == "button-message"
    assert chat.unsafe_description == "chat"
    assert chat.unsafe_dialog_with_user is user
    assert chat.unsafe_icon is icon
    assert chat.unsafe_link == "https://max.ru/join"
    assert chat.unsafe_messages_count == 3
    assert chat.unsafe_owner_id == 1
    assert chat.unsafe_participants is participants
    assert chat.unsafe_pinned_message is message
    assert chat.unsafe_title == "Chat"


def test_chat_accessors_raise_for_explicit_none_values() -> None:
    chat = make_chat(description=None, icon=None, title=None)

    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_description
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_icon
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_title


def test_chat_accessors_raise_for_omitted_values() -> None:
    chat = make_chat()

    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_chat_message_id
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_dialog_with_user
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_link
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_messages_count
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_owner_id
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_participants
    with pytest.raises(AttributeIsEmptyError):
        _ = chat.unsafe_pinned_message


def test_message_accessors_and_generated_url() -> None:
    stat = MessageStat(views=5)
    sender = make_user()
    message = make_message(sender=sender, stat=stat, url="https://max.ru/post")

    assert message.message is message
    assert message.unsafe_sender is sender
    assert message.unsafe_stat is stat
    assert message.unsafe_url == "https://max.ru/post"
    assert message.generated_url is not None
    assert message.unsafe_generated_url == message.generated_url


def test_message_generated_url_is_none_without_chat_id() -> None:
    message = make_message(
        recipient=Recipient(chat_type=ChatType.DIALOG, user_id=1),
    )

    assert message.generated_url is None
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_generated_url


def test_recipient_accessors() -> None:
    recipient = Recipient(chat_type=ChatType.CHAT, chat_id=10, user_id=1)

    assert recipient.unsafe_chat_id == 10
    assert recipient.unsafe_user_id == 1


def test_recipient_accessors_raise_for_missing_values() -> None:
    recipient = Recipient(chat_type=ChatType.CHAT)

    with pytest.raises(AttributeIsEmptyError):
        _ = recipient.unsafe_chat_id
    with pytest.raises(AttributeIsEmptyError):
        _ = recipient.unsafe_user_id


def test_message_body_attachment_accessors() -> None:
    keyboard = Keyboard(buttons=[])
    photo = PhotoAttachment.factory(photo_id=1, token=TOKEN, url="photo-url")
    video = VideoAttachment.factory(url="video-url", token=TOKEN)
    audio = AudioAttachment.factory(url="audio-url", token=TOKEN)
    file = FileAttachment.factory(
        url="file-url",
        token=TOKEN,
        filename="file.txt",
        size=10,
    )
    sticker = StickerAttachment.factory(
        url="sticker-url",
        code="sticker-code",
        width=10,
        height=10,
    )
    contact = ContactAttachment.factory(max_info=make_user())
    share = ShareAttachment.factory(url="https://example.com")
    location = LocationAttachment(latitude=1.0, longitude=2.0)
    body = MessageBody(
        mid="mid",
        seq=1,
        text="text",
        attachments=[
            InlineKeyboardAttachment(payload=keyboard),
            photo,
            video,
            audio,
            file,
            sticker,
            contact,
            share,
            location,
        ],
        markup=[],
    )

    assert body.id == "mid"
    assert body.keyboard is keyboard
    assert body.reply_markup is keyboard
    assert body.photo == [photo]
    assert body.video == [video]
    assert body.audio is audio
    assert body.file is file
    assert body.sticker is sticker
    assert body.contact is contact
    assert body.share is share
    assert body.location is location
    assert body.unsafe_attachments == body.attachments
    assert body.unsafe_markup == []
    assert body.unsafe_text == "text"
    assert body.html_text == "text"
    assert body.md_text == "text"


@pytest.mark.parametrize(
    ("body", "attachment_type"),
    [
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[
                    PhotoAttachment.factory(
                        photo_id=1,
                        token=TOKEN,
                        url="photo-url",
                    ),
                ],
            ),
            AttachmentType.PHOTO,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[VideoAttachment.factory(url="url", token=TOKEN)],
            ),
            AttachmentType.VIDEO,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[AudioAttachment.factory(url="url", token=TOKEN)],
            ),
            AttachmentType.AUDIO,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[
                    FileAttachment.factory(
                        url="url",
                        token=TOKEN,
                        filename="file",
                        size=1,
                    ),
                ],
            ),
            AttachmentType.FILE,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[
                    StickerAttachment.factory(
                        url="url",
                        code="code",
                        width=1,
                        height=1,
                    ),
                ],
            ),
            AttachmentType.STICKER,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[ContactAttachment.factory(max_info=make_user())],
            ),
            AttachmentType.CONTACT,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[ShareAttachment.factory(url="https://example.com")],
            ),
            AttachmentType.SHARE,
        ),
        (
            MessageBody(
                mid="mid",
                seq=1,
                attachments=[LocationAttachment(latitude=1.0, longitude=2.0)],
            ),
            AttachmentType.LOCATION,
        ),
        (MessageBody(mid="mid", seq=1, text="text"), AttachmentType.TEXT),
        (MessageBody(mid="mid", seq=1), AttachmentType.UNKNOWN),
    ],
)
def test_message_body_attachment_type(
    body: MessageBody,
    attachment_type: AttachmentType,
) -> None:
    assert body.attachment_type is attachment_type
    assert body.content_type is attachment_type


def test_message_body_unsafe_accessors_raise_for_omitted_values() -> None:
    body = MessageBody(mid="mid", seq=1)

    with pytest.raises(AttributeIsEmptyError):
        _ = body.unsafe_markup
    with pytest.raises(AttributeIsEmptyError):
        _ = body.unsafe_text


def test_message_body_unsafe_attachments_raises_for_explicit_none() -> None:
    body = MessageBody(mid="mid", seq=1, attachments=None)

    with pytest.raises(AttributeIsEmptyError):
        _ = body.unsafe_attachments


def test_callback_accessors() -> None:
    callback = Callback(
        callback_id="callback",
        timestamp=NOW,
        user=make_user(),
        payload="payload",
    )

    assert callback.id == "callback"
    assert callback.data == "payload"
    assert callback.unsafe_payload == "payload"
    assert callback.unsafe_data == "payload"

    with pytest.raises(AttributeIsEmptyError):
        _ = Callback(
            callback_id="callback",
            timestamp=NOW,
            user=make_user(),
        ).unsafe_payload


def test_linked_message_accessors_and_generated_url() -> None:
    sender = make_user()
    linked = LinkedMessage(
        type=MessageLinkType.FORWARD,
        message=MessageBody(mid="mid", seq=5, text="forwarded"),
        chat_id=10,
        sender=sender,
    )

    assert linked.unsafe_chat_id == 10
    assert linked.unsafe_sender is sender
    assert linked.generated_url is not None
    assert linked.unsafe_generated_url == linked.generated_url

    omitted = LinkedMessage(
        type=MessageLinkType.REPLY,
        message=MessageBody(mid="mid", seq=5, text="reply"),
    )
    assert omitted.generated_url is None
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_chat_id
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_sender
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_generated_url


def test_new_message_body_accessors() -> None:
    link = NewMessageLink(mid="mid", type=MessageLinkType.REPLY)
    body = NewMessageBody(
        attachments=[],
        format=TextFormat.MARKDOWN,
        link=link,
        notify=False,
        text="text",
    )

    assert body.unsafe_attachments == []
    assert body.unsafe_format is TextFormat.MARKDOWN
    assert body.unsafe_link is link
    assert body.unsafe_notify is False
    assert body.unsafe_text == "text"

    omitted = NewMessageBody()
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_format
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_notify


def test_media_attachment_to_request_factories() -> None:
    assert AudioAttachment.factory(url="url", token=TOKEN).to_request().payload.token
    assert (
        FileAttachment.factory(
            url="url",
            token=TOKEN,
            filename="file",
            size=1,
        )
        .to_request()
        .payload.token
        == TOKEN
    )
    assert (
        PhotoAttachment.factory(
            photo_id=1,
            token=TOKEN,
            url="url",
        )
        .to_request()
        .payload.token
        == TOKEN
    )
    assert (
        StickerAttachment.factory(
            url="url",
            code="code",
            width=1,
            height=1,
        )
        .to_request()
        .payload.code
        == "code"
    )
    assert (
        VideoAttachment.factory(
            url="url",
            token=TOKEN,
            thumbnail_url="thumbnail",
            width=1,
            height=2,
            duration=3,
        )
        .to_request()
        .payload.token
        == TOKEN
    )
    assert InlineKeyboardAttachment.factory([]).to_request().payload.buttons == []
    assert LocationAttachment(latitude=1.0, longitude=2.0).to_request().latitude == 1.0


def test_media_attachment_unsafe_optional_values() -> None:
    audio = AudioAttachment.factory(url="url", token=TOKEN, transcription="text")
    video = VideoAttachment.factory(
        url="url",
        token=TOKEN,
        thumbnail_url="thumbnail",
        width=1,
        height=2,
        duration=3,
    )
    share = ShareAttachment.factory(
        url="url",
        token=TOKEN,
        title="title",
        description="description",
        image_url="image",
    )

    assert audio.unsafe_transcription == "text"
    assert video.unsafe_width == 1
    assert video.unsafe_height == 2
    assert video.unsafe_duration == 3
    assert isinstance(video.unsafe_thumbnail, VideoThumbnail)
    assert share.unsafe_title == "title"
    assert share.unsafe_description == "description"
    assert share.unsafe_image_url == "image"
    assert share.to_request().payload.token == TOKEN

    with pytest.raises(AttributeIsEmptyError):
        _ = AudioAttachment.factory(url="url", token=TOKEN).unsafe_transcription
    with pytest.raises(AttributeIsEmptyError):
        _ = VideoAttachment.factory(url="url", token=TOKEN).unsafe_width
    with pytest.raises(AttributeIsEmptyError):
        _ = ShareAttachment().unsafe_title


def test_contact_attachment_request_payload_accessors() -> None:
    payload = ContactAttachmentRequestPayload(
        contact_id=1,
        name="Alice",
        vcf_info="BEGIN:VCARD",
        vcf_phone="+1",
    )

    assert payload.unsafe_contact_id == 1
    assert payload.unsafe_name == "Alice"
    assert payload.unsafe_vcf_info == "BEGIN:VCARD"
    assert payload.unsafe_vcf_phone == "+1"

    omitted = ContactAttachmentRequestPayload()
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_contact_id
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_vcf_info


def test_contact_attachment_payload_accessors() -> None:
    user = make_user()
    payload = ContactAttachmentPayload(
        hash="hash",
        max_info=user,
        vcf_info="BEGIN:VCARD",
    )

    assert payload.unsafe_hash == "hash"
    assert payload.unsafe_max_info is user
    assert payload.unsafe_vcf_info == "BEGIN:VCARD"

    omitted = ContactAttachmentPayload()
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_hash
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_max_info


def test_photo_request_payload_and_share_payload_accessors() -> None:
    photo_token = PhotoToken(token=TOKEN)
    photo_payload = PhotoAttachmentRequestPayload(
        photos=[photo_token],
        token=TOKEN,
        url="url",
    )
    share_payload = ShareAttachmentPayload(token=TOKEN, url="url")

    assert photo_payload.unsafe_photos == [photo_token]
    assert photo_payload.unsafe_token == TOKEN
    assert photo_payload.unsafe_url == "url"
    assert share_payload.unsafe_token == TOKEN
    assert share_payload.unsafe_url == "url"

    with pytest.raises(AttributeIsEmptyError):
        _ = PhotoAttachmentRequestPayload().unsafe_token
    with pytest.raises(AttributeIsEmptyError):
        _ = ShareAttachmentPayload().unsafe_url


def test_video_urls_and_details_accessors() -> None:
    urls = VideoUrls(
        hls="hls",
        mp4_1080="1080",
        mp4_144="144",
        mp4_240="240",
        mp4_360="360",
        mp4_480="480",
        mp4_720="720",
    )
    details = VideoAttachmentDetails(
        duration=1,
        height=2,
        token=TOKEN,
        width=3,
        thumbnail=PhotoAttachment.factory(
            photo_id=1,
            token=TOKEN,
            url="thumbnail",
        ).payload,
        urls=urls,
    )

    assert urls.unsafe_hls == "hls"
    assert urls.unsafe_mp4_1080 == "1080"
    assert urls.unsafe_mp4_144 == "144"
    assert urls.unsafe_mp4_240 == "240"
    assert urls.unsafe_mp4_360 == "360"
    assert urls.unsafe_mp4_480 == "480"
    assert urls.unsafe_mp4_720 == "720"
    assert details.unsafe_thumbnail.url == "thumbnail"
    assert details.unsafe_urls is urls

    with pytest.raises(AttributeIsEmptyError):
        _ = VideoUrls().unsafe_hls
    with pytest.raises(AttributeIsEmptyError):
        _ = VideoAttachmentDetails(
            duration=1,
            height=2,
            token=TOKEN,
            width=3,
        ).unsafe_urls


def test_small_generated_accessors() -> None:
    permissions = [ChatAdminPermission.READ_ALL_MESSAGES]
    failed_users = [1, 2]

    assert BotCommand(name="start", description="desc").unsafe_description == "desc"
    assert CallbackButton(text="callback", payload="payload").callback_data == "payload"
    assert ChatAdmin(user_id=1, permissions=permissions, alias="admin").unsafe_alias
    assert (
        ChatMember(
            user_id=1,
            first_name="Alice",
            is_bot=False,
            last_activity_time=NOW,
            join_time=NOW,
            last_access_time=NOW,
            is_admin=True,
            is_owner=False,
            alias="admin",
            permissions=permissions,
        ).unsafe_permissions
        == permissions
    )
    assert (
        GetPinnedMessageResult(message=make_message()).unsafe_message.message
        is not None
    )
    assert MessageButton(text="text").unsafe_text == "text"
    assert (
        ModifyMembersResult(
            success=True,
            failed_user_ids=failed_users,
        ).unsafe_failed_user_ids
        == failed_users
    )
    assert OpenAppButton(
        text="open",
        contact_id=1,
        payload="payload",
        web_app="app",
    ).unsafe_payload
    assert RequestGeoLocationButton(text="geo", quick=True).unsafe_quick is True
    assert SimpleQueryResult(success=True, message="ok").unsafe_message == "ok"
    assert Subscription(
        time=NOW,
        url="https://example.com/webhook",
        update_types=["message_created"],
    ).unsafe_update_types == ["message_created"]
    assert UploadEndpoint(url="url", token=TOKEN).unsafe_token == TOKEN
    assert UploadedInfo(token=TOKEN).unsafe_token == TOKEN
    assert (
        UserMentionMarkup(
            from_=0,
            length=4,
            user_id=1,
            user_link="https://max.ru/u",
        ).unsafe_user_id
        == 1
    )
    assert (
        UserWithPhoto(
            user_id=1,
            first_name="Alice",
            is_bot=False,
            last_activity_time=NOW,
            avatar_url="avatar",
            description="description",
            full_avatar_url="full",
        ).unsafe_full_avatar_url
        == "full"
    )


def test_upload_media_result_last_token() -> None:
    photo_token = "photo-upload-token"  # noqa: S105

    assert UploadMediaResult(token=TOKEN).last_token == TOKEN
    assert (
        UploadMediaResult(photos={"1": PhotoToken(token=photo_token)}).last_token
        == photo_token
    )

    with pytest.raises(RuntimeError):
        _ = UploadMediaResult().last_token


def test_base_message_button_accessors() -> None:
    message_button = MessageButton(text="Hello")

    assert message_button.unsafe_text == "Hello"


def test_button_accessors_raise_for_omitted_values() -> None:
    message_button = MessageButton()
    open_app_button = OpenAppButton(text="Open")

    with pytest.raises(AttributeIsEmptyError):
        _ = message_button.unsafe_text
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app_button.unsafe_contact_id
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app_button.unsafe_payload
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app_button.unsafe_web_app


def test_video_urls_and_user_with_photo_accessors() -> None:
    urls = VideoUrls(
        hls="https://example.com/hls.m3u8",
        mp4_1080="https://example.com/1080.mp4",
    )
    user = UserWithPhoto(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=NOW,
        avatar_url="https://example.com/avatar.png",
        description="About Alice",
        full_avatar_url="https://example.com/full.png",
    )

    assert urls.unsafe_hls == "https://example.com/hls.m3u8"
    assert urls.unsafe_mp4_1080 == "https://example.com/1080.mp4"
    assert user.unsafe_avatar_url == "https://example.com/avatar.png"
    assert user.unsafe_description == "About Alice"
    assert user.unsafe_full_avatar_url == "https://example.com/full.png"


def test_update_list_and_simple_query_result_accessors() -> None:
    update_list = UpdateList(updates=[], marker=10)
    query_result = SimpleQueryResult(success=True, message="ok")

    assert update_list.unsafe_marker == 10
    assert query_result.unsafe_message == "ok"


def test_update_list_and_simple_query_result_raise_for_missing_values() -> None:
    update_list = UpdateList(updates=[])
    query_result = SimpleQueryResult(success=False)

    with pytest.raises(AttributeIsEmptyError):
        _ = update_list.unsafe_marker
    with pytest.raises(AttributeIsEmptyError):
        _ = query_result.unsafe_message


def test_message_generated_url_requires_chat_id() -> None:
    message = Message(
        body=MessageBody(mid="1", seq=1, text="hello"),
        recipient=Recipient(chat_type=ChatType.DIALOG),
        timestamp=NOW,
    )

    assert message.generated_url is None


def test_maxo_type_bot_accessors() -> None:
    user = make_user()

    with pytest.raises(AttributeIsEmptyError):
        _ = user.bot

    user.bot = None
    assert user._bot is None

    class DummyBot: ...

    # cast нужен для проверки BaseMethodsFacade без создания реального Bot с сетевым клиентом.
    bot = cast(Bot, DummyBot())
    assert user.as_(bot) is user
    assert user.bot is bot


def test_user_and_chat_related_accessors() -> None:
    chat = Chat(
        chat_id=1,
        is_public=False,
        last_event_time=NOW,
        participants_count=1,
        status=ChatStatus.ACTIVE,
        type=ChatType.CHAT,
        title="Room",
    )
    chat_admin = ChatAdmin(
        user_id=1,
        permissions=[ChatAdminPermission.READ_ALL_MESSAGES],
        alias="Admin",
    )
    member = ChatMember(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=NOW,
        is_admin=True,
        is_owner=False,
        join_time=NOW,
        last_access_time=NOW,
        permissions=[ChatAdminPermission.READ_ALL_MESSAGES],
        alias="Admin",
        avatar_url="https://example.com/avatar.png",
        full_avatar_url="https://example.com/full.png",
    )

    assert chat_admin.unsafe_alias == "Admin"
    assert chat_admin.permissions == [ChatAdminPermission.READ_ALL_MESSAGES]
    assert member.unsafe_alias == "Admin"
    assert member.unsafe_permissions == [ChatAdminPermission.READ_ALL_MESSAGES]
    assert chat.id == 1
    assert make_user().full_name == "Alice Tester"


def test_list_and_result_accessors() -> None:
    admin = ChatAdmin(
        user_id=1,
        permissions=[ChatAdminPermission.READ_ALL_MESSAGES],
    )
    chat = Chat(
        chat_id=1,
        is_public=False,
        last_event_time=NOW,
        participants_count=1,
        status=ChatStatus.ACTIVE,
        type=ChatType.CHAT,
        title="Room",
    )
    admins = ChatAdminsList(admins=[admin], marker=2)
    chats = ChatList(chats=[chat], marker=3)
    pinned_result = GetPinnedMessageResult(message=None)

    assert admins.unsafe_marker == 2
    assert chats.unsafe_marker == 3
    with pytest.raises(AttributeIsEmptyError):
        _ = pinned_result.unsafe_message


def test_markup_and_context_accessors() -> None:
    element = MarkupElement(from_=1, length=2, type=MarkupElementType.STRONG)
    mention = UserMentionMarkup(
        from_=0,
        length=5,
        type=MarkupElementType.USER_MENTION,
        user_id=10,
        user_link="@alice",
    )
    context = UpdateContext(chat_id=1, user_id=2, type=ChatType.DIALOG)

    assert element.offset == 1
    assert mention.unsafe_user_id == 10
    assert mention.unsafe_user_link == "@alice"
    assert context.chat_type == ChatType.DIALOG


def test_attachment_factories_and_unsafe_fields() -> None:
    max_info = make_user()
    contact = ContactAttachment.factory(
        max_info=max_info,
        vcf_info="BEGIN:VCARD",
    )
    photo_request = PhotoAttachmentRequest.factory(photos=["a", "b"])
    photo_payload = PhotoAttachmentRequestPayload(
        photos=[PhotoToken(token=PHOTO_ATTACHMENT_ID)],
        token=PHOTO_ID,
        url="https://example.com",
    )
    share = ShareAttachment.factory(
        url="https://example.com",
        token=SHARE_ID,
        title="Title",
        description="Desc",
        image_url="https://example.com/image.png",
    )
    subscription = Subscription(
        time=NOW,
        url="https://example.com",
        update_types=["message_created"],
    )
    upload = UploadEndpoint(url="https://upload.example.com", token=UPLOAD_ID)
    uploaded = UploadedInfo(token=UPLOADED_ID)
    geo = RequestGeoLocationButton(text="geo", quick=True)

    assert contact.payload.unsafe_max_info is max_info
    assert contact.payload.unsafe_vcf_info == "BEGIN:VCARD"
    assert photo_request.payload.unsafe_photos[0].token == chr(97)
    assert photo_payload.unsafe_token == PHOTO_ID
    assert share.unsafe_title == "Title"
    assert share.unsafe_description == "Desc"
    assert share.unsafe_image_url == "https://example.com/image.png"
    assert share.to_request().payload.unsafe_url == "https://example.com"
    assert subscription.unsafe_update_types == ["message_created"]
    assert upload.unsafe_token == UPLOAD_ID
    assert uploaded.unsafe_token == UPLOADED_ID
    assert geo.unsafe_quick is True
    assert contact.to_request().payload.unsafe_contact_id == 1


def test_media_and_message_models() -> None:
    message = NewMessageBody(
        attachments=[],
        format=TextFormat.HTML,
        link=None,
        notify=True,
        text="hello",
    )
    video = VideoAttachment.factory(
        url="https://example.com/video.mp4",
        token=VIDEO_ID,
        thumbnail_url="https://example.com/thumb.png",
        width=1920,
        height=1080,
        duration=33,
    )
    details = VideoAttachmentDetails(
        duration=33,
        height=1080,
        token=DETAILS_ID,
        width=1920,
        thumbnail=PhotoAttachmentPayload(
            photo_id=1,
            token=PHOTO_ATTACHMENT_ID,
            url="https://example.com/video.png",
        ),
        urls=VideoUrls(mp4_720="https://example.com/720.mp4"),
    )
    video_urls = VideoUrls(mp4_720="https://example.com/720.mp4")

    assert message.unsafe_text == "hello"
    assert message.unsafe_notify is True
    assert video.unsafe_duration == 33
    assert video.unsafe_thumbnail.url == "https://example.com/thumb.png"
    assert video.to_request().payload.token == VIDEO_ID
    assert details.unsafe_urls.unsafe_mp4_720 == "https://example.com/720.mp4"
    assert video_urls.unsafe_mp4_720 == "https://example.com/720.mp4"


def test_remaining_optional_branches() -> None:
    message = Message(
        body=MessageBody(mid="1", seq=1, text="hello"),
        recipient=Recipient(chat_type=ChatType.DIALOG),
        timestamp=NOW,
        sender=make_user(),
        stat=MessageStat(views=1),
        url="https://example.com",
    )
    open_app = OpenAppButton(text="open")
    new_message = NewMessageBody(
        attachments=[],
        format=TextFormat.HTML,
        link=None,
        notify=True,
        text="hello",
    )
    share = ShareAttachment(
        title="Title",
        description="Desc",
        image_url="https://example.com/image.png",
    )
    modify = ModifyMembersResult(
        success=False,
        message="failed",
        failed_user_details=[FailedUserDetails(user_ids=[1], error_code="bad")],
        failed_user_ids=[1],
    )
    photo_payload = PhotoAttachmentRequestPayload(
        photos=[PhotoToken(token=PHOTO_ID)],
        token=TOKEN,
        url="https://example.com",
    )
    contact_request = ContactAttachmentRequest.factory(vcf_info="BEGIN:VCARD")
    subscription = Subscription(time=NOW, url="https://example.com")

    assert message.unsafe_sender.user_id == 1
    assert message.unsafe_stat.views == 1
    assert message.unsafe_url == "https://example.com"
    with pytest.raises(
        AttributeIsEmptyError,
        match=r"OpenAppButton.contact_id is empty \(<Omitted>\)",
    ):
        _ = open_app.unsafe_contact_id
    assert new_message.unsafe_attachments == []
    assert new_message.unsafe_format == TextFormat.HTML
    with pytest.raises(
        AttributeIsEmptyError,
        match=r"NewMessageBody.link is empty \(None\)",
    ):
        _ = new_message.unsafe_link
    assert new_message.unsafe_notify is True
    assert share.unsafe_description == "Desc"
    assert share.unsafe_image_url == "https://example.com/image.png"
    assert share.unsafe_title == "Title"
    assert modify.unsafe_failed_user_details[0].user_ids == [1]
    assert modify.unsafe_failed_user_ids == [1]
    assert photo_payload.unsafe_photos[0].token == PHOTO_ID
    assert photo_payload.unsafe_token == TOKEN
    assert photo_payload.unsafe_url == "https://example.com"
    assert contact_request.payload.unsafe_vcf_info == "BEGIN:VCARD"
    with pytest.raises(
        AttributeIsEmptyError,
        match=r"Subscription.update_types is empty \(None\)",
    ):
        _ = subscription.unsafe_update_types


def test_additional_type_edges() -> None:
    bot_command = BotCommand(name="start")
    member = UserWithPhoto(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=NOW,
        username=None,
        avatar_url="https://example.com/avatar.png",
        description="About Alice",
        full_avatar_url="https://example.com/full.png",
    )

    with pytest.raises(AttributeIsEmptyError):
        _ = bot_command.unsafe_description
    assert member.unsafe_description == "About Alice"


def test_missing_optional_fields_raise_for_unsafe_accessors() -> None:
    user = User(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=datetime.fromtimestamp(1234567890, tz=UTC),
    )
    chat_admin = ChatAdmin(user_id=1, permissions=[])
    member = UserWithPhoto(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=NOW,
    )
    chat_member = ChatMember(
        user_id=1,
        first_name="Alice",
        is_bot=False,
        last_activity_time=NOW,
        is_admin=False,
        is_owner=False,
        join_time=NOW,
        last_access_time=NOW,
    )
    chat_admins = ChatAdminsList(admins=[chat_admin])
    chats = ChatList(chats=[])
    pinned_result = GetPinnedMessageResult()
    geo = RequestGeoLocationButton(text="geo")
    upload = UploadEndpoint(url="https://upload.example.com")
    uploaded = UploadedInfo()
    mention = UserMentionMarkup(
        from_=0,
        length=5,
        type=MarkupElementType.USER_MENTION,
    )
    video = VideoAttachment(
        payload=MediaAttachmentPayload(
            url="https://example.com/video.mp4",
            token=VIDEO_ID,
        ),
    )
    details = VideoAttachmentDetails(
        duration=33,
        height=1080,
        token=DETAILS_ID,
        width=1920,
    )
    open_app = OpenAppButton(text="open")
    share_payload = ShareAttachmentPayload()
    video_urls = VideoUrls()
    message = Message(
        body=MessageBody(mid="1", seq=1, text="hello"),
        recipient=Recipient(chat_type=ChatType.DIALOG),
        timestamp=NOW,
    )

    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_last_name
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_name
    with pytest.raises(AttributeIsEmptyError):
        _ = user.unsafe_username
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_admin.unsafe_alias
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_admins.unsafe_marker
    with pytest.raises(AttributeIsEmptyError):
        _ = chats.unsafe_marker
    with pytest.raises(AttributeIsEmptyError):
        _ = member.unsafe_avatar_url
    with pytest.raises(AttributeIsEmptyError):
        _ = member.unsafe_description
    with pytest.raises(AttributeIsEmptyError):
        _ = member.unsafe_full_avatar_url
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_member.unsafe_alias
    with pytest.raises(AttributeIsEmptyError):
        _ = chat_member.unsafe_permissions
    with pytest.raises(AttributeIsEmptyError):
        _ = pinned_result.unsafe_message
    with pytest.raises(AttributeIsEmptyError):
        _ = geo.unsafe_quick
    with pytest.raises(AttributeIsEmptyError):
        _ = upload.unsafe_token
    with pytest.raises(AttributeIsEmptyError):
        _ = uploaded.unsafe_token
    with pytest.raises(AttributeIsEmptyError):
        _ = mention.unsafe_user_id
    with pytest.raises(AttributeIsEmptyError):
        _ = mention.unsafe_user_link
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_link
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_sender
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_stat
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_url
    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_duration
    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_height
    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_thumbnail
    with pytest.raises(AttributeIsEmptyError):
        _ = video.unsafe_width
    with pytest.raises(AttributeIsEmptyError):
        _ = details.unsafe_thumbnail
    with pytest.raises(AttributeIsEmptyError):
        _ = details.unsafe_urls
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app.unsafe_contact_id
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app.unsafe_payload
    with pytest.raises(AttributeIsEmptyError):
        _ = open_app.unsafe_web_app
    with pytest.raises(AttributeIsEmptyError):
        _ = share_payload.unsafe_token
    with pytest.raises(AttributeIsEmptyError):
        _ = share_payload.unsafe_url
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_hls
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_1080
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_144
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_240
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_360
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_480
    with pytest.raises(AttributeIsEmptyError):
        _ = video_urls.unsafe_mp4_720
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_link
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_sender
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_stat
    with pytest.raises(AttributeIsEmptyError):
        _ = message.unsafe_url


def test_bot_stopped_unsafe_user_locale() -> None:
    defined = BotStopped(
        chat_id=1,
        user=make_user(),
        user_locale="ru-RU",
        timestamp=NOW,
    )
    assert defined.unsafe_user_locale == "ru-RU"

    omitted = BotStopped(chat_id=1, user=make_user(), timestamp=NOW)
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_user_locale


def test_dialog_cleared_unsafe_user_locale() -> None:
    defined = DialogCleared(
        chat_id=1,
        user=make_user(),
        user_locale="ru-RU",
        timestamp=NOW,
    )
    assert defined.unsafe_user_locale == "ru-RU"

    omitted = DialogCleared(chat_id=1, user=make_user(), timestamp=NOW)
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_user_locale


def test_dialog_muted_unsafe_user_locale() -> None:
    defined = DialogMuted(
        chat_id=1,
        muted_until=NOW,
        user=make_user(),
        user_locale="ru-RU",
        timestamp=NOW,
    )
    assert defined.unsafe_user_locale == "ru-RU"

    omitted = DialogMuted(
        chat_id=1,
        muted_until=NOW,
        user=make_user(),
        timestamp=NOW,
    )
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_user_locale


def test_dialog_removed_unsafe_user_locale() -> None:
    defined = DialogRemoved(
        chat_id=1,
        user=make_user(),
        user_locale="ru-RU",
        timestamp=NOW,
    )
    assert defined.unsafe_user_locale == "ru-RU"

    omitted = DialogRemoved(chat_id=1, user=make_user(), timestamp=NOW)
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_user_locale


def test_dialog_unmuted_unsafe_user_locale() -> None:
    defined = DialogUnmuted(
        chat_id=1,
        user=make_user(),
        user_locale="ru-RU",
        timestamp=NOW,
    )
    assert defined.unsafe_user_locale == "ru-RU"

    omitted = DialogUnmuted(chat_id=1, user=make_user(), timestamp=NOW)
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_user_locale


def test_user_added_to_chat_unsafe_inviter_id() -> None:
    defined = UserAddedToChat(
        chat_id=1,
        is_channel=False,
        user=make_user(),
        inviter_id=2,
        timestamp=NOW,
    )
    assert defined.unsafe_inviter_id == 2

    omitted = UserAddedToChat(
        chat_id=1,
        is_channel=False,
        user=make_user(),
        timestamp=NOW,
    )
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_inviter_id


def test_user_removed_from_chat_unsafe_admin_id() -> None:
    defined = UserRemovedFromChat(
        chat_id=1,
        is_channel=False,
        user=make_user(),
        admin_id=2,
        timestamp=NOW,
    )
    assert defined.unsafe_admin_id == 2

    omitted = UserRemovedFromChat(
        chat_id=1,
        is_channel=False,
        user=make_user(),
        timestamp=NOW,
    )
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_admin_id


def test_message_edited_text() -> None:
    edited = MessageEdited(message=make_message(), timestamp=NOW)
    assert edited.text == "hello"


def test_message_callback_unsafe_message() -> None:
    with_message = MessageCallback(
        callback=make_callback(),
        message=make_message(),
        timestamp=NOW,
    )
    assert with_message.unsafe_message is with_message.message

    without_message = MessageCallback(
        callback=make_callback(),
        message=None,
        timestamp=NOW,
    )
    with pytest.raises(AttributeIsEmptyError):
        _ = without_message.unsafe_message


def test_message_callback_unsafe_user_locale() -> None:
    defined = MessageCallback(
        callback=make_callback(),
        user_locale="ru-RU",
        timestamp=NOW,
    )
    assert defined.unsafe_user_locale == "ru-RU"

    omitted = MessageCallback(callback=make_callback(), timestamp=NOW)
    with pytest.raises(AttributeIsEmptyError):
        _ = omitted.unsafe_user_locale


def test_comment_accessors() -> None:
    sender = make_user()
    body = CommentMessageBody(mid="comment", seq=1, text="Текст", markup=[])
    link = CommentLinkedMessage(
        message=body,
        type=MessageLinkType.REPLY,
        chat_id=10,
        sender=sender,
    )
    recipient = Recipient(chat_type=ChatType.CHANNEL, chat_id=10, post_id="post")
    removed = MessageRemoved(
        chat_id=10,
        message_id="comment",
        post_id="post",
        timestamp=NOW,
        user_id=20,
    )
    comment_removed = CommentRemoved(
        chat_id=10,
        message_id="comment",
        post_id="post",
        timestamp=NOW,
        user_id=20,
    )
    comment = CommentMessage(
        body=body,
        recipient=recipient,
        timestamp=NOW,
        link=link,
        sender=sender,
    )
    new_body = NewCommentBody(format=TextFormat.HTML)

    assert body.unsafe_markup == []
    assert body.unsafe_text == "Текст"
    assert link.unsafe_chat_id == 10
    assert link.unsafe_sender is sender
    assert recipient.unsafe_post_id == "post"
    assert removed.unsafe_post_id == "post"
    assert comment_removed.unsafe_post_id == "post"
    assert comment.unsafe_link is link
    assert comment.unsafe_sender is sender
    assert new_body.unsafe_format is TextFormat.HTML

    with pytest.raises(AttributeIsEmptyError):
        _ = new_body.unsafe_link
    with pytest.raises(AttributeIsEmptyError):
        _ = new_body.unsafe_text
    with pytest.raises(AttributeIsEmptyError):
        _ = NewCommentBody().unsafe_format
    with pytest.raises(AttributeIsEmptyError):
        _ = CommentMessageBody(mid="comment", seq=1).unsafe_markup
    with pytest.raises(AttributeIsEmptyError):
        _ = CommentMessageBody(mid="comment", seq=1).unsafe_text
    with pytest.raises(AttributeIsEmptyError):
        _ = CommentLinkedMessage(
            message=body,
            type=MessageLinkType.REPLY,
        ).unsafe_chat_id
    with pytest.raises(AttributeIsEmptyError):
        _ = CommentLinkedMessage(
            message=body,
            type=MessageLinkType.REPLY,
        ).unsafe_sender
    with pytest.raises(AttributeIsEmptyError):
        _ = CommentMessage(
            body=body,
            recipient=recipient,
            timestamp=NOW,
        ).unsafe_link
    with pytest.raises(AttributeIsEmptyError):
        _ = CommentMessage(
            body=body,
            recipient=recipient,
            timestamp=NOW,
        ).unsafe_sender
    with pytest.raises(AttributeIsEmptyError):
        _ = MessageRemoved(
            chat_id=10,
            message_id="comment",
            post_id=None,
            timestamp=NOW,
            user_id=20,
        ).unsafe_post_id
    with pytest.raises(AttributeIsEmptyError):
        _ = CommentRemoved(
            chat_id=10,
            message_id="comment",
            post_id=None,
            timestamp=NOW,
            user_id=20,
        ).unsafe_post_id

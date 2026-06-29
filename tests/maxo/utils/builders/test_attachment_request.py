# ruff: noqa: S106, S105

from decimal import Decimal

from maxo.types.audio_attachment_request import AudioAttachmentRequest
from maxo.types.callback_button import CallbackButton
from maxo.types.contact_attachment_request import ContactAttachmentRequest
from maxo.types.file_attachment_request import FileAttachmentRequest
from maxo.types.inline_keyboard_attachment_request import (
    InlineKeyboardAttachmentRequest,
)
from maxo.types.location_attachment_request import LocationAttachmentRequest
from maxo.types.photo_attachment_request import PhotoAttachmentRequest
from maxo.types.share_attachment_request import ShareAttachmentRequest
from maxo.types.sticker_attachment_request import StickerAttachmentRequest
from maxo.types.video_attachment_request import VideoAttachmentRequest
from maxo.utils.builders.attachment_request import AttachmentRequestBuilder


def test_attachment_request_builder_add_image_url():
    builder = AttachmentRequestBuilder()
    builder.add_image(url="https://example.com/image.jpg")
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], PhotoAttachmentRequest)
    assert attachments[0].payload.url == "https://example.com/image.jpg"


def test_attachment_request_builder_add_image_token():
    builder = AttachmentRequestBuilder()
    builder.add_image(token="photo_token_123")
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], PhotoAttachmentRequest)
    assert attachments[0].payload.token == "photo_token_123"


def test_attachment_request_builder_add_image_token_with_photos():
    builder = AttachmentRequestBuilder()
    builder.add_image(token="photo_token_456", photos=["id1", "id2"])
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], PhotoAttachmentRequest)
    assert attachments[0].payload.token == "photo_token_456"
    assert attachments[0].payload.photos[0].token == "id1"


def test_attachment_request_builder_add_video():
    builder = AttachmentRequestBuilder()
    builder.add_video(token="video_token_123")
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], VideoAttachmentRequest)
    assert attachments[0].payload.token == "video_token_123"


def test_attachment_request_builder_add_audio():
    builder = AttachmentRequestBuilder()
    builder.add_audio(token="audio_token_123")
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], AudioAttachmentRequest)
    assert attachments[0].payload.token == "audio_token_123"


def test_attachment_request_builder_add_file():
    builder = AttachmentRequestBuilder()
    builder.add_file(token="file_token_123")
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], FileAttachmentRequest)
    assert attachments[0].payload.token == "file_token_123"


def test_attachment_request_builder_add_sticker():
    builder = AttachmentRequestBuilder()
    builder.add_sticker(code="sticker_code_123")
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], StickerAttachmentRequest)
    assert attachments[0].payload.code == "sticker_code_123"


def test_attachment_request_builder_add_contact():
    builder = AttachmentRequestBuilder()
    builder.add_contact(
        name="Kirill Lesovoy",
        contact_id=42,
        vcf_info="BEGIN:VCARD...",
        vcf_phone="+79123456789",
    )
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], ContactAttachmentRequest)
    assert attachments[0].payload.name == "Kirill Lesovoy"
    assert attachments[0].payload.contact_id == 42
    assert attachments[0].payload.vcf_info == "BEGIN:VCARD..."
    assert attachments[0].payload.vcf_phone == "+79123456789"


def test_attachment_request_builder_add_inline_keyboard():
    builder = AttachmentRequestBuilder()
    buttons = [[CallbackButton(text="button", payload="data")]]
    builder.add_inline_keyboard(buttons=buttons)
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], InlineKeyboardAttachmentRequest)
    assert attachments[0].payload.buttons == buttons


def test_attachment_request_builder_add_location():
    builder = AttachmentRequestBuilder()
    builder.add_location(latitude=Decimal("12.34"), longitude=Decimal("56.78"))
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], LocationAttachmentRequest)
    assert attachments[0].latitude == 12.34
    assert attachments[0].longitude == 56.78


def test_attachment_request_builder_add_share_url():
    builder = AttachmentRequestBuilder()
    builder.add_share(url="https://example.com/share")
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], ShareAttachmentRequest)
    assert attachments[0].payload.url == "https://example.com/share"


def test_attachment_request_builder_add_share_token():
    builder = AttachmentRequestBuilder()
    builder.add_share(token="share_token_123")
    attachments = builder.build()
    assert len(attachments) == 1
    assert isinstance(attachments[0], ShareAttachmentRequest)
    assert attachments[0].payload.token == "share_token_123"


def test_attachment_request_builder_multiple_items():
    builder = AttachmentRequestBuilder()
    builder.add_image(url="http://example.com/image.jpg")
    builder.add_video(token="video_token_123")
    attachments = builder.build()
    assert len(attachments) == 2
    assert isinstance(attachments[0], PhotoAttachmentRequest)
    assert attachments[0].payload.url == "http://example.com/image.jpg"
    assert isinstance(attachments[1], VideoAttachmentRequest)
    assert attachments[1].payload.token == "video_token_123"

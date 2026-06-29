from maxo.enums.attachment_request_type import AttachmentRequestType
from maxo.types.share_attachment_request import ShareAttachmentRequest
from maxo.utils.hide_link import hide_link


def test_hide_link_returns_share_attachment_request() -> None:
    att = hide_link("https://example.com")
    assert isinstance(att, ShareAttachmentRequest)
    assert att.payload.url == "https://example.com"


def test_hide_link_type_is_share() -> None:
    att = hide_link("https://example.com")
    assert att.type is AttachmentRequestType.SHARE

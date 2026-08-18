from maxo.types.attachment_payload import AttachmentPayload


class StickerAttachmentPayload(AttachmentPayload):
    """
    Результат загрузки стикера

    Args:
        code: ID стикера
    """

    code: str
    """ID стикера"""

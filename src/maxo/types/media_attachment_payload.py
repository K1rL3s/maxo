from maxo.types.attachment_payload import AttachmentPayload


class MediaAttachmentPayload(AttachmentPayload):
    """
    Результат загрузки аудио/видео

    Args:
        token: Используйте `token`, если вы пытаетесь повторно использовать одно и то же вложение в другом сообщении
    """

    token: str
    """Используйте `token`, если вы пытаетесь повторно использовать одно и то же вложение в другом сообщении"""

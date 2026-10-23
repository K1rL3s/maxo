from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachment_payload import AttachmentPayload


class MediaAttachmentPayload(AttachmentPayload):
    """
    Результат загрузки аудио/видео

    Args:
        id: ID медиафайла. Одинаковый у одного и того же видео или аудио в разных сообщениях
        token: Используйте `token`, если вы пытаетесь повторно использовать одно и то же вложение в другом сообщении
    """

    token: str
    """Используйте `token`, если вы пытаетесь повторно использовать одно и то же вложение в другом сообщении"""

    id: Omittable[int | None] = Omitted()
    """ID медиафайла. Одинаковый у одного и того же видео или аудио в разных сообщениях"""

    @property
    def unsafe_id(self) -> int:
        if is_defined(self.id):
            return self.id

        raise AttributeIsEmptyError(
            obj=self,
            attr="id",
        )

from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachment_payload import AttachmentPayload


class FileAttachmentPayload(AttachmentPayload):
    """
    Результат загрузки файла

    Args:
        file_id: ID файла
        token: Используйте `token`, если вы пытаетесь повторно использовать одно и то же вложение в другом сообщении.
    """

    token: str
    """Используйте `token`, если вы пытаетесь повторно использовать одно и то же вложение в другом сообщении."""

    file_id: Omittable[int | None] = Omitted()
    """ID файла"""

    @property
    def unsafe_file_id(self) -> int:
        if is_defined(self.file_id):
            return self.file_id

        raise AttributeIsEmptyError(
            obj=self,
            attr="file_id",
        )

    @property
    def id(self) -> Omittable[int | None]:
        return self.file_id

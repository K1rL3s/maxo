from typing import Self

from maxo.enums.attachment_type import AttachmentType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.attachment import Attachment
from maxo.types.audio_attachment_request import AudioAttachmentRequest
from maxo.types.media_attachment_payload import MediaAttachmentPayload


class AudioAttachment(Attachment):
    """
    Args:
        payload: Результат загрузки аудиосообщения или аудиофайла. В ответах на запросы о сообщениях аудиосообщения имеют тип `audio`
        transcription: Аудио транскрипция
        type:
    """

    type: AttachmentType = AttachmentType.AUDIO

    payload: MediaAttachmentPayload
    """Результат загрузки аудиосообщения или аудиофайла. В ответах на запросы о сообщениях аудиосообщения имеют тип `audio`"""

    transcription: Omittable[str | None] = Omitted()
    """Аудио транскрипция"""

    @classmethod
    def factory(
        cls,
        url: str,
        token: str,
        transcription: Omittable[str | None] = Omitted(),
    ) -> Self:
        """
        Фабричный метод.

        Args:
            url: URL медиа-вложения. Для видео-вложения используйте метод GetVideoAttachmentDetails, чтобы получить прямые ссылки.
            token: Используйте token, если вы пытаетесь повторно использовать одно и то же вложение в другом сообщении.
            transcription: Транскрипция аудио.

        """
        return cls(
            payload=MediaAttachmentPayload(
                url=url,
                token=token,
            ),
            transcription=transcription,
        )

    @property
    def unsafe_transcription(self) -> str:
        if is_defined(self.transcription):
            return self.transcription

        raise AttributeIsEmptyError(
            obj=self,
            attr="transcription",
        )

    def to_request(self) -> AudioAttachmentRequest:
        return AudioAttachmentRequest.factory(token=self.payload.token)

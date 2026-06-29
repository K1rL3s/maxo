from pathlib import Path
from typing import Any

from maxo.enums import AttachmentType
from maxo.types import MaxoType


class MediaId(MaxoType):
    token: str

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MediaId):
            return False
        return self.token == other.token

    __hash__ = None


class MediaAttachment:
    def __init__(
        self,
        type: AttachmentType,
        url: str | None = None,
        path: Path | str | None = None,
        media_id: MediaId | None = None,
        file_id: MediaId | None = None,
        use_pipe: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Медиа аттачмент, которые хавают диалоги.

        file_id: Алиас к `media_id`,
                 потому что в aiogram_dialog используется `file_id`.
                 Приоритет у `media_id`
        """
        media_id = media_id if media_id is not None else file_id
        if not (url or path or media_id):
            raise ValueError("Neither url nor path nor media_id are provided")
        self.type = type
        self.url = url
        self.path = path
        self.media_id = media_id
        self.use_pipe = use_pipe
        self.kwargs = kwargs

    @property
    def file_id(self) -> MediaId | None:
        return self.media_id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MediaAttachment):
            return False
        if type(other) is not type(self):
            return False
        return bool(
            self.type == other.type
            and self.url == other.url
            and self.path == other.path
            and self.media_id == other.media_id
            and self.use_pipe == other.use_pipe
            and self.kwargs == other.kwargs,
        )

    __hash__ = None

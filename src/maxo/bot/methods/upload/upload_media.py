from typing import Any

from unihttp.http import HTTPResponse, UploadFile

from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import File, Path
from maxo.errors import RetvalReturnedServerException
from maxo.types.upload_media_result import UploadMediaResult


# Самодельный метод по доке
# https://dev.max.ru/docs-api/methods/POST/uploads
class UploadMedia(MaxoMethod[UploadMediaResult]):
    """
    Загрузка медиа.

    Args:
        upload_url: URL для загрузки медиа.
        file: Загружаемый файл.
    """

    __url__ = "{upload_url}"
    __method__ = "post"

    upload_url: Path[str]
    file: File[UploadFile]

    def validate_response(self, response: HTTPResponse[Any]) -> None:
        if response.data == b"<retval>1</retval>":
            raise RetvalReturnedServerException

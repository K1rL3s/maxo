from typing import Any

from unihttp.http import HTTPResponse, UploadFile
from unihttp.serialize import ResponseLoader

from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import File, Path
from maxo.types.upload_media_result import UploadMediaResult


# Самодельный метод по доке
# https://dev.max.ru/docs-api/methods/POST/uploads
class UploadMedia(MaxoMethod[UploadMediaResult | None]):
    """
    Загрузка медиа.

    `None`, если хост ответил `<retval>1</retval>`: тогда токен есть в
    ответе `get_upload_url`.

    Args:
        upload_url: URL для загрузки медиа.
        file: Загружаемый файл.
    """

    __url__ = "{upload_url}"
    __method__ = "post"

    upload_url: Path[str]
    file: File[UploadFile]

    def make_response(
        self,
        response: HTTPResponse[Any],
        response_loader: ResponseLoader,
    ) -> UploadMediaResult | None:
        if response.data == b"<retval>1</retval>":
            return None
        return super().make_response(response, response_loader)

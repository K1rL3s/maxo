from typing import Any

from unihttp.http import HTTPResponse
from unihttp.serialize import ResponseLoader

from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Header, Path, Raw

# unihttp парсит JSON сам (см. `AiohttpAsyncClient.make_request`), а при
# нераспарсиваемом теле отдаёт сырые байты как есть.
UploadResponseBody = dict[str, Any] | list[Any] | bytes


# Custom method
class ChunkUpload(MaxoMethod[UploadResponseBody]):
    """Один кусок resumable-загрузки: промежуточный - 201, финальный - 200."""

    __url__ = "{upload_url}"
    __method__ = "post"

    upload_url: Path[str]

    # see https://github.com/max-messenger/max-bot-api-client-ts/blob/adcc479203acd7bf6e664a88c2f2559be3edea60/src/helpers/upload/upload.ts#L211
    content_range: Header[str]
    content_disposition: Header[str]
    content_type: Header[str] = "application/octet-stream"
    # Lets a failed chunk be resent on a new connection
    x_uploading_mode: Header[str] = "parallel"

    chunk: Raw[bytes]

    def make_response(
        self,
        response: HTTPResponse[Any],
        response_loader: ResponseLoader,
    ) -> UploadResponseBody:
        # Already parsed JSON or raw bytes
        return response.data  # type: ignore[no-any-return]

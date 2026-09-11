from dataclasses import dataclass
from typing import Any

from unihttp.http import HTTPRequest, HTTPResponse
from unihttp.method import BaseMethod
from unihttp.serialize import RequestDumper, ResponseLoader

# unihttp парсит JSON сам (см. `AiohttpAsyncClient.make_request`), а при
# нераспарсиваемом теле отдаёт сырые байты как есть.
UploadResponseBody = dict[str, Any] | list[Any] | bytes


@dataclass
class _ChunkUpload(  # type: ignore[no-untyped-call]
    BaseMethod[HTTPResponse[UploadResponseBody]],
):
    """Сырой POST чанка resumable upload."""

    url: str
    chunk: bytes
    headers: dict[str, str]

    __method__ = "POST"

    def build_http_request(self, request_dumper: RequestDumper) -> HTTPRequest:
        return HTTPRequest(
            url=self.url,
            method=self.__method__,
            header=dict(self.headers),
            path={},
            query={},
            body={},
            file={},
            form=None,
            raw=self.chunk,
        )

    def on_error(self, response: HTTPResponse[UploadResponseBody]) -> None:
        pass

    def make_response(
        self,
        response: HTTPResponse[UploadResponseBody],
        response_loader: ResponseLoader,
    ) -> HTTPResponse[UploadResponseBody]:
        return response

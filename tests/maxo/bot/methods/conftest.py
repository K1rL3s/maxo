from http.cookies import SimpleCookie
from unittest.mock import AsyncMock

from multidict import CIMultiDict
from unihttp.http import HTTPResponse


def response(data: object, status_code: int = 200) -> HTTPResponse:
    return HTTPResponse(
        status_code=status_code,
        data=data,
        headers=CIMultiDict(),
        cookies=SimpleCookie(),
        raw_response=AsyncMock(),
    )

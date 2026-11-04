import pytest
from unihttp.http import UploadFile

from maxo.bot.methods.upload.upload_media import UploadMedia
from maxo.errors import MaxBotBadRequestError, RetvalReturnedError

from .conftest import response


def method() -> UploadMedia:
    return UploadMedia(
        upload_url="https://example.com",
        file=UploadFile(file=b"video", filename="video.mp4"),
    )


def test_retval_response_raises_retval_returned_error() -> None:
    with pytest.raises(RetvalReturnedError, match="POST /uploads"):
        method().validate_response(response(b"<retval>1</retval>"))


def test_token_response_passes_validation() -> None:
    method().validate_response(response({"token": "file-token"}))


def test_error_code_response_raises_bad_request() -> None:
    body = {"error_code": "some_error", "message": "denied"}

    with pytest.raises(MaxBotBadRequestError) as exc_info:
        method().validate_response(response(body))

    assert exc_info.value.raw_data == body

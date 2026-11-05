from maxo import errors, exceptions
from maxo.errors import UnsubscribeError


def test_unsubscribe_error_str() -> None:
    failure = ValueError("boom")
    error = UnsubscribeError(url="https://one.example/webhook", error=failure)

    assert str(error) == (
        "Не удалось удалить WebHook-подписку 'https://one.example/webhook': boom"
    )


def test_unsubscribe_error_is_reexported_from_exceptions_alias() -> None:
    # `maxo.exceptions` - постоянный алиас `maxo.errors`, состав должен совпадать.
    assert exceptions.UnsubscribeError is errors.UnsubscribeError
    assert "UnsubscribeError" in exceptions.__all__

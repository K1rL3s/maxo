from maxo.errors import UnsubscribeError


def test_unsubscribe_error_str() -> None:
    failure = ValueError("boom")
    error = UnsubscribeError(url="https://one.example/webhook", error=failure)

    assert str(error) == (
        "Не удалось удалить WebHook-подписку 'https://one.example/webhook': boom"
    )

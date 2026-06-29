from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.simple_query_result import SimpleQueryResult


class UnpinMessage(MaxoMethod[SimpleQueryResult]):
    """
    Открепление сообщения в групповом чате или канале

    Открепляет сообщение в групповом чате или канале 

    Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала 

    Пример запроса:
    ```bash
    curl -X DELETE "https://platform-api.max.ru/chats/{chatId}/pin" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID группового чата или канала, в котором нужно открепить сообщение или пост

    Источник: https://dev.max.ru/docs-api/methods/DELETE/chats/-chatId-/pin
    """

    __url__ = "chats/{chat_id}/pin"
    __method__ = "delete"

    chat_id: Path[int]
    """ID группового чата или канала, в котором нужно открепить сообщение или пост"""

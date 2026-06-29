from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.simple_query_result import SimpleQueryResult


class DeleteChat(MaxoMethod[SimpleQueryResult]):
    """
    Удаление группового чата

    Удаляет групповой чат для всех участников

    #### Пример запроса:
    ```bash
    curl -X DELETE "https://platform-api.max.ru/chats/{chatId}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID чата

    Источник: https://dev.max.ru/docs-api/methods/DELETE/chats/-chatId-
    """

    __url__ = "chats/{chat_id}"
    __method__ = "delete"

    chat_id: Path[int]
    """ID чата"""

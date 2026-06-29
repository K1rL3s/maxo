from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.simple_query_result import SimpleQueryResult


class LeaveChat(MaxoMethod[SimpleQueryResult]):
    """
    Удаление бота из группового чата или канала

    Удаляет бота из участников группового чата или канала

    Пример запроса:
    ```bash
    curl -X DELETE "https://platform-api.max.ru/chats/{chatId}/members/me" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID группового чата или канала

    Источник: https://dev.max.ru/docs-api/methods/DELETE/chats/-chatId-/members/me
    """

    __url__ = "chats/{chat_id}/members/me"
    __method__ = "delete"

    chat_id: Path[int]
    """ID группового чата или канала"""

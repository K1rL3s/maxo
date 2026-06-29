from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.simple_query_result import SimpleQueryResult


class DeleteAdmin(MaxoMethod[SimpleQueryResult]):
    """
    Отменить права администратора в групповом чате или канале

    Лишает пользователя или бота прав администратора в групповом чате или канале. При этом из чата и канала они не исключаются 

    Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала с соответствующим правом `add_admins`. Чтобы получить информацию о правах бота, используйте [GET /chats/-chatId-/members/admins](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins). Подробнее о правах - в описании объекта [`Chat`](https://dev.max.ru/docs-api/objects/Chat) 

    Пример запроса:
    ```bash
    curl -X DELETE "https://platform-api.max.ru/chats/{chatId}/members/admins/{userId}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID группового чата или канала
        user_id: Идентификатор пользователя или бота, которого надо лишить прав администратора

    Источник: https://dev.max.ru/docs-api/methods/DELETE/chats/-chatId-/members/admins/-userId-
    """

    __url__ = "chats/{chat_id}/members/admins/{user_id}"
    __method__ = "delete"

    chat_id: Path[int]
    """ID группового чата или канала"""
    user_id: Path[int]
    """Идентификатор пользователя или бота, которого надо лишить прав администратора"""

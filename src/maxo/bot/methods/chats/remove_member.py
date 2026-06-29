from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path, Query
from maxo.omit import Omittable, Omitted
from maxo.types.simple_query_result import SimpleQueryResult


class RemoveMember(MaxoMethod[SimpleQueryResult]):
    """
    Удаление участника из группового чата или канала

    Удаляет участника из группового чата или канала

     Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала с соответствующим правом `add_remove_members`. Чтобы получить информацию о правах бота, используйте [GET /chats/-chatId-/members/admins](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins). Подробнее о правах - в описании объекта [`Chat`](https://dev.max.ru/docs-api/objects/Chat) 

    Пример запроса:
    ```bash
    curl -X DELETE "https://platform-api.max.ru/chats/{chatId}/members?user_id={user_id}&block=true" \
      -H "Authorization: {access_token}"
    ```

    Args:
        block: Если передать `true`, пользователь будет заблокирован в чате. Применяется только для чатов с публичной или приватной ссылкой. Игнорируется в остальных случаях
        chat_id: ID группового чата или канала
        user_id: ID пользователя, которого нужно удалить из группового чата или канала

    Источник: https://dev.max.ru/docs-api/methods/DELETE/chats/-chatId-/members
    """

    __url__ = "chats/{chat_id}/members"
    __method__ = "delete"

    chat_id: Path[int]
    """ID группового чата или канала"""

    user_id: Query[int]
    """ID пользователя, которого нужно удалить из группового чата или канала"""
    block: Query[Omittable[bool]] = Omitted()
    """Если передать `true`, пользователь будет заблокирован в чате. Применяется только для чатов с публичной или приватной ссылкой. Игнорируется в остальных случаях"""

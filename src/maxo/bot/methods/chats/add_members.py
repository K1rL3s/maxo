from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Path
from maxo.types.modify_members_result import ModifyMembersResult


class AddMembers(MaxoMethod[ModifyMembersResult]):
    """
    Добавление участников в групповой чат или канал

    Добавляет участников в групповой чат или канал 

     Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала с соответствующим правом `add_remove_members`. Чтобы получить информацию о правах бота, используйте [GET /chats/-chatId-/members/admins](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins). Подробнее о правах - в описании объекта [`Chat`](https://dev.max.ru/docs-api/objects/Chat)

    Пример запроса:
    ```bash
    curl -X POST "https://platform-api.max.ru/chats/{chatId}/members" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
      "user_ids": ["{user_id_1}", "{user_id_2}"]
    }'
    ```

    Args:
        chat_id: ID группового чата или канала
        user_ids: 

    Источник: https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members
    """

    __url__ = "chats/{chat_id}/members"
    __method__ = "post"

    chat_id: Path[int]
    """ID группового чата или канала"""

    user_ids: Body[list[int]]

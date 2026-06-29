from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.chat_member import ChatMember


class GetMembership(MaxoMethod[ChatMember]):
    """
    Получение информации о членстве бота в групповом чате или канале

    Возвращает информацию о членстве бота в групповом чате или канале, общую информацию о нём, а также список [доступных прав доступа](https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members/admins#Доступные%20права%20администраторов). Бот идентифицируется с помощью токена доступа

    Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/chats/{chatId}/members/me" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID группового чата или канала

    Источник: https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/me
    """

    __url__ = "chats/{chat_id}/members/me"
    __method__ = "get"

    chat_id: Path[int]
    """ID группового чата или канала"""

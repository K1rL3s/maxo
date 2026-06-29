from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.get_pinned_message_result import GetPinnedMessageResult


class GetPinnedMessage(MaxoMethod[GetPinnedMessageResult]):
    """
    Получение закреплённого сообщения в групповом чате или канале

    Возвращает закреплённое сообщение в групповом чате или канале 

    Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала 

    Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/chats/{chatId}/pin" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID чата

    Источник: https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/pin
    """

    __url__ = "chats/{chat_id}/pin"
    __method__ = "get"

    chat_id: Path[int]
    """ID чата"""

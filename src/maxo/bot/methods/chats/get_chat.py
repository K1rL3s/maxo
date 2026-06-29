from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.chat import Chat


class GetChat(MaxoMethod[Chat]):
    """
    Получение информации о групповом чате или канале

    Возвращает информацию о групповом чате или канале по его ID

    Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/chats/{chatId}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID запрашиваемого группового чата или канала. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)

    Источник: https://dev.max.ru/docs-api/methods/GET/chats/-chatId-
    """

    __url__ = "chats/{chat_id}"
    __method__ = "get"

    chat_id: Path[int]
    """ID запрашиваемого группового чата или канала. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""

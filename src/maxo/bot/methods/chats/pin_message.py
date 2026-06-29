from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Path
from maxo.omit import Omittable, Omitted
from maxo.types.simple_query_result import SimpleQueryResult


class PinMessage(MaxoMethod[SimpleQueryResult]):
    """
    Закрепление сообщения в групповом чате или канале

    Закрепляет сообщение в групповом чате или канале 

    Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала 

    Пример запроса:
    ```bash
    curl -X PUT "https://platform-api.max.ru/chats/{chatId}/pin" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
      "message_id": "{message_id}",
      "notify": true
    }'
    ```

    Args:
        chat_id: ID группового чата или канала, где нужно закрепить сообщение
        message_id: ID сообщения, которое нужно закрепить. Соответствует полю `Message.body.mid`
        notify: Если `true`, участники получат уведомление с системным сообщением о закреплении

    Источник: https://dev.max.ru/docs-api/methods/PUT/chats/-chatId-/pin
    """

    __url__ = "chats/{chat_id}/pin"
    __method__ = "put"

    chat_id: Path[int]
    """ID группового чата или канала, где нужно закрепить сообщение"""

    message_id: Body[str]
    """ID сообщения, которое нужно закрепить. Соответствует полю `Message.body.mid`"""
    notify: Body[Omittable[bool | None]] = Omitted()
    """Если `true`, участники получат уведомление с системным сообщением о закреплении"""

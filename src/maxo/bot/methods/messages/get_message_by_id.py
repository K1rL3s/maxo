from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.message import Message


class GetMessageById(MaxoMethod[Message]):
    """
    Получение сообщений

    Возвращает сообщение из канала или чата по его ID

    #### Пример запроса:
    ```bash
    curl -X GET "https://platform-api2.max.ru/messages/{messageId}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        message_id: ID сообщения (`mid`), чтобы получить одно сообщение в чате или канале

    Источник: https://dev.max.ru/docs-api/methods/GET/messages/-messageId-
    """

    __url__ = "messages/{message_id}"
    __method__ = "get"

    message_id: Path[str]
    """ID сообщения (`mid`), чтобы получить одно сообщение в чате или канале"""

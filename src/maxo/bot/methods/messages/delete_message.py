from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Query
from maxo.types.simple_query_result import SimpleQueryResult


class DeleteMessage(MaxoMethod[SimpleQueryResult]):
    """
    Удалить сообщение

    Удаляет сообщение в диалоге или чате, если бот имеет разрешение на удаление сообщений

    #### Пример запроса:
    ```bash
    curl -X DELETE "https://platform-api.max.ru/messages?message_id={message_id}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        message_id: ID удаляемого сообщения

    Источник: https://dev.max.ru/docs-api/methods/DELETE/messages
    """

    __url__ = "messages"
    __method__ = "delete"

    message_id: Query[str]
    """ID удаляемого сообщения"""

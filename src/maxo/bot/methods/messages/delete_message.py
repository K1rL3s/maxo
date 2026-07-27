from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Query
from maxo.types.simple_query_result import SimpleQueryResult


class DeleteMessage(MaxoMethod[SimpleQueryResult]):
    """
    Удалить сообщение

    Удаляет сообщения в диалоге, групповом чате или канале

     #### Ограничения
    - Бот должен быть администратором и иметь право на удаление сообщений
    - Бот может удалять сообщения:
        - в диалоге - только сообщения, отправленные самим ботом
        - в групповом чате - любые сообщения
        - в канале - любые сообщения
    - Можно удалять не более двух сообщений в секунду в одном диалоге, групповом чате или канале. При превышении этого лимита сообщения следует ставить в очередь или делать задержку перед удалением

    #### Пример запроса:
    ```bash
    curl -X DELETE "https://platform-api2.max.ru/messages?message_id={message_id}" \
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

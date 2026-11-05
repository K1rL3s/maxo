from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path, Query
from maxo.types.simple_query_result import SimpleQueryResult


class DeleteComment(MaxoMethod[SimpleQueryResult]):
    """
    Удаление комментария

    Удаляет комментарий пользователя или бота к посту в канале

    • С помощью метода можно удалять как чужие комментарии, так и свои
    • Если канал архивирован или в нём [отключены комментарии](https://dev.max.ru/docs/channels/manage#Как%20отключить%20комментарии%20в%20канале), по-прежнему можно удалять старые комментарии
    • Если комментарий удалён ошибочно, восстановить его нельзя

     Для удаления комментария бот, чей токен `access_token` используется для авторизации, должен быть администратором этого канала с правами `read_all_messages` и `delete`

    Чтобы получить информацию о правах бота, используйте [`GET /chats/-chatId-/members/admins`](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins). Подробнее о правах - в описании [`POST /chats/{chatId}/members/admins`](https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members/admins#Доступные%20права%20администратора)

    **Пример запроса**:
    ```bash
    curl -X DELETE "https://platform-api2.max.ru/messages/{messageId}/comments?comment_id={comment_id}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        comment_id: Идентификатор удаляемого комментария
        message_id: Идентификатор поста (`mid`), комментарий к которому надо удалить

    Источник: https://dev.max.ru/docs-api/methods/DELETE/messages/-messageId-/comments
    """

    __url__ = "messages/{message_id}/comments"
    __method__ = "delete"

    message_id: Path[str]
    """Идентификатор поста (`mid`), комментарий к которому надо удалить"""

    comment_id: Query[str]
    """Идентификатор удаляемого комментария"""

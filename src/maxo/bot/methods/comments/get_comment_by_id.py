from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path
from maxo.types.comment_message import CommentMessage


class GetCommentById(MaxoMethod[CommentMessage]):
    """
    Получение комментария по его ID

    Возвращает информацию о комментарии к посту в канале по его идентификатору (`mid`)

    Для этого бот, чей токен `access_token` используется для авторизации, должен быть администратором этого канала с правом `read_all_messages`

     Чтобы получить информацию о правах бота, используйте [`GET /chats/-chatId-/members/admins`](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins). Подробнее о правах - в описании [`POST /chats/{chatId}/members/admins`](https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members/admins#Доступные%20права%20администратора)

    **Пример запроса**:
    ```bash
    curl -X GET "https://platform-api2.max.ru/messages/{messageId}/comments/{commentId}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        comment_id: Идентификатор комментария (`mid`)
        message_id: Идентификатор поста (`mid`), к которому относится комментарий

    Источник: https://dev.max.ru/docs-api/methods/GET/messages/-messageId-/comments/-commentId-
    """

    __url__ = "messages/{message_id}/comments/{comment_id}"
    __method__ = "get"

    comment_id: Path[str]
    """Идентификатор комментария (`mid`)"""
    message_id: Path[str]
    """Идентификатор поста (`mid`), к которому относится комментарий"""

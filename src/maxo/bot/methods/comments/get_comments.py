from datetime import datetime

from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Path, Query
from maxo.omit import Omittable, Omitted
from maxo.types.comment_message_list import CommentMessageList


class GetComments(MaxoMethod[CommentMessageList]):
    """
    Получение всех комментариев к посту

    Возвращает все комментарии к посту в канале по его ID: страницу результата и маркер на следующую страницу. Вы можете отфильтровать комментарии: указать промежуток времени, за который хотите их получить, и/или запросить N последних

    Для получения комментариев к посту бот, чей токен `access_token` используется для авторизации, должен быть администратором этого канала с правом `read_all_messages`

     Чтобы получить информацию о правах бота, используйте [`GET /chats/-chatId-/members/admins`](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins). Подробнее о правах - в описании [`POST /chats/{chatId}/members/admins`](https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members/admins#Доступные%20права%20администратора)

    **Пример запроса с фильтрацией по времени и количеству последних комментариев за этот промежуток**:
    ```bash
    curl -X GET "https://platform-api2.max.ru/messages/{messageId}/comments?after={after}&before={before}&count={count}" \
      -H "Authorization: {access_token}"
    ```

    **Пример запроса конкретных комментариев к посту по их ID**:
    ```bash
    curl -X GET "https://platform-api2.max.ru/messages/{messageId}/comments?comment_ids={comment_ids1},{comment_ids2},{comment_ids3}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        after: Время, начиная с которого будут запрошены все комментарии до конца чата (в формате Unix timestamp в миллисекундах)
             Минимум: `0`
        before: Время, до которого будут запрошены все комментарии с начала чата (в формате Unix timestamp в миллисекундах)
            Минимум: `0`
        comment_ids: Список идентификаторов комментариев, которые вы хотите получить, - укажите через запятую
            Если параметр указан, возвращаются только запрошенные комментарии: пагинация игнорируется
        count: Количество комментариев, которое вы хотите получить в ответе: от `1` до `100`
        message_id: Идентификатор поста (`mid`), к которому относится комментарий

    Источник: https://dev.max.ru/docs-api/methods/GET/messages/-messageId-/comments
    """

    __url__ = "messages/{message_id}/comments"
    __method__ = "get"

    message_id: Path[str]
    """Идентификатор поста (`mid`), к которому относится комментарий"""

    after: Query[Omittable[datetime]] = Omitted()
    """
    Время, начиная с которого будут запрошены все комментарии до конца чата (в формате Unix timestamp в миллисекундах)

     Минимум: `0`
    """
    before: Query[Omittable[datetime]] = Omitted()
    """
    Время, до которого будут запрошены все комментарии с начала чата (в формате Unix timestamp в миллисекундах)

    Минимум: `0`
    """
    comment_ids: Query[Omittable[list[str] | None]] = Omitted()
    """
    Список идентификаторов комментариев, которые вы хотите получить, - укажите через запятую

    Если параметр указан, возвращаются только запрошенные комментарии: пагинация игнорируется
    """
    count: Query[Omittable[int]] = Omitted()
    """Количество комментариев, которое вы хотите получить в ответе: от `1` до `100`"""

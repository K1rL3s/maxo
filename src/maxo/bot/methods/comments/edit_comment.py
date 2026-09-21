from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Path, Query
from maxo.enums.text_format import TextFormat
from maxo.omit import Omittable, Omitted
from maxo.types.new_message_link import NewMessageLink
from maxo.types.simple_query_result import SimpleQueryResult


class EditComment(MaxoMethod[SimpleQueryResult]):
    """
    Редактирование комментария

    Редактирует комментарий бота к посту в канале

    Для редактирования комментария бот, чей токен `access_token` используется для авторизации, должен быть участником этого канала

    С помощью метода можно редактировать:
    • Комментарии, которые опубликованы от имени канала,  - если боту назначено право администратора `edit`
    • Только свои комментарии - если у бота нет права администратора `edit`

    Если канал архивирован или в нём [отключены комментарии](https://dev.max.ru/docs/channels/manage#Как%20отключить%20комментарии%20в%20канале), бот может редактировать старые комментарии

     Чтобы получить информацию о правах бота, используйте [`GET /chats/-chatId-/members/admins`](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins). Подробнее о правах - в описании [`POST /chats/{chatId}/members/admins`](https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members/admins#Доступные%20права%20администратора)

    #### Пример запроса:
    ```bash
    curl -X PUT "https://platform-api2.max.ru/messages/{messageId}/comments?comment_id={commentId}" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
      "text": "Изменённый текст"
    }'
    ```

    Args:
        comment_id: Идентификатор редактируемого комментария
        format: Разметка текста комментария. Для комментариев не поддерживается упоминание других пользователей и гиперссылки. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)
        link: Ссылка на комментарий
        message_id: Идентификатор поста (`mid`), комментарий к которому вы хотите отредактировать
        text: Текст комментария

    Источник: https://dev.max.ru/docs-api/methods/PUT/messages/-messageId-/comments
    """

    __url__ = "messages/{message_id}/comments"
    __method__ = "put"

    message_id: Path[str]
    """Идентификатор поста (`mid`), комментарий к которому вы хотите отредактировать"""

    comment_id: Query[str]
    """Идентификатор редактируемого комментария"""

    link: Body[NewMessageLink | None] = None
    """Ссылка на комментарий"""
    text: Body[str | None] = None
    """Текст комментария"""
    format: Body[Omittable[TextFormat | None]] = Omitted()
    """Разметка текста комментария. Для комментариев не поддерживается упоминание других пользователей и гиперссылки. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)"""

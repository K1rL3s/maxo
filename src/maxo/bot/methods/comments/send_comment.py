from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Path, Query
from maxo.enums.text_format import TextFormat
from maxo.omit import Omittable, Omitted
from maxo.types.new_message_link import NewMessageLink
from maxo.types.send_comment_result import SendCommentResult


class SendComment(MaxoMethod[SendCommentResult]):
    """
    Отправка комментария

    Отправляет комментарий к посту в канале

     Для этого:

    • В настройках канала должны быть [включены комментарии](https://dev.max.ru/docs/channels/manage#Как%20включить%20комментарии%20в%20канале)
    • Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого канала c правами `read_all_messages` и `write`


     Чтобы получить информацию о правах бота, используйте [`GET /chats/-chatId-/members/admins`](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members/admins). Подробнее о правах - в описании [`GET /chats/{chatId}/members/admins`](https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/members/admins#Доступные%20права%20администратора)

    **Пример запроса**:
    ```bash
    curl -X POST "https://platform-api2.max.ru/messages/{messageId}/comments" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{"text": "Новый комментарий"}'
    ```

    Args:
        disable_link_preview: Если `false`, сервер не будет генерировать предпросмотр для ссылок в тексте. Работает только для десктоп-клиента
        format: Разметка текста комментария. Для комментариев не поддерживается упоминание других пользователей и гиперссылки. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)
        link: Ссылка на комментарий
        message_id: Идентификатор сообщения (`mid`), к которому относится комментарий
        text: Текст комментария

    Источник: https://dev.max.ru/docs-api/methods/POST/messages/-messageId-/comments
    """

    __url__ = "messages/{message_id}/comments"
    __method__ = "post"

    message_id: Path[str]
    """Идентификатор сообщения (`mid`), к которому относится комментарий"""

    disable_link_preview: Query[Omittable[bool]] = Omitted()
    """Если `false`, сервер не будет генерировать предпросмотр для ссылок в тексте. Работает только для десктоп-клиента"""

    link: Body[NewMessageLink | None] = None
    """Ссылка на комментарий"""
    text: Body[str | None] = None
    """Текст комментария"""
    format: Body[Omittable[TextFormat | None]] = Omitted()
    """Разметка текста комментария. Для комментариев не поддерживается упоминание других пользователей и гиперссылки. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)"""

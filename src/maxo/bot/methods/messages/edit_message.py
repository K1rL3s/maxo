from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Query
from maxo.enums.text_format import TextFormat
from maxo.omit import Omittable, Omitted
from maxo.types.attachments import Attachments, AttachmentsRequests
from maxo.types.new_message_link import NewMessageLink
from maxo.types.simple_query_result import SimpleQueryResult


class EditMessage(MaxoMethod[SimpleQueryResult]):
    """
    Редактирование сообщений

    Редактирует сообщения и посты, отправленные ботом

      #### Ограничения
    - Есть особенности редактирования сообщений в диалогах с ботом, связанные со сроком давности:
        - сообщения с кнопками [`inline_keyboard`](https://dev.max.ru/docs-api#Как%20добавить%20кнопки) редактируются независимо от срока давности
        - остальные сообщения редактируются, если они отправлены менее 7 суток назад
    - В групповых чатах и каналах любые сообщения редактируются независимо от срока давности
    - Можно редактировать не более двух сообщений в секунду в одном диалоге, групповом чате или канале. При превышении этого лимита сообщения следует ставить в очередь или делать задержку перед редактированием

    #### Пример запроса:
    ```bash
    curl -X PUT "https://platform-api2.max.ru/messages?message_id=message_id" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
      "text": "Изменённый текст"
    }'
    ```

    Args:
        attachments: Вложения сообщения. Если поле равно `null`, изменений не произойдет. Если массив пуст, все вложения будут удалены
        format: Если установлен, текст сообщения будет форматирован данным способом. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)
        link: Ссылка на сообщение
        message_id: ID редактируемого сообщения
        notify: Если `false`, участники чата не получат push-уведомления. Для каналов необходимо отправлять запрос с `notify = true` или без этого поля, т.к. каналы не подразумевают отправку постов без push-уведомлений
        text:

    Источник: https://dev.max.ru/docs-api/methods/PUT/messages
    """

    __url__ = "messages"
    __method__ = "put"

    message_id: Query[str]
    """ID редактируемого сообщения"""

    attachments: Body[list[AttachmentsRequests | Attachments] | None] = None
    """Вложения сообщения. Если поле равно `null`, изменений не произойдет. Если массив пуст, все вложения будут удалены"""
    link: Body[NewMessageLink | None] = None
    """Ссылка на сообщение"""
    text: Body[str | None] = None
    format: Body[Omittable[TextFormat | None]] = Omitted()
    """Если установлен, текст сообщения будет форматирован данным способом. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)"""
    notify: Body[Omittable[bool]] = Omitted()
    """Если `false`, участники чата не получат push-уведомления. Для каналов необходимо отправлять запрос с `notify = true` или без этого поля, т.к. каналы не подразумевают отправку постов без push-уведомлений"""

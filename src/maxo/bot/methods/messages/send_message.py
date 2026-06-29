from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Query
from maxo.enums.text_format import TextFormat
from maxo.omit import Omittable, Omitted
from maxo.types.attachments import Attachments, AttachmentsRequests
from maxo.types.new_message_link import NewMessageLink
from maxo.types.send_message_result import SendMessageResult


class SendMessage(MaxoMethod[SendMessageResult]):
    """
    Отправить сообщение

    Отправляет сообщение в чат

    #### Пример запроса с одной кнопкой-ссылкой

    Больше примеров запросов с кнопками - [в разделе «Клавиатура»](https://dev.max.ru/docs-api#Как%20добавить%20кнопки)
    ```bash
    curl -X POST "https://platform-api.max.ru/messages?user_id={user_id}" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
      "text": "Это сообщение с кнопкой-ссылкой",
      "attachments": [
        {
          "type": "inline_keyboard",
          "payload": {
            "buttons": [
              [
                {
                  "type": "link",
                  "text": "Откройте сайт",
                  "url": "https://example.com"
                }
              ]
            ]
          }
        }
      ]
     }'
    ```

    Args:
        attachments: Вложения сообщения. Если поле равно `null`, изменений не произойдет. Если пусто, все вложения будут удалены
        chat_id: Если сообщение отправляется в чат, укажите его ID. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        disable_link_preview: Если `false`, сервер не будет генерировать превью для ссылок в тексте сообщения
        format: Если установлен, текст сообщения будет форматирован данным способом. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)
        link: Ссылка на сообщение
        notify: Если false, участники чата не будут уведомлены (по умолчанию `true`)
        text: Новый текст сообщения
        user_id: Если вы хотите отправить сообщение пользователю, укажите его ID

    Источник: https://dev.max.ru/docs-api/methods/POST/messages
    """

    __url__ = "messages"
    __method__ = "post"

    chat_id: Query[Omittable[int]] = Omitted()
    """Если сообщение отправляется в чат, укажите его ID. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    disable_link_preview: Query[Omittable[bool]] = Omitted()
    """Если `false`, сервер не будет генерировать превью для ссылок в тексте сообщения"""
    user_id: Query[Omittable[int]] = Omitted()
    """Если вы хотите отправить сообщение пользователю, укажите его ID"""

    attachments: Body[list[AttachmentsRequests | Attachments] | None] = None
    """Вложения сообщения. Если поле равно `null`, изменений не произойдет. Если пусто, все вложения будут удалены"""
    link: Body[NewMessageLink | None] = None
    """Ссылка на сообщение"""
    text: Body[str | None] = None
    """Новый текст сообщения"""
    format: Body[Omittable[TextFormat | None]] = Omitted()
    """Если установлен, текст сообщения будет форматирован данным способом. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)"""
    notify: Body[Omittable[bool]] = Omitted()
    """Если false, участники чата не будут уведомлены (по умолчанию `true`)"""

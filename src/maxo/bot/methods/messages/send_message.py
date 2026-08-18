from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Query
from maxo.enums.text_format import TextFormat
from maxo.omit import Omittable, Omitted
from maxo.types.attachments import Attachments, AttachmentsRequests
from maxo.types.new_message_link import NewMessageLink
from maxo.types.send_message_result import SendMessageResult


class SendMessage(MaxoMethod[SendMessageResult]):
    """
    Отправка сообщений

    Отправляет сообщение в диалог, групповой чат или канал

    Кроме текста сообщения или посты могут содержать следующие типы вложений:
    - `image` - изображение (JPG, JPEG, PNG, GIF, TIFF, BMP, HEIC)
    - `video` - видео (MP4, MOV, MKV, WEBM, MATROSKA)
    - `audio` - аудио (MP3, WAV, M4A и другие)
    - `file` - файл для загрузки в (TXT, DOC и другие)
    - `sticker` - стикер
    - `contact` - контакт (данные контакта из телефонного справочника)
    - `inline_keyboard` - сообщение или пост с кнопкой
    - `share` - контент, прикрепленный по внешнему URL
    - `location` - локация

    #### Ограничения

    Можно отправлять не более двух сообщений в секунду в один диалог, групповой чат или канал. При превышении этого лимита сообщения следует ставить в очередь или делать задержку перед отправкой

    #### Пример запроса с одной кнопкой-ссылкой

    Больше примеров запросов с кнопками - [в разделе «Клавиатура»](https://dev.max.ru/docs-api#Как%20добавить%20кнопки)
    ```bash
    curl -X POST "https://platform-api2.max.ru/messages?user_id={user_id}" \
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
        attachments: Вложения сообщения. Если поле равно `null`, изменений не произойдет. Если массив пуст, все вложения будут удалены
        chat_id: Если сообщение отправляется в чат или канал, укажите ID этого чата или канала. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        disable_link_preview: Если `true`, сервер не будет генерировать превью для ссылок в тексте сообщения или поста
        format: Если установлен, текст сообщения будет форматирован данным способом. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)
        link: Ссылка на сообщение
        notify: Если `false`, участники чата не получат push-уведомления. Для каналов необходимо отправлять запрос с `notify = true` или без этого поля, т.к. каналы не подразумевают отправку постов без push-уведомлений
        text:
        user_id: Если вы хотите отправить сообщение пользователю, укажите ID этого пользователя

    Источник: https://dev.max.ru/docs-api/methods/POST/messages
    """

    __url__ = "messages"
    __method__ = "post"

    chat_id: Query[Omittable[int]] = Omitted()
    """Если сообщение отправляется в чат или канал, укажите ID этого чата или канала. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    disable_link_preview: Query[Omittable[bool]] = Omitted()
    """Если `true`, сервер не будет генерировать превью для ссылок в тексте сообщения или поста"""
    user_id: Query[Omittable[int]] = Omitted()
    """Если вы хотите отправить сообщение пользователю, укажите ID этого пользователя"""

    attachments: Body[list[AttachmentsRequests | Attachments] | None] = None
    """Вложения сообщения. Если поле равно `null`, изменений не произойдет. Если массив пуст, все вложения будут удалены"""
    link: Body[NewMessageLink | None] = None
    """Ссылка на сообщение"""
    text: Body[str | None] = None
    format: Body[Omittable[TextFormat | None]] = Omitted()
    """Если установлен, текст сообщения будет форматирован данным способом. Для подробной информации загляните в раздел [Форматирование](https://dev.max.ru/docs-api#Форматирование%20текста%20в%20сообщениях)"""
    notify: Body[Omittable[bool]] = Omitted()
    """Если `false`, участники чата не получат push-уведомления. Для каналов необходимо отправлять запрос с `notify = true` или без этого поля, т.к. каналы не подразумевают отправку постов без push-уведомлений"""

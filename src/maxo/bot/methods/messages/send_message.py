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

    Кроме текста сообщения или посты могут содержать вложения следующих типов:
    - `image` - изображение (JPG, JPEG, PNG, GIF, TIFF, BMP, HEIC)
    - `video` - видео (MP4, MOV, MKV, WEBM, MATROSKA)
    - `audio` - аудио (MP3, M4A и другие)
    - `file` - файл (TXT, DOC и другие)
    - `sticker` - стикер
    - `contact` - контакт (данные контакта из телефонного справочника)
    - `inline_keyboard` - сообщение или пост с кнопкой
    - `share` - контент, прикреплённый по внешнему URL
    - `location` - локация

    #### Ограничения

    Можно отправлять не более двух сообщений в секунду в один диалог, групповой чат или канал. При превышении этого лимита сообщения следует ставить в очередь или делать задержку перед отправкой

    #### Пример запроса с одной кнопкой-ссылкой

    Больше примеров запросов с кнопками - [в разделе «Клавиатура»](https://dev.max.ru/docs-api/use-cases/sending-messages/keyboard#Как%20добавить%20кнопки)

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
        attachments: Вложения отправляемого сообщения. Пустое значение означает, что вложений нет
        chat_id: Чтобы отправить сообщение в чат или канал, укажите его ID. Как получить ID - [на странице «Получение ID чата или канала»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)
        disable_link_preview: Если `true`, сервер не будет генерировать превью для ссылок в тексте сообщения или поста
        format: Разметка текста сообщения. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)
        link: Ссылка на сообщение в чате или пост в канале. Ссылки на комментарии к постам в каналах не поддержаны
        notify: Для каналов всегда отправляйте запрос с `notify = true` или без этого поля. Отключить push-уведомления в каналах нельзя
            В групповых чатах и диалогах, если `notify = true` или поле отсутствует, уведомление отобразится пользователю
            При `notify = false` отображение push-уведомлений зависит от платформы:
            - **Десктоп-клиент и веб-приложение на iOS**. В диалогах и групповых чатах при `notify = false` уведомления не отображаются
            - **Приложение на Android**. В диалогах при `notify = false` уведомления не отображаются. В групповых чатах при `notify = false` уведомление не отображаются, только если приложение МАХ свёрнуто или закрыто. Если приложение открыто, пользователь увидит уведомление
            - **Веб-приложение**. Управление отображением уведомлений с помощью параметра `notify` не поддержано
        text: Текст сообщения, до 4000 символов
        user_id: Чтобы отправить сообщение пользователю, укажите его ID

    Источник: https://dev.max.ru/docs-api/methods/POST/messages
    """

    __url__ = "messages"
    __method__ = "post"

    chat_id: Query[Omittable[int]] = Omitted()
    """Чтобы отправить сообщение в чат или канал, укажите его ID. Как получить ID - [на странице «Получение ID чата или канала»](https://dev.max.ru/docs-api/use-cases/getting-chat-id)"""
    disable_link_preview: Query[Omittable[bool]] = Omitted()
    """Если `true`, сервер не будет генерировать превью для ссылок в тексте сообщения или поста"""
    user_id: Query[Omittable[int]] = Omitted()
    """Чтобы отправить сообщение пользователю, укажите его ID"""

    attachments: Body[list[AttachmentsRequests | Attachments] | None] = None
    """Вложения отправляемого сообщения. Пустое значение означает, что вложений нет"""
    link: Body[NewMessageLink | None] = None
    """Ссылка на сообщение в чате или пост в канале. Ссылки на комментарии к постам в каналах не поддержаны"""
    text: Body[str | None] = None
    """Текст сообщения, до 4000 символов"""
    format: Body[Omittable[TextFormat | None]] = Omitted()
    """Разметка текста сообщения. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)"""
    notify: Body[Omittable[bool]] = Omitted()
    """
    Для каналов всегда отправляйте запрос с `notify = true` или без этого поля. Отключить push-уведомления в каналах нельзя

    В групповых чатах и диалогах, если `notify = true` или поле отсутствует, уведомление отобразится пользователю

    При `notify = false` отображение push-уведомлений зависит от платформы:
    - **Десктоп-клиент и веб-приложение на iOS**. В диалогах и групповых чатах при `notify = false` уведомления не отображаются
    - **Приложение на Android**. В диалогах при `notify = false` уведомления не отображаются. В групповых чатах при `notify = false` уведомление не отображаются, только если приложение МАХ свёрнуто или закрыто. Если приложение открыто, пользователь увидит уведомление
    - **Веб-приложение**. Управление отображением уведомлений с помощью параметра `notify` не поддержано
    """

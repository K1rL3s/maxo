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
        - сообщения с кнопками [`inline_keyboard`](https://dev.max.ru/docs-api/use-cases/sending-messages/keyboard#Как%20добавить%20кнопки) редактируются независимо от срока давности
        - остальные сообщения редактируются, если они отправлены менее 7 суток назад
    - В групповых чатах и каналах любые сообщения редактируются независимо от срока давности
    - Можно редактировать не более двух сообщений в секунду в одном диалоге, групповом чате или канале. При превышении этого лимита сообщения следует ставить в очередь или делать задержку перед редактированием

    #### Пример запроса:
    ```bash
    curl -X PUT "https://platform-api2.max.ru/messages?message_id=message_id" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
     -d '{
      "text": "**Новый текст**",
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
      ],
       "link": {
              "type": "reply",
              "mid": "mid.message_id"
        },
       "notify": false,
       "format": "markdown"
       }
     }'
    ```

    Args:
        attachments: Вложения сообщения. Если поле пустое или равно `null`, изменений не произойдёт. Если массив пуст, все вложения будут удалены
        format: Разметка текста сообщения. Подробнее - в разделе [Форматирование](https://dev.max.ru/docs-api/use-cases/sending-messages/text-formatting)
        link: Ссылка на сообщение в чате или пост в канале. Ссылки на комментарии к постам в каналах не поддержаны
        message_id: ID редактируемого сообщения
        notify: Для каналов всегда отправляйте запрос с `notify = true` или без этого поля. Отключить push-уведомления в каналах нельзя
            В групповых чатах и диалогах, если `notify = true` или поле отсутствует, уведомление отобразится пользователю
            При `notify = false` отображение push-уведомлений зависит от платформы:
            - **Десктоп-клиент и веб-приложение на iOS**. В диалогах и групповых чатах при `notify = false` уведомления не отображаются
            - **Приложение на Android**. В диалогах при `notify = false` уведомления не отображаются. В групповых чатах при `notify = false` уведомление не отображаются, только если приложение МАХ свёрнуто или закрыто. Если приложение открыто, пользователь увидит уведомление
            - **Веб-приложение**. Управление отображением уведомлений с помощью параметра `notify` не поддержано
        text: Новый текст сообщения, до 4000 символов. `null` оставляет текст без изменений, пустая строка удаляет его

    Источник: https://dev.max.ru/docs-api/methods/PUT/messages
    """

    __url__ = "messages"
    __method__ = "put"

    message_id: Query[str]
    """ID редактируемого сообщения"""

    attachments: Body[list[AttachmentsRequests | Attachments] | None] = None
    """Вложения сообщения. Если поле пустое или равно `null`, изменений не произойдёт. Если массив пуст, все вложения будут удалены"""
    link: Body[NewMessageLink | None] = None
    """Ссылка на сообщение в чате или пост в канале. Ссылки на комментарии к постам в каналах не поддержаны"""
    text: Body[str | None] = None
    """Новый текст сообщения, до 4000 символов. `null` оставляет текст без изменений, пустая строка удаляет его"""
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

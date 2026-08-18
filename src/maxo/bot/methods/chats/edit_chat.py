from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body, Path
from maxo.omit import Omittable, Omitted
from maxo.types.chat import Chat
from maxo.types.photo_attachment_request_payload import PhotoAttachmentRequestPayload


class EditChat(MaxoMethod[Chat]):
    """
    Изменение информации о групповом чате или канале

    Позволяет редактировать информацию о групповом чате или канале, включая название, иконку и закреплённое сообщение или пост

    Бот, чей токен `access_token` используется для авторизации, должен быть администратором этого чата или канала

    Пример запроса:
    ```bash
    curl -X PATCH "https://platform-api2.max.ru/chats/{chatId}" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
      "icon": { "url": "https://example.com/image.jpg" },
      "title": "Название чата",
      "notify": true
    }'
    ```

    Args:
        chat_id: ID чата или канала
        icon: Данные для прикрепления изображения в качестве аватара чата или канала
        notify: Если `true`, участники получат системное уведомление об изменении
        pin: ID сообщения для закрепления в чате или канале. Чтобы удалить закреплённое сообщение, используйте метод [`DELETE /chats/{chatId}/pin`](https://dev.max.ru/docs-api/methods/DELETE/chats/-chatId-/pin)
        title:

    Источник: https://dev.max.ru/docs-api/methods/PATCH/chats/-chatId-
    """

    __url__ = "chats/{chat_id}"
    __method__ = "patch"

    chat_id: Path[int]
    """ID чата или канала"""

    icon: Body[Omittable[PhotoAttachmentRequestPayload | None]] = Omitted()
    """Данные для прикрепления изображения в качестве аватара чата или канала"""
    notify: Body[Omittable[bool | None]] = Omitted()
    """Если `true`, участники получат системное уведомление об изменении"""
    pin: Body[Omittable[str | None]] = Omitted()
    """ID сообщения для закрепления в чате или канале. Чтобы удалить закреплённое сообщение, используйте метод [`DELETE /chats/{chatId}/pin`](https://dev.max.ru/docs-api/methods/DELETE/chats/-chatId-/pin)"""
    title: Body[Omittable[str | None]] = Omitted()

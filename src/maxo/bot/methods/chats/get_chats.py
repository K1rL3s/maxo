from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Query
from maxo.omit import Omittable, Omitted
from maxo.types.chat_list import ChatList


class GetChats(MaxoMethod[ChatList]):
    """
    Получение списка всех групповых чатов и каналов для бота

    > ! Начиная **с июня 2026** метод `GET /chats` больше не поддерживается, и API не предоставляет готовой возможности для получения списка групповых чатов и каналов, в которые добавлен бот

     Если вам требуется получить для бота такой список, используйте [POST /subscriptions](https://dev.max.ru/docs-api/methods/POST/subscriptions). При этом задача сбора, хранения и поддержки идентификаторов ложится на разработчика: он выбирает способ реализации исходя из своей инфраструктуры и сценария использования

    **Возможный алгоритм действий:**

    1. **Cоздайте подписку** через [POST /subscriptions](https://dev.max.ru/docs-api/methods/POST/subscriptions) и укажите нужные типы событий в параметре `update_types[]`, например, `bot_added` или `bot_started`. Список поддерживаемых типов событий - в объекте [Update](https://dev.max.ru/docs-api/objects/Update)

    2. **Получите `chat_id` в событии** - о том, как это сделать, см. в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)

    3. **Сохраните `chat_id`**:

       - разверните на своей стороне хранилище данных
       - при получении каждого события с `chat_id` - сохраните его, если он ещё не сохранён
       - обработайте возможные дубли (одно и то же событие может прийти повторно)
       - удалите `chat_id` при возникновении соответствующих событий, например, `bot_removed`

    4. **Используйте сохранённый `chat_id` для вызовов API**. После того как `chat_id` окажется в вашем хранилище, вы сможете использовать его во всех методах, где он требуется:

       - [POST `/messages`](https://dev.max.ru/docs-api/methods/POST/messages) - отправить сообщение в чат
       - [GET `/chats/{chat_id}/members`](https://dev.max.ru/docs-api/methods/GET/chats/-chatId-/members) - получить участников группового чата или канала
       - [POST `/chats/{chat_id}/actions`](https://dev.max.ru/docs-api/methods/POST/chats/-chatId-/actions) - отправить действия бота в групповой чат
       - и любые другие методы, принимающие `chat_id` как параметр

     > Использование [Long Polling](https://dev.max.ru/docs-api#Long%C2%A0Polling) для получения списка чатов и каналов для бота не предусмотрено

    Возвращает список групповых чатов и каналов, в которые добавлен бот, информацию о каждом чате и маркер для перехода к следующей странице списка

    Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/chats" \
      -H "Authorization: {access_token}"
    ```

    Args:
        count: Количество запрашиваемых чатов
        marker: Указатель на следующую страницу данных. Для первой страницы передайте `null`

    Источник: https://dev.max.ru/docs-api/methods/GET/chats
    """

    __url__ = "chats"
    __method__ = "get"

    count: Query[Omittable[int]] = Omitted()
    """Количество запрашиваемых чатов"""
    marker: Query[Omittable[int]] = Omitted()
    """Указатель на следующую страницу данных. Для первой страницы передайте `null`"""

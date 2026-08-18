from datetime import datetime

from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Query
from maxo.omit import Omittable, Omitted
from maxo.types.message_list import MessageList


class GetMessages(MaxoMethod[MessageList]):
    """
    Получение информации о сообщениях или постах

    Возвращает информацию о сообщении или массив сообщений из чата или посты из каналов. Для выполнения запроса нужно указать один из параметров - `chat_id` или `message_ids`:
    - `chat_id` - метод возвращает массив сообщений или постов из указанного чата или канала, только если чат-бот в них является администратором. Сообщения возвращаются в обратном порядке: последние сообщения будут первыми в массиве. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
    - `message_ids` - метод возвращает информацию о запрошенных сообщениях или постах. Можно указать один идентификатор или несколько

    #### Пример запроса с использованием `chat_id`:
    ```bash
    curl -X GET "https://platform-api2.max.ru/messages?chat_id={chat_id}" \
      -H "Authorization: {access_token}"
    ```

    #### Пример запроса с использованием `message_ids`:
    ```bash
    curl -X GET "https://platform-api2.max.ru/messages?message_ids={message_id1},{message_id2}" \
      -H "Authorization: {access_token}"
    ```

    Args:
        chat_id: ID чата или канала, чтобы получить из него сообщения или посты. Обязательный параметр, если не указан `message_ids`. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        count: Максимальное количество сообщений или постов в ответе
        from_: Время, до которого будут запрошены все сообщения или посты, начиная с первого опубликованного. Формат времени: Unix timestamp в миллисекундах
        message_ids: Список ID сообщений или постов, которые нужно получить (через запятую). Обязательный параметр, если не указан `chat_id`
        to: Время, начиная с которого будут запрошены все сообщения или посты, - вплоть до последнего опубликованного. Формат времени: Unix timestamp в миллисекундах

    Источник: https://dev.max.ru/docs-api/methods/GET/messages
    """

    __url__ = "messages"
    __method__ = "get"

    chat_id: Query[Omittable[int]] = Omitted()
    """ID чата или канала, чтобы получить из него сообщения или посты. Обязательный параметр, если не указан `message_ids`. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    count: Query[Omittable[int]] = Omitted()
    """Максимальное количество сообщений или постов в ответе"""
    from_: Query[Omittable[datetime]] = Omitted()
    """Время, до которого будут запрошены все сообщения или посты, начиная с первого опубликованного. Формат времени: Unix timestamp в миллисекундах"""
    message_ids: Query[Omittable[list[str] | None]] = Omitted()
    """Список ID сообщений или постов, которые нужно получить (через запятую). Обязательный параметр, если не указан `chat_id`"""
    to: Query[Omittable[datetime]] = Omitted()
    """Время, начиная с которого будут запрошены все сообщения или посты, - вплоть до последнего опубликованного. Формат времени: Unix timestamp в миллисекундах"""

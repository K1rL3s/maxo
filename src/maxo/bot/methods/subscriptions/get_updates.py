from adaptix.load_error import LoadError
from unihttp.http import HTTPResponse
from unihttp.serialize import ResponseLoader

from maxo import loggers
from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Query
from maxo.omit import Omittable, Omitted
from maxo.routing.updates.updates import Updates
from maxo.types.update_list import UpdateList


class GetUpdates(MaxoMethod[UpdateList], slots=False):
    """
    Получение обновлений о событиях через Long Polling

    > ! Получение обновлений с помощью [Long Polling](https://dev.max.ru/docs-api/methods/GET/updates) ограничено по скорости и сроку хранения событий - этот способ не подходит для production-окружения. Рекомендуем на всех этапах работы использовать [Webhook](https://dev.max.ru/docs-api/methods/POST/subscriptions)

    Метод `GET /updates` можно использовать для получения обновлений при разработке и тестировании, если ваш бот не подписан на Webhook. **Для production-окружения используйте только Webhook**

      Каждое обновление со списком событий имеет свой порядковый номер. Свойство `marker` в ответе указывает на следующее ожидаемое обновление. После того, как вы передали `marker` с указателем на конкретное обновление, все предыдущие считаются прочитанными 

     Если параметр `marker` **не передан** или передано значение `null`, вы получите только последнее обновление 

    #### Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/updates" \
      -H "Authorization: {access_token}"
    ```

    Args:
        limit: Максимальное количество обновлений о событиях, которое может вернуться в ответе на запрос
        marker: Чтобы получить последнее обновление событий, передайте `null` или оставьте поле пустым. Чтобы получить все обновления по событиям с момента предыдущего запроса, передайте значение `marker`, которое получили в ответ на предыдущий запрос
        timeout: Тайм-аут в секундах для долгого опроса
        types: Список типов событий, которые вы хотите получать, например: `message_created`, `message_callback`. Полный список возможных событий смотрите в описании [объекта `Update`](https://dev.max.ru/docs-api/objects/Update)

    Источник: https://dev.max.ru/docs-api/methods/GET/updates
    """

    __url__ = "updates"
    __method__ = "get"

    limit: Query[Omittable[int]] = Omitted()
    """Максимальное количество обновлений о событиях, которое может вернуться в ответе на запрос"""
    marker: Query[Omittable[int | None]] = Omitted()
    """Чтобы получить последнее обновление событий, передайте `null` или оставьте поле пустым. Чтобы получить все обновления по событиям с момента предыдущего запроса, передайте значение `marker`, которое получили в ответ на предыдущий запрос"""
    timeout: Query[Omittable[int]] = Omitted()
    """Тайм-аут в секундах для долгого опроса"""
    types: Query[Omittable[list[str] | None]] = Omitted()
    """Список типов событий, которые вы хотите получать, например: `message_created`, `message_callback`. Полный список возможных событий смотрите в описании [объекта `Update`](https://dev.max.ru/docs-api/objects/Update)"""

    def make_response(
        self,
        response: HTTPResponse,
        response_loader: ResponseLoader,
    ) -> UpdateList:
        try:
            return super().make_response(response, response_loader)
        except LoadError:
            raw = response.data
            marker = raw.get("marker")
            updates: list[Updates] = []
            for raw_upd in raw.get("updates", []):
                try:
                    updates.append(response_loader.load(raw_upd, Updates))
                except LoadError:
                    loggers.methods.warning(
                        "Пропуск незагружаемого апдейта. Сообщите об этой ошибке в "
                        "https://github.com/K1rL3s/maxo/issues. Тело апдейта: %s",
                        raw_upd,
                        exc_info=True,
                    )
            return UpdateList(updates=updates, marker=marker)

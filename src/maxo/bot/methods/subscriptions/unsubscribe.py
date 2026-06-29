from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Query
from maxo.types.simple_query_result import SimpleQueryResult


class Unsubscribe(MaxoMethod[SimpleQueryResult]):
    """
    Отписка от обновлений о новых событиях через Webhook

    Отписывает бота от получения обновлений о новых событиях через Webhook. После вызова этого метода бот перестаёт получать уведомления о новых событиях на Webhook-endpoint, и становится доступна доставка уведомлений через Long Polling 

    > !
    > - Для повышения безопасности **с 25 мая** прекращается поддержка получения вебхуков по HTTP, а также самоподписных сертификатов. Рекомендуем заранее перейти на HTTPS и сертификаты от доверенных центров. Чтобы обновить подписку на события, используйте [POST /subscriptions](https://dev.max.ru/docs-api/methods/POST/subscriptions)
    > - Получение обновлений с помощью [Long Polling](https://dev.max.ru/docs-api/methods/GET/updates) ограничено по скорости и сроку хранения событий - этот способ не подходит для production-окружения. Рекомендуем на всех этапах работы использовать [Webhook](https://dev.max.ru/docs-api/methods/POST/subscriptions)

    #### Пример запроса:
    ```bash
    curl -X DELETE "https://platform-api.max.ru/subscriptions?url=https://your-domain.com/webhook" \
      -H "Authorization: {access_token}"
    ```

    Args:
        url: URL, который нужно удалить из подписок на WebHook

    Источник: https://dev.max.ru/docs-api/methods/DELETE/subscriptions
    """

    __url__ = "subscriptions"
    __method__ = "delete"

    url: Query[str]
    """URL, который нужно удалить из подписок на WebHook"""

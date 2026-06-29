from maxo.bot.methods.base import MaxoMethod
from maxo.types.get_subscriptions_result import GetSubscriptionsResult


class GetSubscriptions(MaxoMethod[GetSubscriptionsResult]):
    """
    Получение всех подписок через Webhook

    Если ваш бот получает данные через Webhook, этот метод возвращает список всех подписок 

    > ! 
    > - Для повышения безопасности **с 25 мая** прекращается поддержка получения вебхуков по HTTP, а также самоподписных сертификатов. Рекомендуем заранее перейти на HTTPS и сертификаты от доверенных центров. Чтобы обновить подписку на события, используйте [POST /subscriptions](https://dev.max.ru/docs-api/methods/POST/subscriptions)
    > - Получение обновлений с помощью [Long Polling](https://dev.max.ru/docs-api/methods/GET/updates) ограничено по скорости и сроку хранения событий - этот способ не подходит для production-окружения. Рекомендуем на всех этапах работы использовать [Webhook](https://dev.max.ru/docs-api/methods/POST/subscriptions)

    #### Пример запроса:
    ```bash
    curl -X GET "https://platform-api.max.ru/subscriptions" \
      -H "Authorization: {access_token}"
    ```

    Источник: https://dev.max.ru/docs-api/methods/GET/subscriptions
    """

    __url__ = "subscriptions"
    __method__ = "get"

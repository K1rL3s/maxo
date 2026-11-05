from maxo.types.base import MaxoType
from maxo.types.subscription import Subscription


# Самодельный объект
class ClearSubscriptionsResult(MaxoType):
    """
    Результат очистки WebHook-подписок.

    Args:
        removed: Удалённые подписки
        kept: Подписки, сохранённые по `active_urls`
    """

    removed: list[Subscription]
    """Удалённые подписки"""
    kept: list[Subscription]
    """Подписки, сохранённые по `active_urls`"""

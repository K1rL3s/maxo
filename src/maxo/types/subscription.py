from datetime import datetime

from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.types.base import MaxoType


class Subscription(MaxoType):
    """
    Схема для описания подписки на WebHook

    Args:
        time: Unix-время, когда была создана подписка
        update_types: Типы событий, на которые подписан бот
        url: URL вебхука
    """

    time: datetime
    """Unix-время, когда была создана подписка"""
    url: str
    """URL вебхука"""

    update_types: list[str] | None = None
    """Типы событий, на которые подписан бот"""

    @property
    def unsafe_update_types(self) -> list[str]:
        if is_defined(self.update_types):
            return self.update_types

        raise AttributeIsEmptyError(
            obj=self,
            attr="update_types",
        )

from maxo.enums.update_type import UpdateType
from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxUpdate
from maxo.types.facades.chat import ChatMethodsFacade
from maxo.types.user import User


class BotStarted(MaxUpdate, ChatMethodsFacade):
    """
    Вы получите это событие, как только пользователь начнёт или возобновит общение с ботом: нажмёт соответствующую кнопку в настройках бота в МАКС

    Args:
        chat_id: ID диалога, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)
        payload: Дополнительные данные из диплинков, переданные при запуске бота. Подробнее о диплинках - [в разделе FAQ](https://dev.max.ru/help/deeplinks)
        type:
        user: Пользователь, который запустил бота через интерфейс, например, нажав кнопку `Start`
        user_locale: Текущий язык пользователя в формате [IETF BCP 47](https://www.rfc-editor.org/info/bcp47/)
    """

    type = UpdateType.BOT_STARTED

    chat_id: int
    """ID диалога, где произошло событие. Как получить ID - в [разделе «Получение chat_id»](https://dev.max.ru/docs-api#Получение%20chat_id)"""
    user: User
    """Пользователь, который запустил бота через интерфейс, например, нажав кнопку `Start`"""

    payload: Omittable[str | None] = Omitted()
    """Дополнительные данные из диплинков, переданные при запуске бота. Подробнее о диплинках - [в разделе FAQ](https://dev.max.ru/help/deeplinks)"""
    user_locale: Omittable[str] = Omitted()
    """Текущий язык пользователя в формате [IETF BCP 47](https://www.rfc-editor.org/info/bcp47/)"""

    @property
    def unsafe_payload(self) -> str:
        if is_defined(self.payload):
            return self.payload

        raise AttributeIsEmptyError(
            obj=self,
            attr="payload",
        )

    @property
    def unsafe_user_locale(self) -> str:
        if is_defined(self.user_locale):
            return self.user_locale

        raise AttributeIsEmptyError(
            obj=self,
            attr="user_locale",
        )

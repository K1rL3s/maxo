from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType


class SimpleQueryResult(MaxoType):
    """
    Простой ответ на запрос

    Args:
        message: Сообщение об ошибке
        success: `true`, если запрос был успешным, `false` - в противном случае
    """

    success: bool
    """`true`, если запрос был успешным, `false` - в противном случае"""

    message: Omittable[str] = Omitted()
    """Сообщение об ошибке"""

    @property
    def unsafe_message(self) -> str:
        if is_defined(self.message):
            return self.message

        raise AttributeIsEmptyError(
            obj=self,
            attr="message",
        )

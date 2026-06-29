from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_defined
from maxo.routing.updates.updates import Updates
from maxo.types.base import MaxoType


class UpdateList(MaxoType):
    """
    Список обновлений о событиях в чатах и каналах, в которые добавлен бот. Обратите внимание, чтобы получать события из групповых чатов и каналов, бот должен быть администратором

    Args:
        marker: Указатель на следующую страницу данных
        updates: Список обновлений о событиях в чатах и каналах, в которые добавлен бот. Обратите внимание, чтобы получать события из групповых чатов и каналов, бот должен быть администратором. Подробнее о возможных событиях - [в описании объекта Update](https://dev.max.ru/docs-api/objects/Update)
    """

    updates: list[Updates]
    """Список обновлений о событиях в чатах и каналах, в которые добавлен бот. Обратите внимание, чтобы получать события из групповых чатов и каналов, бот должен быть администратором. Подробнее о возможных событиях - [в описании объекта Update](https://dev.max.ru/docs-api/objects/Update)"""

    marker: int | None = None
    """Указатель на следующую страницу данных"""

    @property
    def unsafe_marker(self) -> int:
        if is_defined(self.marker):
            return self.marker

        raise AttributeIsEmptyError(
            obj=self,
            attr="marker",
        )

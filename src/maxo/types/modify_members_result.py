from maxo.errors import AttributeIsEmptyError
from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.failed_user_details import FailedUserDetails
from maxo.types.simple_query_result import SimpleQueryResult


class ModifyMembersResult(SimpleQueryResult):
    """
    Результат запроса на изменение списка участников

    Args:
        failed_user_details: Подробное описание, почему пользователь не был добавлен в групповой чат или канал
        failed_user_ids: ID пользователей, которых не удалось добавить
    """

    failed_user_details: Omittable[list[FailedUserDetails] | None] = Omitted()
    """Подробное описание, почему пользователь не был добавлен в групповой чат или канал"""
    failed_user_ids: Omittable[list[int] | None] = Omitted()
    """ID пользователей, которых не удалось добавить"""

    @property
    def unsafe_failed_user_details(self) -> list[FailedUserDetails]:
        if is_defined(self.failed_user_details):
            return self.failed_user_details

        raise AttributeIsEmptyError(
            obj=self,
            attr="failed_user_details",
        )

    @property
    def unsafe_failed_user_ids(self) -> list[int]:
        if is_defined(self.failed_user_ids):
            return self.failed_user_ids

        raise AttributeIsEmptyError(
            obj=self,
            attr="failed_user_ids",
        )

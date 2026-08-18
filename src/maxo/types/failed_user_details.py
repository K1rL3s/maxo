from maxo.types.base import MaxoType


class FailedUserDetails(MaxoType):
    """
    Подробное описание, почему пользователь не был добавлен в групповой чат или канал

    Args:
        error_code: Код ошибки
            Возможные значения:
            - `add.participant.privacy` - ошибки конфиденциальности при добавлении пользователей
            - `add.participant.not.found` - пользователи не найдены
        user_ids: ID пользователей с данной ошибкой
    """

    error_code: str
    """
    Код ошибки

    Возможные значения:
        - `add.participant.privacy` - ошибки конфиденциальности при добавлении пользователей
        - `add.participant.not.found` - пользователи не найдены
    """
    user_ids: list[int]
    """ID пользователей с данной ошибкой"""

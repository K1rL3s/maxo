from typing import Generic, TypeVar

from maxo.omit import Omittable, Omitted
from maxo.routing.updates.base import BaseUpdate

_UpdateT = TypeVar("_UpdateT", bound=BaseUpdate)


class MaxoUpdate(BaseUpdate, Generic[_UpdateT]):
    """Внутренний апдейт, используется в роутинге как обёртка над апдейтом из Макса."""

    update: _UpdateT
    marker: Omittable[int | None] = Omitted()

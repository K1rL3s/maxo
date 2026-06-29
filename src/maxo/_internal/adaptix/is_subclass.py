from typing import Any

from adaptix._internal.provider.loc_stack_filtering import OriginSubclassLSC


def is_subclass(class_: type[Any]) -> OriginSubclassLSC:
    return OriginSubclassLSC(class_)

from typing import Any

from adaptix import Chain, Provider, dumper, loader
from adaptix._internal.provider.loc_stack_filtering import Pred
from adaptix.load_error import LoadError

from maxo._internal.adaptix.concat_provider import concat_provider


def _loader_has_tag(pred: Pred, tag: str, value: Any) -> Provider:
    def loader_fn(data: dict[str, Any]) -> Any:
        if data.get(tag) == value:
            return data
        raise LoadError(tag, data.get(tag), value)

    return loader(pred, loader_fn, Chain.FIRST)


def _dumper_has_tag(pred: Pred, tag: str, value: Any) -> Provider:
    def dumper_fn(data: dict[str, Any]) -> Any:
        data[tag] = value
        return data

    return dumper(pred, dumper_fn, Chain.LAST)


def has_tag_provider(pred: Pred, tag: str, value: Any) -> Provider:
    return concat_provider(
        _loader_has_tag(pred, tag, value),
        _dumper_has_tag(pred, tag, value),
    )

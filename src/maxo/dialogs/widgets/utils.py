from collections.abc import Callable, Sequence
from typing import TypeAlias

from maxo.dialogs.api.exceptions import InvalidWidgetType
from maxo.dialogs.api.internal import DataGetter, LinkPreviewWidget, TextWidget

from .data.data_context import CompositeGetter, StaticGetter
from .input import BaseInput, CombinedInput, MessageHandlerFunc, MessageInput
from .kbd import Group, Keyboard
from .link_preview import LinkPreviewBase
from .media import Media, MultiMedia
from .text import Format, Multi as MultiText
from .widget_event import WidgetEventProcessor

WidgetSrc: TypeAlias = (
    str
    | TextWidget
    | Keyboard
    | MessageHandlerFunc
    | Media
    | BaseInput
    | LinkPreviewBase
)

SingleGetterBase: TypeAlias = DataGetter | dict
GetterVariant: TypeAlias = (
    SingleGetterBase | list[SingleGetterBase] | tuple[SingleGetterBase, ...] | None
)


def ensure_text(widget: str | TextWidget | Sequence[TextWidget]) -> TextWidget:
    if isinstance(widget, str):
        return Format(widget)
    if isinstance(widget, Sequence):
        if len(widget) == 1:
            return widget[0]
        return MultiText(*widget)
    return widget


def ensure_keyboard(widget: Keyboard | Sequence[Keyboard]) -> Keyboard:
    if isinstance(widget, Sequence):
        if len(widget) == 1:
            return widget[0]
        return Group(*widget)
    return widget


def ensure_input(
    widget: MessageHandlerFunc | WidgetEventProcessor | BaseInput | Sequence[BaseInput],
) -> BaseInput | None:
    if isinstance(widget, BaseInput):
        return widget
    if isinstance(widget, Sequence):
        if len(widget) == 0:
            return None
        if len(widget) == 1:
            return widget[0]
        return CombinedInput(*widget)
    return MessageInput(widget)


def ensure_media(widget: Media | Sequence[Media]) -> Media:
    if isinstance(widget, Media):
        return widget
    if len(widget) == 1:
        return widget[0]
    if len(widget) > 1:
        return MultiMedia(*widget)
    return Media()


def ensure_link_preview(
    widget: LinkPreviewWidget | Sequence[LinkPreviewWidget],
) -> LinkPreviewWidget | None:
    if isinstance(widget, LinkPreviewWidget):
        return widget
    if len(widget) > 1:
        raise ValueError("Only one link preview widget is supported")
    if len(widget) == 1:
        return widget[0]
    return None


def ensure_widgets(
    widgets: Sequence[WidgetSrc],
) -> tuple[
    TextWidget,
    Keyboard,
    BaseInput | None,
    Media,
    LinkPreviewWidget | None,
]:
    texts = []
    keyboards = []
    inputs = []
    media = []
    link_preview = []

    for w in widgets:
        if isinstance(w, (str, TextWidget)):
            texts.append(ensure_text(w))
        elif isinstance(w, Keyboard):
            keyboards.append(ensure_keyboard(w))
        elif isinstance(w, (BaseInput, Callable)):
            inputs.append(ensure_input(w))
        elif isinstance(w, Media):
            media.append(ensure_media(w))
        elif isinstance(w, LinkPreviewBase):
            link_preview.append(ensure_link_preview(w))
        else:
            raise InvalidWidgetType(
                f"Cannot add widget of type {type(w)}. "
                f"Only str, TextWidget, Keyboard, BaseInput, Media, LinkPreview "
                f"and Callable are supported",
            )
    return (
        ensure_text(texts),
        ensure_keyboard(keyboards),
        ensure_input(inputs),
        ensure_media(media),
        ensure_link_preview(link_preview),
    )


def ensure_data_getter(getter: GetterVariant) -> DataGetter:
    if isinstance(getter, Callable):
        return getter
    if isinstance(getter, dict):
        return StaticGetter(getter)
    if isinstance(getter, (list, tuple)):
        return CompositeGetter(*map(ensure_data_getter, getter))
    if getter is None:
        return StaticGetter({})
    raise InvalidWidgetType(
        f"Cannot add data getter of type {type(getter)}. "
        f"Only Dict, Callable or List of Callables are supported",
    )

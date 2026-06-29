from datetime import date
from typing import Any

from babel.dates import get_day_names, get_month_names
from magic_filter import F

from maxo.dialogs import ChatEvent, Dialog, DialogManager, Window
from maxo.dialogs.api.internal import Widget
from maxo.dialogs.widgets.kbd import (
    Calendar,
    CalendarScope,
    ManagedCalendar,
    SwitchTo,
    TimeSelect,
)
from maxo.dialogs.widgets.kbd.calendar_kbd import (
    DATE_TEXT,
    TODAY_TEXT,
    CalendarDaysView,
    CalendarMonthView,
    CalendarScopeView,
    CalendarYearsView,
)
from maxo.dialogs.widgets.text import Const, Format, Text

from . import states
from .common import MAIN_MENU_BUTTON

SELECTED_DAYS_KEY = "selected_dates"


class WeekDay(Text):
    async def _render_text(self, data: dict[str, Any], manager: DialogManager) -> str:
        selected_date: date = data["date"]
        locale = manager.event.user_locale or None
        return get_day_names(
            width="short",
            context="stand-alone",
            locale=locale,
        )[selected_date.weekday()].title()


class Month(Text):
    async def _render_text(self, data: dict[str, Any], manager: DialogManager) -> str:
        selected_date: date = data["date"]
        locale = manager.event.user_locale or None
        return get_month_names(
            "wide",
            context="stand-alone",
            locale=locale,
        )[selected_date.month].title()


def is_date_selected(
    data: dict[str, Any],
    widget: Widget,
    manager: DialogManager,
) -> bool:
    current_date: date = data["date"]
    serial_date = current_date.isoformat()
    selected = manager.dialog_data.get(SELECTED_DAYS_KEY, [])
    return serial_date in selected


class CustomCalendar(Calendar):
    def _init_views(self) -> dict[CalendarScope, CalendarScopeView]:
        return {
            CalendarScope.DAYS: CalendarDaysView(
                self._item_callback_data,
                date_text=Const("🔴", when=is_date_selected) | DATE_TEXT,
                today_text=Const("⭕", when=is_date_selected) | TODAY_TEXT,
                header_text="~~~~~ " + Month() + " ~~~~~",
                weekday_text=WeekDay(),
                next_month_text=Month() + " >>",
                prev_month_text="<< " + Month(),
            ),
            CalendarScope.MONTHS: CalendarMonthView(
                self._item_callback_data,
                month_text=Month(),
                header_text="~~~~~ " + Format("{date:%Y}") + " ~~~~~",
                this_month_text="[" + Month() + "]",
            ),
            CalendarScope.YEARS: CalendarYearsView(
                self._item_callback_data,
            ),
        }


async def on_date_clicked(
    callback: ChatEvent,
    widget: ManagedCalendar,
    manager: DialogManager,
    selected_date: date,
    /,
) -> None:
    await callback.callback_answer(str(selected_date))


async def on_date_selected(
    callback: ChatEvent,
    widget: ManagedCalendar,
    manager: DialogManager,
    clicked_date: date,
    /,
) -> None:
    selected = manager.dialog_data.setdefault(SELECTED_DAYS_KEY, [])
    serial_date = clicked_date.isoformat()
    if serial_date in selected:
        selected.remove(serial_date)
    else:
        selected.append(serial_date)


async def selection_getter(dialog_manager: DialogManager, **__: Any) -> dict[str, Any]:
    selected = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY, [])
    return {"selected": ", ".join(sorted(selected))}


CALENDAR_MAIN_MENU_BUTTON = SwitchTo(
    text=Const("Back"),
    id="back",
    state=states.Calendar.MAIN,
)
calendar_dialog = Dialog(
    Window(
        Const("Select configuration"),
        SwitchTo(
            Const("Default calendar"),
            id="default",
            state=states.Calendar.DEFAULT,
        ),
        SwitchTo(
            Const("Customized calendar"),
            id="custom",
            state=states.Calendar.CUSTOM,
        ),
        SwitchTo(
            Const("Time selection"),
            id="time",
            state=states.Calendar.TIME,
        ),
        MAIN_MENU_BUTTON,
        state=states.Calendar.MAIN,
    ),
    Window(
        Const("Default calendar widget"),
        Calendar(
            id="cal",
            on_click=on_date_clicked,
        ),
        CALENDAR_MAIN_MENU_BUTTON,
        state=states.Calendar.DEFAULT,
    ),
    Window(
        Const("Customized calendar widget"),
        Const("Here we use custom text widgets to localize and store selection"),
        Format("\nSelected: {selected}", when=F["selected"]),
        Format("\nNo dates selected", when=~F["selected"]),
        CustomCalendar(
            id="cal",
            on_click=on_date_selected,
        ),
        CALENDAR_MAIN_MENU_BUTTON,
        getter=selection_getter,
        state=states.Calendar.CUSTOM,
    ),
    Window(
        Const("TimeSelect widget"),
        TimeSelect("time"),
        CALENDAR_MAIN_MENU_BUTTON,
        state=states.Calendar.TIME,
    ),
)

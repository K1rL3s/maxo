from datetime import UTC, date, timedelta, timezone as dt_timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import Calendar, CalendarScope
from maxo.dialogs.widgets.kbd.calendar_kbd import (
    CALLBACK_NEXT_MONTH,
    CALLBACK_NEXT_YEAR,
    CALLBACK_NEXT_YEARS_PAGE,
    CALLBACK_PREFIX_MONTH,
    CALLBACK_PREFIX_YEAR,
    CALLBACK_PREV_MONTH,
    CALLBACK_PREV_YEAR,
    CALLBACK_PREV_YEARS_PAGE,
    CALLBACK_SCOPE_MONTHS,
    CALLBACK_SCOPE_YEARS,
    CalendarConfig,
    CalendarUserConfig,
    ManagedCalendar,
    _coalesce,
    _local_timezone,
    date_from_raw,
    empty_button,
    get_today,
    month_begin,
    next_month_begin,
    prev_month_begin,
    raw_from_date,
)
from maxo.types import CallbackButton

BOUNDED = CalendarConfig(
    min_date=date(2024, 2, 1),
    max_date=date(2024, 2, 29),
    timezone=UTC,
)


async def render_payloads(calendar: Calendar, manager: DialogManager) -> list[str]:
    keyboard = await calendar.render_keyboard({}, manager)
    return [
        button.payload
        for row in keyboard
        for button in row
        if isinstance(button, CallbackButton)
    ]


class TestHelpers:
    def test_raw_date_roundtrip(self) -> None:
        day = date(2024, 3, 15)

        assert date_from_raw(raw_from_date(day)) == day

    def test_month_begin(self) -> None:
        assert month_begin(date(2024, 3, 15)) == date(2024, 3, 1)

    def test_next_month_begin(self) -> None:
        assert next_month_begin(date(2024, 1, 31)) == date(2024, 2, 1)
        assert next_month_begin(date(2024, 12, 5)) == date(2025, 1, 1)

    def test_prev_month_begin(self) -> None:
        assert prev_month_begin(date(2024, 3, 15)) == date(2024, 2, 1)
        assert prev_month_begin(date(2024, 1, 5)) == date(2023, 12, 1)

    def test_get_today(self) -> None:
        assert isinstance(get_today(UTC), date)

    def test_empty_button(self) -> None:
        button = empty_button()

        assert button.text == button.payload

    def test_coalesce(self) -> None:
        assert _coalesce(None, 5) == 5
        assert _coalesce(1, 5) == 1

    def test_local_timezone_is_fixed_offset(self) -> None:
        assert isinstance(_local_timezone(), dt_timezone)


class TestCalendarConfig:
    def test_merge_takes_user_values(self) -> None:
        merged = CalendarConfig().merge(
            CalendarUserConfig(
                firstweekday=6,
                timezone=UTC,
                min_date=date(2000, 1, 1),
                max_date=date(2001, 1, 1),
                month_columns=4,
                years_per_page=10,
                years_columns=2,
            ),
        )

        assert merged.firstweekday == 6
        assert merged.timezone is UTC
        assert merged.min_date == date(2000, 1, 1)
        assert merged.years_columns == 2

    def test_merge_keeps_defaults_for_none(self) -> None:
        base = CalendarConfig(firstweekday=3)

        merged = base.merge(CalendarUserConfig())

        assert merged.firstweekday == 3
        assert merged.min_date == base.min_date


class TestScopeAndOffset:
    def test_default_scope_is_days(self, mock_manager: DialogManager) -> None:
        assert Calendar(id="cal").get_scope(mock_manager) is CalendarScope.DAYS

    def test_unknown_scope_falls_back_to_days(
        self,
        mock_manager: DialogManager,
    ) -> None:
        calendar = Calendar(id="cal")
        data: dict[str, Any] = calendar.get_widget_data(mock_manager, {})
        data["current_scope"] = "NOPE"

        assert calendar.get_scope(mock_manager) is CalendarScope.DAYS

    def test_set_and_get_scope(self, mock_manager: DialogManager) -> None:
        calendar = Calendar(id="cal")
        calendar.set_scope(CalendarScope.YEARS, mock_manager)

        assert calendar.get_scope(mock_manager) is CalendarScope.YEARS

    def test_offset_is_none_by_default(self, mock_manager: DialogManager) -> None:
        assert Calendar(id="cal").get_offset(mock_manager) is None

    def test_set_and_get_offset(self, mock_manager: DialogManager) -> None:
        calendar = Calendar(id="cal")
        calendar.set_offset(date(2024, 5, 1), mock_manager)

        assert calendar.get_offset(mock_manager) == date(2024, 5, 1)

    def test_require_offset_defaults_to_today(
        self,
        mock_manager: DialogManager,
    ) -> None:
        calendar = Calendar(id="cal", config=CalendarConfig(timezone=UTC))

        assert calendar._require_offset(mock_manager) == get_today(UTC)


class TestCallbackHandlers:
    @pytest.fixture
    def calendar(self, mock_manager: DialogManager) -> Calendar:
        calendar = Calendar(id="cal", config=CalendarConfig(timezone=UTC))
        calendar.set_offset(date(2024, 6, 15), mock_manager)
        return calendar

    async def process(
        self,
        calendar: Calendar,
        data: str,
        manager: DialogManager,
    ) -> None:
        assert (
            await calendar._process_item_callback(
                MagicMock(),
                data,
                MagicMock(),
                manager,
            )
            is True
        )

    async def test_next_month(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, CALLBACK_NEXT_MONTH, mock_manager)

        assert calendar.get_offset(mock_manager) == date(2024, 7, 1)

    async def test_prev_month(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, CALLBACK_PREV_MONTH, mock_manager)

        assert calendar.get_offset(mock_manager) == date(2024, 5, 1)

    async def test_next_year(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, CALLBACK_NEXT_YEAR, mock_manager)

        assert calendar.get_offset(mock_manager) == date(2025, 6, 15)

    async def test_prev_year(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, CALLBACK_PREV_YEAR, mock_manager)

        assert calendar.get_offset(mock_manager) == date(2023, 6, 15)

    async def test_next_years_page(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, CALLBACK_NEXT_YEARS_PAGE, mock_manager)

        offset = calendar.get_offset(mock_manager)
        assert offset is not None
        assert offset.year == 2024 + calendar.config.years_per_page

    async def test_prev_years_page(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, CALLBACK_PREV_YEARS_PAGE, mock_manager)

        offset = calendar.get_offset(mock_manager)
        assert offset is not None
        assert offset.year == 2024 - calendar.config.years_per_page

    async def test_scope_months(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, CALLBACK_SCOPE_MONTHS, mock_manager)

        assert calendar.get_scope(mock_manager) is CalendarScope.MONTHS

    async def test_scope_years(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, CALLBACK_SCOPE_YEARS, mock_manager)

        assert calendar.get_scope(mock_manager) is CalendarScope.YEARS

    async def test_click_month_switches_to_days(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, f"{CALLBACK_PREFIX_MONTH}3", mock_manager)

        assert calendar.get_offset(mock_manager) == date(2024, 3, 1)
        assert calendar.get_scope(mock_manager) is CalendarScope.DAYS

    async def test_click_year_switches_to_months(
        self,
        calendar: Calendar,
        mock_manager: DialogManager,
    ) -> None:
        await self.process(calendar, f"{CALLBACK_PREFIX_YEAR}2030", mock_manager)

        assert calendar.get_offset(mock_manager) == date(2030, 1, 1)
        assert calendar.get_scope(mock_manager) is CalendarScope.MONTHS

    async def test_click_date_calls_on_click(
        self,
        mock_manager: DialogManager,
    ) -> None:
        on_click = AsyncMock()
        calendar = Calendar(id="cal", on_click=on_click)
        selected = date(2024, 6, 15)

        await self.process(calendar, str(raw_from_date(selected)), mock_manager)

        on_click.assert_awaited_once()
        assert on_click.call_args.args[-1] == selected

    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (CALLBACK_PREV_YEAR, date(2023, 2, 28)),
            (CALLBACK_NEXT_YEAR, date(2025, 2, 28)),
            (CALLBACK_PREV_YEARS_PAGE, date(2021, 2, 28)),
            (CALLBACK_NEXT_YEARS_PAGE, date(2027, 2, 28)),
        ],
    )
    async def test_year_shift_from_leap_day(
        self,
        mock_manager: DialogManager,
        data: str,
        expected: date,
    ) -> None:
        calendar = Calendar(
            id="cal",
            config=CalendarConfig(timezone=UTC, years_per_page=3),
        )
        calendar.set_offset(date(2024, 2, 29), mock_manager)

        await self.process(calendar, data, mock_manager)

        assert calendar.get_offset(mock_manager) == expected


class TestRenderingBounds:
    async def test_render_all_scopes(self, mock_manager: DialogManager) -> None:
        calendar = Calendar(id="cal", config=BOUNDED)
        calendar.set_offset(date(2024, 2, 10), mock_manager)

        for scope in CalendarScope:
            calendar.set_scope(scope, mock_manager)
            assert await calendar.render_keyboard({}, mock_manager)

    async def test_days_header_dropped_when_no_navigation_possible(
        self,
        mock_manager: DialogManager,
    ) -> None:
        calendar = Calendar(id="cal", config=BOUNDED)
        calendar.set_offset(date(2024, 2, 10), mock_manager)

        payloads = await render_payloads(calendar, mock_manager)

        # min_date и max_date внутри одного месяца - стрелки листания не рисуются
        assert calendar._item_payload(CALLBACK_PREV_MONTH) not in payloads
        assert calendar._item_payload(CALLBACK_NEXT_MONTH) not in payloads

    async def test_days_header_replaces_unavailable_arrow_with_stub(
        self,
        mock_manager: DialogManager,
    ) -> None:
        config = CalendarConfig(
            min_date=date(2024, 2, 1),
            max_date=date(2024, 12, 31),
            timezone=UTC,
        )
        calendar = Calendar(id="cal", config=config)
        calendar.set_offset(date(2024, 2, 10), mock_manager)

        payloads = await render_payloads(calendar, mock_manager)

        assert empty_button().payload in payloads  # назад нельзя
        assert calendar._item_payload(CALLBACK_NEXT_MONTH) in payloads

    async def test_years_scope_outside_range(
        self,
        mock_manager: DialogManager,
    ) -> None:
        calendar = Calendar(id="cal", config=BOUNDED)
        calendar.set_scope(CalendarScope.YEARS, mock_manager)
        calendar.set_offset(date(2024, 2, 10), mock_manager)

        payloads = await render_payloads(calendar, mock_manager)

        assert calendar._item_payload(CALLBACK_PREV_YEARS_PAGE) not in payloads
        assert calendar._item_payload(CALLBACK_NEXT_YEARS_PAGE) not in payloads


class TestManagedCalendar:
    def test_delegates_to_widget(self, mock_manager: DialogManager) -> None:
        calendar = Calendar(id="cal")
        managed: ManagedCalendar = calendar.managed(mock_manager)

        assert managed.get_scope() is CalendarScope.DAYS
        assert managed.get_offset() is None

        managed.set_offset(date(2024, 4, 1))
        managed.set_scope(CalendarScope.MONTHS)

        assert managed.get_offset() == date(2024, 4, 1)
        assert managed.get_scope() is CalendarScope.MONTHS


def test_date_from_raw_handles_negative() -> None:
    assert date_from_raw(-int(timedelta(days=1).total_seconds())) == date(1969, 12, 31)

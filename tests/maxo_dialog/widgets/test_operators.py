from unittest.mock import MagicMock

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.kbd import Button, Row
from maxo.dialogs.widgets.kbd.base import Or as KbdOr
from maxo.dialogs.widgets.media import MultiMedia, StaticMedia
from maxo.dialogs.widgets.media.base import Media, Or as MediaOr
from maxo.dialogs.widgets.text import Const, Multi
from maxo.dialogs.widgets.text.base import Or as TextOr


class TestTextAdd:
    async def test_add_str(self, mock_manager: DialogManager) -> None:
        multi = Const("a") + "b"

        assert isinstance(multi, Multi)
        assert await multi.render_text({}, mock_manager) == "ab"

    async def test_radd_str(self, mock_manager: DialogManager) -> None:
        multi = "a" + Const("b")

        assert await multi.render_text({}, mock_manager) == "ab"

    async def test_add_text(self, mock_manager: DialogManager) -> None:
        multi = Const("a") + Const("b")

        assert await multi.render_text({}, mock_manager) == "ab"

    def test_add_multi_is_not_implemented(self) -> None:
        assert Const.__add__(Const("a"), Multi(Const("b"))) is NotImplemented

    async def test_multi_iadd(self, mock_manager: DialogManager) -> None:
        multi = Multi(Const("a"), sep="")
        multi += "b"

        assert await multi.render_text({}, mock_manager) == "ab"

    async def test_multi_add_flattens(self, mock_manager: DialogManager) -> None:
        multi = Multi(Const("a"), Const("b"), sep="") + "c"

        assert len(multi.texts) == 3
        assert await multi.render_text({}, mock_manager) == "abc"

    async def test_multi_radd_flattens(self, mock_manager: DialogManager) -> None:
        multi = "c" + Multi(Const("a"), Const("b"), sep="")

        assert len(multi.texts) == 3
        assert await multi.render_text({}, mock_manager) == "cab"

    async def test_multi_add_with_separator_nests(
        self,
        mock_manager: DialogManager,
    ) -> None:
        multi = Multi(Const("a"), Const("b"), sep="-") + "c"

        assert len(multi.texts) == 2
        assert await multi.render_text({}, mock_manager) == "a-bc"

    async def test_multi_radd_with_separator_nests(
        self,
        mock_manager: DialogManager,
    ) -> None:
        multi = "c" + Multi(Const("a"), Const("b"), sep="-")

        # Внутренний Multi со своим `sep` не разворачивается в внешний.
        assert len(multi.texts) == 2
        assert await multi.render_text({}, mock_manager) == "ca-b"

    def test_multi_find(self) -> None:
        assert Multi(Const("a")).find("nope") is None


class TestTextOr:
    async def test_or_picks_first_non_empty(
        self,
        mock_manager: DialogManager,
    ) -> None:
        text = Const("") | Const("b")

        assert isinstance(text, TextOr)
        assert await text.render_text({}, mock_manager) == "b"

    async def test_or_with_str(self, mock_manager: DialogManager) -> None:
        assert await (Const("") | "b").render_text({}, mock_manager) == "b"

    async def test_ror_with_str(self, mock_manager: DialogManager) -> None:
        assert await ("a" | Const("b")).render_text({}, mock_manager) == "a"

    def test_or_with_or_is_not_implemented(self) -> None:
        assert Const.__or__(Const("a"), TextOr(Const("b"))) is NotImplemented

    async def test_or_returns_empty_when_all_empty(
        self,
        mock_manager: DialogManager,
    ) -> None:
        assert await (Const("") | Const("")).render_text({}, mock_manager) == ""

    async def test_or_ior_extends(self, mock_manager: DialogManager) -> None:
        text = TextOr(Const(""))
        text |= "b"

        assert await text.render_text({}, mock_manager) == "b"

    def test_or_or_flattens(self) -> None:
        text = TextOr(Const("a"), Const("b")) | "c"

        assert len(text.texts) == 3

    def test_or_ror_flattens(self) -> None:
        text = "c" | TextOr(Const("a"), Const("b"))

        assert len(text.texts) == 3

    def test_or_find(self) -> None:
        assert TextOr(Const("a")).find("nope") is None


class TestKeyboardOr:
    async def test_or_picks_first_non_empty(
        self,
        mock_manager: DialogManager,
    ) -> None:
        empty = Row()
        button = Button(Const("b"), id="btn")

        keyboard = empty | button

        assert isinstance(keyboard, KbdOr)
        rendered = await keyboard.render_keyboard({}, mock_manager)
        assert rendered[0][0].text == "b"

    async def test_or_returns_empty_when_all_empty(
        self,
        mock_manager: DialogManager,
    ) -> None:
        keyboard = KbdOr(Row(), Row())

        assert await keyboard.render_keyboard({}, mock_manager) == []

    def test_or_with_or_is_not_implemented(self) -> None:
        button = Button(Const("b"), id="btn")

        assert button.__or__(KbdOr(button)) is NotImplemented

    def test_ror(self) -> None:
        button = Button(Const("b"), id="btn")

        assert isinstance(Button.__ror__(button, Row()), KbdOr)

    def test_or_ior_extends(self) -> None:
        keyboard = KbdOr(Row())
        keyboard |= Button(Const("b"), id="btn")

        assert len(keyboard.widgets) == 2

    def test_or_or_flattens(self) -> None:
        keyboard = KbdOr(Row(), Row()) | Button(Const("b"), id="btn")

        assert len(keyboard.widgets) == 3

    def test_or_ror_flattens(self) -> None:
        keyboard = KbdOr.__ror__(KbdOr(Row(), Row()), Button(Const("b"), id="btn"))

        assert len(keyboard.widgets) == 3

    def test_find_inside_or(self) -> None:
        button = Button(Const("b"), id="btn")
        keyboard = KbdOr(button)

        assert keyboard.find("btn") is button
        assert keyboard.find("missing") is None

    async def test_process_other_callback_delegates(
        self,
        mock_manager: DialogManager,
    ) -> None:
        button = Button(Const("b"), id="btn")
        keyboard = KbdOr(button)
        callback = MagicMock(payload="btn")

        assert (
            await keyboard._process_other_callback(
                callback,
                MagicMock(),
                mock_manager,
            )
            is True
        )

    async def test_process_other_callback_without_match(
        self,
        mock_manager: DialogManager,
    ) -> None:
        keyboard = KbdOr(Button(Const("b"), id="btn"))
        callback = MagicMock(payload="nope")

        assert (
            await keyboard._process_other_callback(
                callback,
                MagicMock(),
                mock_manager,
            )
            is False
        )


class TestMediaOperators:
    def test_add_media(self) -> None:
        media = StaticMedia(url="a") + StaticMedia(url="b")

        assert isinstance(media, MultiMedia)
        assert len(media.media) == 2

    def test_add_multi_is_not_implemented(self) -> None:
        one = StaticMedia(url="a")

        assert Media.__add__(one, MultiMedia(one)) is NotImplemented

    def test_radd(self) -> None:
        media = Media.__radd__(StaticMedia(url="a"), StaticMedia(url="b"))

        assert isinstance(media, MultiMedia)

    def test_multi_add_flattens(self) -> None:
        media = MultiMedia(StaticMedia(url="a"), StaticMedia(url="b")) + StaticMedia(
            url="c",
        )

        assert len(media.media) == 3

    def test_multi_radd_flattens(self) -> None:
        media = MultiMedia.__radd__(
            MultiMedia(StaticMedia(url="a")),
            StaticMedia(url="b"),
        )

        assert len(media.media) == 2

    def test_or(self) -> None:
        media = StaticMedia(url="a") | StaticMedia(url="b")

        assert isinstance(media, MediaOr)

    def test_ror(self) -> None:
        media = Media.__ror__(StaticMedia(url="a"), StaticMedia(url="b"))

        assert isinstance(media, MediaOr)

    def test_multi_find(self) -> None:
        assert MultiMedia(StaticMedia(url="a")).find("nope") is None

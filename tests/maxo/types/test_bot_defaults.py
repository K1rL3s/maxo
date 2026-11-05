import pytest

from maxo.bot.defaults import BotDefaults
from maxo.errors import AttributeIsEmptyError
from maxo.omit import is_omitted


def test_bot_defaults() -> None:
    defaults = BotDefaults()
    assert defaults.text_format is None
    assert is_omitted(defaults.disable_link_preview)


def test_bot_defaults_without_bot_raises_attribute_is_empty() -> None:
    with pytest.raises(AttributeIsEmptyError):
        _ = BotDefaults().bot

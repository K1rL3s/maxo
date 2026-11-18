from maxo.bot.defaults import BotDefaults
from maxo.omit import is_omitted


def test_bot_defaults() -> None:
    defaults = BotDefaults()
    assert defaults.text_format is None
    assert is_omitted(defaults.disable_link_preview)

import pytest

from maxo.bot.bot import Bot
from tests.factories import make_bot


@pytest.fixture
def bot() -> Bot:
    return make_bot()

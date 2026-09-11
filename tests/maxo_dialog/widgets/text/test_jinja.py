import pytest
from jinja2 import Environment

from maxo import Dispatcher
from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Jinja, setup_jinja
from maxo.dialogs.widgets.text.jinja import JINJA_ENV_FIELD, StubLoader
from tests.factories import make_bot


@pytest.fixture
def mock_manager(mock_manager: DialogManager) -> DialogManager:
    mock_manager.middleware_data = {}  # type: ignore[misc]
    return mock_manager


async def test_render_jinja(mock_manager: DialogManager) -> None:
    jinja = Jinja(
        """
<b>{{title}}</b>
{% for animal in animals %}
* <a href="https://yandex.ru/search/?text={{ animal }}">{{ animal|capitalize }}</a>
{% endfor %}
""",
    )

    data = {
        "title": "Animals list",
        "animals": ["cat", "dog", "my brother's tortoise"],
    }

    rendered_text = await jinja.render_text(
        data=data,
        manager=mock_manager,
    )

    expected = """
<b>Animals list</b>
* <a href="https://yandex.ru/search/?text=cat">Cat</a>
* <a href="https://yandex.ru/search/?text=dog">Dog</a>
* <a href="https://yandex.ru/search/?text=my brother&#39;s tortoise">\
My brother&#39;s tortoise</a>
"""
    assert rendered_text == expected


async def test_render_jinja_from_bot_middleware_data(
    mock_manager: DialogManager,
) -> None:
    env = Environment(loader=StubLoader(), autoescape=True)
    bot = type("BotWithJinja", (), {JINJA_ENV_FIELD: env})()
    mock_manager.middleware_data = {"bot": bot}  # type: ignore[misc]
    jinja = Jinja("Hello, {{ name }}!")

    assert await jinja.render_text({"name": "Alice"}, mock_manager) == "Hello, Alice!"


async def test_render_jinja_async_environment(mock_manager: DialogManager) -> None:
    env = Environment(loader=StubLoader(), autoescape=True, enable_async=True)
    mock_manager.middleware_data = {JINJA_ENV_FIELD: env}  # type: ignore[misc]
    jinja = Jinja("Hello, {{ name }}!")

    assert await jinja.render_text({"name": "Alice"}, mock_manager) == "Hello, Alice!"


def test_setup_jinja_for_dispatcher_with_filters() -> None:
    dp = Dispatcher()

    env = setup_jinja(dp, filters={"shout": lambda value: value.upper()})

    assert dp.workflow_data[JINJA_ENV_FIELD] is env
    assert env.from_string("{{ 'ok'|shout }}").render() == "OK"


def test_setup_jinja_for_bot_is_deprecated() -> None:
    bot = make_bot()

    with pytest.warns(DeprecationWarning, match="Passing `Bot` to setup_jinja"):
        env = setup_jinja(bot)

    assert getattr(bot, JINJA_ENV_FIELD) is env

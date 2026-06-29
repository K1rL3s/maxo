import pytest

from maxo.dialogs import DialogManager
from maxo.dialogs.widgets.text import Jinja


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

    assert (
        rendered_text
        == """
<b>Animals list</b>
* <a href="https://yandex.ru/search/?text=cat">Cat</a>
* <a href="https://yandex.ru/search/?text=dog">Dog</a>
* <a href="https://yandex.ru/search/?text=my brother&#39;s tortoise">\
My brother&#39;s tortoise</a>
"""
    )

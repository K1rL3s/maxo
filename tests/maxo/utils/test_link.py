from maxo.utils.link import create_max_http_link, create_max_link


def test_create_max_link() -> None:
    assert create_max_link("somepage") == "max://somepage"


def test_create_max_link_with_query() -> None:
    assert create_max_link("somepage", foo="bar") == "max://somepage?foo=bar"


def test_create_max_link_with_fragment() -> None:
    assert create_max_link("somepage", fragment_="frag") == "max://somepage#frag"


def test_create_max_link_with_query_and_fragment() -> None:
    link = create_max_link("somepage", fragment_="frag", foo="bar")
    assert link == "max://somepage?foo=bar#frag"


def test_create_max_http_link_with_fragment() -> None:
    link = create_max_http_link("somepage", fragment_="frag")
    assert link == "https://max.ru/somepage#frag"


def test_create_max_http_link_with_query_and_fragment() -> None:
    link = create_max_http_link("somepage", fragment_="frag", foo="bar")
    assert link == "https://max.ru/somepage?foo=bar#frag"

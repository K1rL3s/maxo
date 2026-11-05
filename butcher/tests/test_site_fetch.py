import json
from pathlib import Path

import pytest

from butcher.site_spec import fetch
from butcher.site_spec.fetch import fetch_pages, http_get, page_key, page_paths
from butcher.site_spec.pages import SiteFormatError

INDEX = [
    {"permalink": "https://dev.max.ru/docs-api/methods/GET/me/"},
    {"permalink": "https://dev.max.ru/docs-api/objects/User/"},
    {"permalink": "https://dev.max.ru/docs-api/objects/User/"},
    {"permalink": "https://dev.max.ru/docs-api/use-cases/webhooks/"},
    {"permalink": "https://dev.max.ru/docs/chatbots/"},
    {"title": "без ссылки"},
    "мусор",
]


def test_page_paths():
    assert page_paths(INDEX, min_pages=2) == [
        "/docs-api/methods/GET/me/",
        "/docs-api/objects/User/",
    ]


def test_page_paths_too_few():
    with pytest.raises(SiteFormatError, match="ожидалось не меньше 40"):
        page_paths(INDEX)


def test_page_paths_not_a_list():
    with pytest.raises(SiteFormatError):
        page_paths({"pages": []}, min_pages=0)


def test_page_key():
    assert page_key("/docs-api/methods/GET/chats/-chatId-/members/") == (
        "methods__GET__chats__-chatId-__members"
    )
    with pytest.raises(SiteFormatError):
        page_key("/docs-api/methods/GET/../../etc/")


def test_http_get_rejects_other_hosts():
    with pytest.raises(ValueError, match="Недоверенный URL"):
        http_get("https://example.com/index.json")
    with pytest.raises(ValueError, match="Недоверенный URL"):
        http_get("http://dev.max.ru/index.json")


def test_fetch_pages_replaces_stale_pages(tmp_path: Path, monkeypatch):
    pages = {
        "https://dev.max.ru/index.json": json.dumps(INDEX).encode(),
        "https://dev.max.ru/docs-api/methods/GET/me/": b"<main>me</main>",
        "https://dev.max.ru/docs-api/objects/User/": b"<main>user</main>",
    }
    monkeypatch.setattr(fetch, "http_get", pages.__getitem__)
    (tmp_path / "objects__Gone.html").write_text("old")

    assert fetch_pages(tmp_path, delay=0, min_pages=2) == 2

    assert sorted(path.name for path in tmp_path.iterdir()) == [
        "methods__GET__me.html",
        "objects__User.html",
    ]
    assert (tmp_path / "objects__User.html").read_bytes() == b"<main>user</main>"


def test_fetch_pages_keeps_old_pages_on_failure(tmp_path: Path, monkeypatch):
    def broken(url: str) -> bytes:
        if url.endswith("index.json"):
            return json.dumps(INDEX).encode()
        raise OSError("сеть упала")

    monkeypatch.setattr(fetch, "http_get", broken)
    (tmp_path / "objects__User.html").write_text("old")

    with pytest.raises(OSError, match="сеть упала"):
        fetch_pages(tmp_path, delay=0, min_pages=2)

    assert (tmp_path / "objects__User.html").read_text() == "old"

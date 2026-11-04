import json
import re
import time
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from butcher.site_spec.pages import MIN_PAGES, SiteFormatError

SITE_URL = "https://dev.max.ru"
SITE_HOST = "dev.max.ru"
INDEX_URL = f"{SITE_URL}/index.json"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36"
)
PAGE_PATH_RE = re.compile(r"^/docs-api/(?:methods/[A-Z]+/.+|objects/[^/]+)/$")
PAGE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")
REQUEST_TIMEOUT = 60
REQUEST_DELAY = 1.0


def http_get(url: str) -> bytes:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != SITE_HOST:
        raise ValueError(f"Недоверенный URL: {url}")
    request = Request(url, headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urlopen(request, timeout=REQUEST_TIMEOUT) as response:  # noqa: S310
        return bytes(response.read())


def page_paths(index: object, min_pages: int = MIN_PAGES) -> list[str]:
    if not isinstance(index, list):
        raise SiteFormatError("index.json не список страниц")
    paths = {
        urlsplit(item["permalink"]).path
        for item in index
        if isinstance(item, dict) and isinstance(item.get("permalink"), str)
    }
    pages = sorted(path for path in paths if PAGE_PATH_RE.match(path))
    if len(pages) < min_pages:
        raise SiteFormatError(
            f"В index.json {len(pages)} страниц методов и объектов, "
            f"ожидалось не меньше {min_pages}",
        )
    return pages


def page_key(path: str) -> str:
    key = path.strip("/").removeprefix("docs-api/").replace("/", "__")
    if not PAGE_KEY_RE.match(key):
        raise SiteFormatError(f"Неожиданный путь страницы: {path}")
    return key


def fetch_pages(
    pages_dir: Path,
    delay: float = REQUEST_DELAY,
    min_pages: int = MIN_PAGES,
) -> int:
    paths = page_paths(json.loads(http_get(INDEX_URL)), min_pages)
    downloaded: dict[str, bytes] = {}
    for path in paths:
        time.sleep(delay)
        downloaded[page_key(path)] = http_get(SITE_URL + path)
    pages_dir.mkdir(parents=True, exist_ok=True)
    for stale in pages_dir.glob("*.html"):
        stale.unlink()
    for key, content in downloaded.items():
        (pages_dir / f"{key}.html").write_bytes(content)
    return len(downloaded)

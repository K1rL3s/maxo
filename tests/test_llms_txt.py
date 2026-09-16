"""Guard that docs/_extra/llms.txt lists every page from the Sphinx toctrees."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
LLMS_TXT = DOCS / "_extra" / "llms.txt"
INDEX_RST = DOCS / "index.rst"
BOTAPI_INDEX = DOCS / "pages" / "botapi" / "index.rst"
DOCS_BASE = "https://maxo.readthedocs.io/ru/latest/"


def _toctree_entries(rst_path: Path) -> list[str]:
    entries: list[str] = []
    in_toctree = False
    for raw in rst_path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if stripped.startswith(".. toctree::"):
            in_toctree = True
            continue
        if in_toctree:
            if not stripped:
                if entries:
                    in_toctree = False
                continue
            if stripped.startswith(":"):
                continue
            if stripped.startswith(".."):
                in_toctree = False
                continue
            entries.append(stripped)
    return entries


def _doc_url(entry: str, *, relative_to: Path) -> str:
    page = (relative_to / entry).resolve().relative_to(DOCS).as_posix()
    return f"{DOCS_BASE}{page}.html"


def test_llms_txt_covers_root_and_botapi_toctrees() -> None:
    llms = LLMS_TXT.read_text(encoding="utf-8")
    expected = [_doc_url(entry, relative_to=DOCS) for entry in _toctree_entries(INDEX_RST)]
    expected.extend(
        _doc_url(entry, relative_to=BOTAPI_INDEX.parent)
        for entry in _toctree_entries(BOTAPI_INDEX)
    )

    missing = [url for url in expected if url not in llms]
    assert not missing, "llms.txt is missing documentation pages:\n" + "\n".join(missing)

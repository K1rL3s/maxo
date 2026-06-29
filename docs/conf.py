import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from typing import cast

# We need `maxo` to be importable from here:
_ROOT = Path("..").resolve(strict=True)
sys.path.insert(0, str(_ROOT))


# ----- Project Information -----

def _get_project_meta() -> dict[str, str]:
    pyproject = _ROOT / "pyproject.toml"
    return cast(
        dict[str, str],
        tomllib.loads(pyproject.read_text())["project"],
    )


pkg_meta = _get_project_meta()
project = str(pkg_meta["name"])

copyright = "2026, Kirill Lesovoy"
author = "Kirill Lesovoy"
version = str(pkg_meta["version"])
release = version

# ----- General configuration -----

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    # https://github.com/executablebooks/MyST-Parser
    "myst_parser",
    # 3rd party, order matters:
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx_contributors",
    "sphinx_tabs.tabs",
    "sphinx_iconify",
    "sphinxcontrib.mermaid",
    "sphinx_sitemap",
    "sphinxext.opengraph",
]

# ----- SEO / canonical / sitemap / Open Graph -----

html_baseurl = "https://maxo.readthedocs.io/ru/latest/"
sitemap_url_scheme = "{link}"
sitemap_excludes = [
    "search.html",
    "genindex.html",
    "py-modindex.html",
    "_modules/index.html",
]


def _strip_modules_from_sitemap(app, exception):
    """Пост-фильтр: удаляет все ``_modules/*`` URL из ``sitemap.xml``."""
    if exception is not None:
        return
    sitemap_path = Path(app.outdir) / "sitemap.xml"
    if not sitemap_path.exists():
        return
    text = sitemap_path.read_text(encoding="utf-8")
    text = re.sub(
        r"<url><loc>[^<]*?/_modules/[^<]*?</loc></url>",
        "",
        text,
    )
    sitemap_path.write_text(text, encoding="utf-8")

ogp_site_url = "https://maxo.readthedocs.io/ru/latest/"
ogp_site_name = "maxo"
ogp_image = "https://raw.githubusercontent.com/K1rL3s/maxo/master/docs/_static/maxo-logo.png"
ogp_type = "website"
ogp_enable_meta_description = True
ogp_social_cards = {"enable": False}
ogp_custom_meta_tags = [
    '<meta name="twitter:card" content="summary_large_image" />',
    '<meta name="twitter:title" content="maxo - асинхронный Python-фреймворк для ботов MAX (max.ru)" />',
    '<meta name="twitter:description" content="Асинхронный Python-фреймворк для ботов мессенджера MAX (max.ru): long-polling, вебхуки, FSM, диалоги, фильтры, DI." />',
    '<meta name="twitter:image" content="https://raw.githubusercontent.com/K1rL3s/maxo/master/docs/_static/maxo-logo.png" />',
]

rst_prolog = """
.. meta::
   :description: maxo - асинхронный Python-фреймворк для ботов мессенджера MAX (max.ru): long-polling, вебхуки, FSM, диалоги, фильтры, DI.
   :keywords: maxo, max.ru, max messenger, бот max, python фреймворк, asyncio, aiohttp, fsm, диалоги, long-polling, webhook
"""

# Napoleon:
napoleon_google_docstring = True
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_attr_annotations = True
napoleon_use_param = True
napoleon_use_ivar = True

# Autodoc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_class_signature = "separated"
autodoc_default_options = {
    "undoc-members": True,
    "exclude-members": "__init__",
}


def setup(app):
    app.connect("autodoc-process-docstring", fix_docstring, priority=400)
    app.connect("build-finished", _strip_modules_from_sitemap)
    app.connect("builder-inited", _refresh_changelog_from_github)


def fix_docstring(app, what, name, obj, options, lines):
    """Исправляет Markdown, убирает дублирование и экранирует спецсимволы Sphinx."""
    if not lines:
        return

    # Только для наших модулей
    if not name.startswith("maxo"):
        return

    is_method = name.startswith("maxo.bot.methods")
    is_type = name.startswith("maxo.types")

    if not hasattr(app, "_method_args"):
        app._method_args = {}

    class_name = name if what == "class" else ".".join(name.split(".")[:-1])

    new_lines = []
    in_code = False
    in_args = False

    for line in lines:
        s = line.strip()

        # 1. Исправление списков (rST требует пустой строки перед списком)
        if s.startswith("- ") and new_lines and new_lines[-1].strip() != "":
            new_lines.append("")

        # 2. Обработка секции Args
        if (is_method or is_type) and s == "Args:":
            in_args = True
            continue

        if in_args:
            if s == "" or s.startswith("Источник:") or s.startswith("Example:") or s.startswith(".. "):
                in_args = False
                if s: new_lines.append(line)
            else:
                m = re.match(r"^([a-z0-9_]+)\s*:\s*(.*)", s, re.IGNORECASE)
                if m:
                    arg_name, arg_desc = m.groups()
                    if class_name not in app._method_args:
                        app._method_args[class_name] = {}
                    app._method_args[class_name][arg_name] = arg_desc.strip()
                continue

        # 3. Превращаем Markdown заголовки ## в rST стиль
        if s.startswith("## "):
            title = s[3:]
            new_lines.append(title)
            new_lines.append("-" * len(title))
            new_lines.append("")
            continue

        # 4. Исправляем блоки кода (``` -> .. code-block::)
        if s.startswith("```"):
            if not in_code:
                lang = s.replace("`", "").strip() or "bash"
                if new_lines and new_lines[-1].strip():
                    new_lines.append("")
                new_lines.append(f".. code-block:: {lang}")
                new_lines.append("")
                in_code = True
            else:
                in_code = False
                new_lines.append("")
            continue

        if in_code:
            new_lines.append("    " + line)
        else:
            # 5. Экранирование и конвертация Markdown -> rST
            # Конвертируем одинарные обратные кавычки в двойные (inline code)
            processed_line = re.sub(r"(?<!`)`([^`\n]+)`(?!`)", r"``\1``", line)

            # Экранируем висячие подчеркивания и звездочки
            processed_line = re.sub(r"(?<!\\)([_*])", r"\\\1", processed_line)

            # Удаляем только висячую кавычку в конце, если она не часть пары
            if processed_line.count("`") % 2 != 0:
                processed_line = re.sub(r"(?<!`)(`)\s*$", r"\\`", processed_line)

            new_lines.append(processed_line)

    # 6. Подставляем описание атрибута, если оно пустое
    if (is_method or is_type) and what in ("attribute", "variable"):
        if not any(l.strip() for l in new_lines):
            attr_name = name.split(".")[-1]
            if class_name in app._method_args and attr_name in app._method_args[class_name]:
                desc = app._method_args[class_name][attr_name]
                # Обрабатываем описание так же
                desc = re.sub(r"(?<!`)`([^`\n]+)`(?!`)", r"``\1``", desc)
                desc = re.sub(r"(?<!\\)([_*])", r"\\\1", desc)
                new_lines.append(desc)

    lines[:] = new_lines


# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
}

# MyST settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
myst_heading_anchors = 3

# Set `typing.TYPE_CHECKING` to `True`:
# https://pypi.org/project/sphinx-autodoc-typehints/
set_type_checking_flag = True

language = "ru"

# Theme options
html_theme = "shibuya"

html_static_path = ["_static"]
html_extra_path = ["_extra"]


# ----- Changelog: pull from GitHub Releases at build time -----

def _refresh_changelog_from_github(app=None) -> None:
    """Перегенерировать ``pages/changelog.md`` из GitHub Releases.

    Вызывается из Sphinx-события ``builder-inited`` один раз за билд
    (RTD, локальный ``sphinx-build``). При сетевой ошибке / rate limit
    оставляет уже закоммиченный файл как фолбэк. Авторизация подхватывается
    из ``GITHUB_TOKEN``, если он задан в окружении (на RTD задаётся вручную
    через Admin > Environment Variables).
    """
    target = Path(__file__).parent / "pages" / "changelog.md"
    api_url = (
        "https://api.github.com/repos/K1rL3s/maxo/releases?per_page=100"
    )
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    def _fallback(reason: str) -> None:
        if target.exists():
            print(f"[changelog] {reason}; using committed file")
            return
        target.write_text(
            "# Changelog\n\n_(нет данных)_\n", encoding="utf-8",
        )

    try:
        req = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            releases = json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        _fallback(f"fetch failed ({exc})")
        return

    if not isinstance(releases, list):
        _fallback(
            f"unexpected GitHub response: {type(releases).__name__}",
        )
        return

    def _shift(text: str) -> str:
        # Сдвигаем уровень markdown-заголовков на единицу, но НЕ внутри
        # fenced-code-блоков, иначе `# install` в bash-сниппете релиза
        # превратится в `## install`.
        out: list[str] = []
        in_fence = False
        for line in text.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = not in_fence
                out.append(line)
                continue
            if not in_fence:
                line = re.sub(r"^(#{1,5})(\s)", r"#\1\2", line)
            out.append(line)
        return "\n".join(out)

    # Гайдлайн репо: только ASCII `-`. Покрываем все «нестандартные» тире.
    # Literals задаём через unicode escapes, чтобы и в исходниках conf.py
    # не было ни одного запрещённого символа.
    _DASH_TRANSLATE = {
        0x2010: "-",  # hyphen
        0x2011: "-",  # non-breaking hyphen
        0x2012: "-",  # figure dash
        0x2013: "-",  # en dash
        0x2014: "-",  # em dash
        0x2015: "-",  # horizontal bar
        0x2212: "-",  # minus sign
    }

    def _normalize_dashes(text: str) -> str:
        return text.translate(_DASH_TRANSLATE)

    parts = [
        "# Changelog\n",
        "История релизов автоматически собирается из "
        "[GitHub Releases](https://github.com/K1rL3s/maxo/releases) "
        "при каждой сборке документации.\n",
    ]
    for r in releases:
        if not isinstance(r, dict) or r.get("draft"):
            continue
        tag = r.get("tag_name", "")
        name = r.get("name") or tag
        published = (r.get("published_at") or "")[:10]
        html_url = r.get("html_url", "")
        body = (r.get("body") or "").strip()
        body = _normalize_dashes(_shift(body)) if body else "_(нет описания)_"
        title = _normalize_dashes(name if name and name != tag else tag)
        suffix = f" - {published}" if published else ""
        parts.append(f"\n## [{title}]({html_url}){suffix}\n")
        parts.append(body)
        parts.append("")
    target.write_text("\n".join(parts), encoding="utf-8")
    print(f"[changelog] wrote {len(releases)} releases -> {target.name}")

html_logo = "_static/maxo-logo.png"

html_favicon = "_static/maxo-logo.png"

html_theme_options = {
    "github_url": "https://github.com/K1rL3s/maxo",
    "readthedocs_url": "https://maxo.readthedocs.io",
    "globaltoc_expand_depth": 2,
    "nav_links": [
        {
            "title": "PyPI",
            "url": "https://pypi.org/project/maxo/",
        },
        {
            "title": "DeepWiki",
            "url": "https://deepwiki.com/K1rL3s/maxo",
        },
    ],
    "accent_color": "green",
    "dark_logo": "_static/maxo-logo.png",
}

html_context = {
    "source_type": "github",
    "source_user": "K1rL3s",
    "source_repo": "maxo",
    "source_version": "master",
}

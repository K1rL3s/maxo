import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from butcher.site_spec.fetch import REQUEST_DELAY, fetch_pages
from butcher.site_spec.overlay import build_site_spec
from butcher.site_spec.pages import parse_pages

DEFAULT_PAGES_DIR = Path(".butcher/site-pages")
DEFAULT_BASE = Path("max-swagger.json")
DEFAULT_OUTPUT = Path(".butcher/site-swagger.json")
DEFAULT_REPORT = Path(".butcher/site-report.json")
SHOWN_PAGES = 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="butcher.site_spec",
        description="Сваггер сайта dev.max.ru из HTML-страниц методов и объектов.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    fetch = commands.add_parser("fetch", help="Скачать страницы методов и объектов.")
    fetch.add_argument(
        "--pages-dir",
        type=Path,
        default=DEFAULT_PAGES_DIR,
        help=f"Каталог страниц (по умолчанию {DEFAULT_PAGES_DIR}).",
    )
    fetch.add_argument(
        "--delay",
        type=float,
        default=REQUEST_DELAY,
        help=f"Пауза между запросами в секундах (по умолчанию {REQUEST_DELAY}).",
    )
    build = commands.add_parser(
        "build",
        help="Наложить скачанные страницы на json и записать отчёт.",
    )
    build.add_argument(
        "--pages-dir",
        type=Path,
        default=DEFAULT_PAGES_DIR,
        help=f"Каталог страниц (по умолчанию {DEFAULT_PAGES_DIR}).",
    )
    build.add_argument(
        "--base",
        type=Path,
        default=DEFAULT_BASE,
        help=f"Спека, на которую накладывается сайт (по умолчанию {DEFAULT_BASE}).",
    )
    build.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Куда записать сваггер сайта (по умолчанию {DEFAULT_OUTPUT}).",
    )
    build.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"Куда записать отчёт (по умолчанию {DEFAULT_REPORT}).",
    )
    args = parser.parse_args(argv)

    if args.command == "fetch":
        count = fetch_pages(args.pages_dir, args.delay)
        print(f"Скачано страниц: {count} в {args.pages_dir}")
        return 0

    base = json.loads(args.base.read_text(encoding="utf-8"))
    spec, report = build_site_spec(base, parse_pages(args.pages_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(spec, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps([asdict(entry) for entry in report], ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )
    for entry in report:
        pages = ", ".join(entry.pages[:SHOWN_PAGES])
        if len(entry.pages) > SHOWN_PAGES:
            pages += f" +{len(entry.pages) - SHOWN_PAGES}"
        print(f"{entry.kind:8} {entry.location} {entry.fact} [{pages}]".rstrip())
    counts = Counter(entry.kind for entry in report)
    summary = ", ".join(f"{kind} {count}" for kind, count in sorted(counts.items()))
    print(f"Записано {args.output}, отчёт {args.report}: {summary or 'без изменений'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

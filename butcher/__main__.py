"""CLI генератора: свагер -> `src/maxo/types`, `enums`, `bot/methods`."""

import argparse
import sys
from pathlib import Path

from butcher.emit import write
from butcher.profile import build_profile
from butcher.spec import load

DEFAULT_SPEC = "max-swagger.json"
DEFAULT_OUTPUT = "src/maxo"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="butcher",
        description="Генерация типов, enum'ов и методов Bot API MAX по OpenAPI-спеке.",
    )
    parser.add_argument(
        "--spec",
        default=DEFAULT_SPEC,
        help=f"Путь или URL спеки (по умолчанию {DEFAULT_SPEC}).",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT,
        help=f"Каталог пакета maxo (по умолчанию {DEFAULT_OUTPUT}).",
    )
    args = parser.parse_args(argv)

    document = build_profile(load(args.spec))
    written = write(document, Path(args.output_dir))

    print(
        f"Готово: {len(document.models)} типов, {len(document.enums)} enum'ов, "
        f"{len(document.unions)} union-файлов, {len(document.methods)} методов "
        f"({len(written)} файлов).",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

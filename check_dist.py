import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path

WHEEL_REQUIRED = (
    "maxo/py.typed",
    "maxo/bot/russiantrustedca.pem",
    "dist-info/licenses/LICENSE",
    "dist-info/licenses/THIRD_PARTY_LICENSES",
)
SDIST_REQUIRED = (
    "LICENSE",
    "THIRD_PARTY_LICENSES",
    "src/maxo/py.typed",
    "src/maxo/bot/russiantrustedca.pem",
)
JUNK = ("graphify", "__pycache__", ".pyc", ".env", ".ds_store")


def single(directory: Path, pattern: str) -> Path:
    found = sorted(directory.glob(pattern))
    if len(found) != 1:
        raise SystemExit(
            f"Ожидался ровно один {pattern} в {directory}, найдено {len(found)}",
        )
    return found[0]


def check_wheel(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()

    for required in WHEEL_REQUIRED:
        if not any(required in name for name in names):
            raise SystemExit(f"В колесе нет {required}")

    junk = [name for name in names if any(part in name.lower() for part in JUNK)]
    if junk:
        raise SystemExit("В колесо попал локальный мусор: " + ", ".join(junk))


def check_sdist(sdist: Path) -> None:
    with tarfile.open(sdist) as archive:
        names = archive.getnames()

    for required in SDIST_REQUIRED:
        if not any(name.endswith(f"/{required}") for name in names):
            raise SystemExit(f"В sdist нет {required}")


def check_importable(wheel: Path) -> None:
    result = subprocess.run(
        [
            "uv",
            "run",
            "--isolated",
            "--no-project",
            "--with",
            str(wheel),
            "python",
            "-c",
            "import maxo",
        ],
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"Пакет не импортируется из одного только {wheel.name}")


def main() -> None:
    dist = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("dist")
    wheel = single(dist, "*.whl")
    check_wheel(wheel)
    check_sdist(single(dist, "*.tar.gz"))
    check_importable(wheel)


if __name__ == "__main__":
    main()

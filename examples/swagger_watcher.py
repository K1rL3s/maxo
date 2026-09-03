import ast
import asyncio
import difflib
import json
import logging
import math
import os
import re
from collections.abc import Awaitable
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from aiohttp import ClientSession, ClientTimeout

try:
    from maxo import Bot as MaxBot
    from maxo.types import LinkButton
    from maxo.types.facades import AttachmentsFacade
    from maxo.utils.upload_media import BufferedInputFile as MaxBufferedInputFile
except ModuleNotFoundError:
    MAXO_INSTALLED = False
else:
    MAXO_INSTALLED = True

try:
    from aiogram import Bot as TelegramBot
    from aiogram.types import (
        BufferedInputFile as TelegramBufferedInputFile,
        InlineKeyboardButton,
        InlineKeyboardMarkup,
    )
except ModuleNotFoundError:
    AIOGRAM_INSTALLED = False
else:
    AIOGRAM_INSTALLED = True

DOCS_URL = "https://dev.max.ru/docs-api"
DIFF_FILE_NAME = "max-bot-api-openapi.diff"
STATE_FILE_NAME = "max-bot-api-openapi.json"
VALUE_PREVIEW_LIMIT = 160
MAX_RETRY_DELAY = 86_400
MAX_BACKOFF_EXPONENT = 16
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
}
JSON_PARSE_RE = re.compile(r"JSON\.parse\('((?:\\.|[^'\\])*)'\)")
CHUNK_RE = re.compile(
    r"(?:src|href)=[\"']([^\"']*/_next/static/chunks/[^\"']+\.js)[\"']",
)
logger = logging.getLogger(__name__)

type JsonValue = None | bool | int | float | str | list[JsonValue] | JsonObject
type JsonObject = dict[str, JsonValue]
type Recipient = tuple[str, int]


@dataclass(frozen=True, slots=True)
class Settings:
    max_recipient: Recipient | None
    telegram_recipient: Recipient | None
    interval: float
    state_path: Path
    pending_path: Path


def load_recipient(chat_id_name: str, token_name: str) -> Recipient | None:
    chat_id = os.environ.get(chat_id_name)
    if chat_id is None:
        return None

    token = os.environ.get(token_name)
    if token is None:
        raise ValueError(f"Для {chat_id_name} задайте {token_name}")
    return token, int(chat_id)


def load_settings() -> Settings:
    max_recipient = load_recipient("MAX_CHAT_ID", "MAX_TOKEN")
    telegram_recipient = load_recipient("TG_CHAT_ID", "TG_TOKEN")
    if max_recipient is None and telegram_recipient is None:
        raise ValueError("Задайте MAX_CHAT_ID или TG_CHAT_ID")
    if max_recipient is not None and not MAXO_INSTALLED:
        raise RuntimeError("Для отправки в MAX установите maxo")
    if telegram_recipient is not None and not AIOGRAM_INSTALLED:
        raise RuntimeError("Для отправки в Telegram установите aiogram")

    interval = float(os.environ.get("CHECK_INTERVAL", "3600"))
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("CHECK_INTERVAL должен быть больше нуля")

    state_path = Path(os.environ.get("STATE_FILE", STATE_FILE_NAME))
    return Settings(
        max_recipient=max_recipient,
        telegram_recipient=telegram_recipient,
        interval=interval,
        state_path=state_path,
        pending_path=state_path.with_name(f".{state_path.name}.delivery.json"),
    )


def extract_openapi_json(javascript: str) -> JsonObject | None:
    for match in JSON_PARSE_RE.finditer(javascript):
        try:
            decoded: object = ast.literal_eval(f"'{match.group(1)}'")
            if not isinstance(decoded, str):
                continue
            value: JsonValue = json.loads(decoded)
        except (json.JSONDecodeError, SyntaxError, ValueError):
            continue

        if isinstance(value, dict) and "openapi" in value:
            return value
    return None


def serialize_json(value: JsonValue) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def render_value(value: JsonValue) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(text) <= VALUE_PREVIEW_LIMIT:
        return text
    return f"{text[: VALUE_PREVIEW_LIMIT - 3]}..."


def collect_changes(
    previous: JsonValue,
    current: JsonValue,
    added: list[str],
    removed: list[str],
    changed: list[str],
    path: str = "",
) -> None:
    if isinstance(previous, dict) and isinstance(current, dict):
        for key in sorted(previous.keys() - current.keys()):
            child_path = f"{path}.{key}" if path else key
            removed.append(f"- {child_path} = {render_value(previous[key])}")
        for key in sorted(current.keys() - previous.keys()):
            child_path = f"{path}.{key}" if path else key
            added.append(f"+ {child_path} = {render_value(current[key])}")
        for key in sorted(previous.keys() & current.keys()):
            child_path = f"{path}.{key}" if path else key
            collect_changes(
                previous[key],
                current[key],
                added,
                removed,
                changed,
                child_path,
            )
        return

    if previous != current:
        changed.append(f"~ {path}: {render_value(previous)} -> {render_value(current)}")


def build_diff(previous: str, current: str) -> tuple[str, int, int, int]:
    added: list[str] = []
    removed: list[str] = []
    changed: list[str] = []
    collect_changes(json.loads(previous), json.loads(current), added, removed, changed)

    summary = ["СТРУКТУРНЫЙ ОТЧЁТ"]
    for title, lines in (
        ("Добавлено", added),
        ("Удалено", removed),
        ("Изменено", changed),
    ):
        summary.extend(("", f"{title} ({len(lines)})", *(lines or ["нет"])))

    unified_diff = difflib.unified_diff(
        previous.splitlines(keepends=True),
        current.splitlines(keepends=True),
        fromfile=f"previous/{STATE_FILE_NAME}",
        tofile=f"current/{STATE_FILE_NAME}",
    )
    report = "\n".join(summary)
    report += "\n\nПОЛНЫЙ UNIFIED DIFF\n\n"
    report += "".join(unified_diff)
    return report, len(added), len(removed), len(changed)


def save_state(path: Path, content: str) -> None:
    temporary_path = path.with_name(f".{path.name}.tmp")
    temporary_path.write_text(content, encoding="utf-8")
    temporary_path.replace(path)


def load_delivered(path: Path, digest: str) -> set[str]:
    if not path.exists():
        return set()
    try:
        data: JsonValue = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.warning("Файл состояния доставки повреждён: %s", path)
        return set()
    if not isinstance(data, dict) or data.get("digest") != digest:
        return set()

    channels = data.get("channels")
    if not isinstance(channels, list):
        return set()
    delivered: set[str] = set()
    for channel in channels:
        if not isinstance(channel, str):
            return set()
        delivered.add(channel)
    return delivered


def save_delivered(path: Path, digest: str, delivered: set[str]) -> None:
    channels: list[JsonValue] = []
    channels.extend(sorted(delivered))
    data: JsonObject = {
        "digest": digest,
        "channels": channels,
    }
    save_state(path, serialize_json(data))


async def fetch_openapi(session: ClientSession) -> JsonObject:
    async with session.get(DOCS_URL) as response:
        response.raise_for_status()
        html = await response.text()

    embedded = extract_openapi_json(html)
    if embedded is not None:
        return embedded

    chunk_urls = dict.fromkeys(
        urljoin(DOCS_URL, path) for path in CHUNK_RE.findall(html)
    )
    for url in chunk_urls:
        parsed_url = urlsplit(url)
        if parsed_url.scheme != "https" or parsed_url.hostname != "dev.max.ru":
            logger.warning("Пропущен чанк с недоверенного URL: %s", url)
            continue
        async with session.get(url) as response:
            response.raise_for_status()
            javascript = await response.text()

        if '"openapi"' not in javascript:
            continue
        spec = extract_openapi_json(javascript)
        if spec is not None:
            return spec
        logger.warning("Не удалось извлечь OpenAPI из чанка %s", url)

    raise RuntimeError("OpenAPI-спецификация не найдена")


async def publish_max(token: str, chat_id: int, diff: str, message: str) -> None:
    async with MaxBot(token).context() as bot:
        attachments = await AttachmentsFacade(bot).build_attachments(
            base=[],
            keyboard=[[LinkButton(text="Документация", url=DOCS_URL)]],
            files=[MaxBufferedInputFile.file(diff.encode(), DIFF_FILE_NAME)],
        )
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            attachments=list(attachments),
        )


async def publish_telegram(token: str, chat_id: int, diff: str, message: str) -> None:
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="Документация", url=DOCS_URL)]],
    )

    async with TelegramBot(token) as bot:
        await bot.send_document(
            chat_id=chat_id,
            document=TelegramBufferedInputFile(diff.encode(), filename=DIFF_FILE_NAME),
            caption=message,
            reply_markup=keyboard,
        )


async def publish_update(
    settings: Settings,
    diff: str,
    message: str,
    digest: str,
) -> None:
    delivered = load_delivered(settings.pending_path, digest)

    async def publish(name: str, delivery: Awaitable[None]) -> Exception | None:
        try:
            await delivery
        # Каналы используют разные клиенты с разными иерархиями ошибок
        except Exception as error:
            logger.exception(
                "Не удалось отправить уведомление в %s",
                name,
            )
            return error

        delivered.add(name)
        save_delivered(settings.pending_path, digest, delivered)
        return None

    deliveries: list[tuple[str, Awaitable[None]]] = []
    if settings.max_recipient is not None and "MAX" not in delivered:
        deliveries.append(
            ("MAX", publish_max(*settings.max_recipient, diff, message)),
        )
    if settings.telegram_recipient is not None and "Telegram" not in delivered:
        deliveries.append(
            (
                "Telegram",
                publish_telegram(*settings.telegram_recipient, diff, message),
            ),
        )

    results = await asyncio.gather(
        *(publish(name, delivery) for name, delivery in deliveries),
    )
    failures = [result for result in results if result is not None]
    if failures:
        raise ExceptionGroup("Не все уведомления доставлены", failures)


async def check_for_update(session: ClientSession, settings: Settings) -> None:
    current = serialize_json(await fetch_openapi(session))
    if not settings.state_path.exists():
        save_state(settings.state_path, current)
        settings.pending_path.unlink(missing_ok=True)
        logger.info("Начальное состояние OpenAPI сохранено")
        return

    previous = settings.state_path.read_text(encoding="utf-8")
    if previous == current:
        settings.pending_path.unlink(missing_ok=True)
        return

    diff, added, removed, changed = build_diff(previous, current)
    logger.info("%s", diff)
    message = (
        f"OpenAPI Max Bot API обновлён\nИзменения: +{added} / -{removed} / ~{changed}"
    )
    digest = sha256(current.encode(), usedforsecurity=False).hexdigest()
    await publish_update(settings, diff, message, digest)
    save_state(settings.state_path, current)
    settings.pending_path.unlink(missing_ok=True)
    logger.info("OpenAPI обновлён: +%d / -%d / ~%d", added, removed, changed)


async def main() -> None:
    settings = load_settings()
    settings.state_path.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    async with ClientSession(
        headers=REQUEST_HEADERS,
        timeout=ClientTimeout(total=60),
    ) as session:
        while True:
            try:
                await check_for_update(session, settings)
            except asyncio.CancelledError:
                raise
            except Exception:
                failures += 1
                logger.exception("Не удалось проверить OpenAPI")
                delay = max(
                    settings.interval,
                    min(
                        settings.interval
                        * 2 ** min(failures - 1, MAX_BACKOFF_EXPONENT),
                        MAX_RETRY_DELAY,
                    ),
                )
                logger.info("Повторная проверка через %.0f секунд", delay)
            else:
                failures = 0
                delay = settings.interval
            await asyncio.sleep(delay)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    asyncio.run(main())

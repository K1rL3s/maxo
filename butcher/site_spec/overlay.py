import copy
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from typing import Any
from urllib.parse import unquote

from butcher.site_spec.pages import Page, Param

HTTP_METHODS = ("get", "post", "put", "patch", "delete")
TYPE_WORDS = frozenset(
    {"string", "integer", "number", "boolean", "object", "array", "enum", "apiKey"},
)
LIMIT_PATTERNS = (
    (re.compile(r"^от `(\d+)` до `(\d+)` символ\w*$"), ("minLength", "maxLength")),
    (re.compile(r"^до `(\d+)` символ\w*$"), ("maxLength",)),
    (re.compile(r"^от `(\d+)` символ\w*$"), ("minLength",)),
    (re.compile(r"^от `(\d+)` до `(\d+)` элемент\w*$"), ("minItems", "maxItems")),
    (re.compile(r"^до `(\d+)` элемент\w*$"), ("maxItems",)),
    (re.compile(r"^от `(\d+)` элемент\w*$"), ("minItems",)),
)
DEFAULT_RE = re.compile(r"^По умолчанию: `(.*)`$")
EXAMPLE_RE = re.compile(r"^Пример: `(.*)`$")
ENUM_RE = re.compile(r"^Возможные значения в enum:((?: `\"[^`]*\"`)+)$")
ENUM_VALUE_RE = re.compile(r'`"([^`]*)"`')
RANGE_RE = re.compile(r"^\[(-?\d+)-(-?\d+)\]$")
FORMAT_RE = re.compile(r"^<(.+)>$")
LENGTH_LIMITS = ("minLength", "maxLength", "minItems", "maxItems")
RANGE_LIMITS = ("minimum", "maximum")
SCHEMAS = ("components", "schemas")
REF_DEPTH = 10
PATH_PARTS = 2

type Pointer = tuple[str | int, ...]
type Key = tuple[str, Pointer]


@dataclass(slots=True)
class TypeInfo:
    base: str | None = None
    array: int = 0
    name: str | None = None
    format: str | None = None
    nullable: bool = False
    minimum: int | None = None
    maximum: int | None = None
    item_base: str | None = None


@dataclass(slots=True)
class Effective:
    description: str | None
    desc_owner: int | None
    descriptions: list[str]
    example: Any
    chain: list[dict[str, Any]]
    nullable: bool
    format: str | None
    type: str | None
    array: int
    ref: str | None
    enum: list[Any] | None
    default: Any
    pattern: str | None
    limits: dict[str, Any]


@dataclass(slots=True, frozen=True)
class ReportEntry:
    kind: str
    location: str
    pages: tuple[str, ...] = ()
    fact: str = ""
    site: Any = None
    base: Any = None


@dataclass(slots=True)
class Change:
    kind: str
    pointer: Pointer
    fact: str
    site: Any
    base: Any
    pages: tuple[str, ...]


@dataclass(slots=True)
class Addition:
    param: Param
    pages: set[str] = field(default_factory=set)


def parse_type(raw: str) -> TypeInfo:
    info = TypeInfo()
    for word in raw.split():
        if word == "Nullable":
            info.nullable = True
        elif match := FORMAT_RE.match(word):
            info.format = match.group(1)
        elif match := RANGE_RE.match(word):
            info.minimum, info.maximum = int(match.group(1)), int(match.group(2))
        elif word.endswith("[]") and info.base is None:
            core = word.rstrip("[]")
            info.array = (len(word) - len(core)) // 2
            info.base = "array"
            if core in TYPE_WORDS:
                info.item_base = core
            elif core:
                info.name = core
        elif word == "[]" and info.base is not None:
            info.item_base, info.base, info.array = info.base, "array", 1
        elif word in TYPE_WORDS and info.base is None:
            info.base = word
        elif word[:1].isupper():
            info.name = word
    if info.base == "array" and info.format and info.item_base is None:
        info.item_base, info.format, info.array = info.format, None, 1
    return info


def split_description(markdown: str) -> tuple[dict[str, Any], str]:
    facts: dict[str, Any] = {}
    rest = markdown.strip()
    while rest:
        line, _, tail = rest.partition("\n")
        line = line.strip()
        for pattern, keys in LIMIT_PATTERNS:
            if match := pattern.match(line):
                facts.update(
                    {
                        key: int(value)
                        for key, value in zip(keys, match.groups(), strict=True)
                    },
                )
                break
        else:
            if match := DEFAULT_RE.match(line):
                facts["default"] = match.group(1)
            elif match := EXAMPLE_RE.match(line):
                facts["example"] = match.group(1)
            elif match := ENUM_RE.match(line):
                facts["enum"] = ENUM_VALUE_RE.findall(match.group(1))
            else:
                break
        rest = tail.strip()
    return facts, rest


def plain(text: str | None) -> str:
    if not text:
        return ""
    text = unquote(text).replace("•", " ")
    text = text.replace("“", '"').replace("”", '"')
    text = re.sub(r">\s*!", " ", text)
    text = re.sub(r"`{3,}\w*", " ", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = re.sub(r"(?m)^\s*-{3,}\s*$", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"(?m)^\s*(?:[-*+]|\d+\.)\s+", " ", text)
    text = re.sub(r"[`*_>#\\|]", "", text)
    return " ".join(text.split()).replace(" ,", ",").rstrip(".").strip()


def default_value(raw: str) -> Any:
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def ref_pointer(ref: str | dict[str, str]) -> Pointer:
    if isinstance(ref, dict):
        ref = ref["$ref"]
    return tuple(ref.removeprefix("#/").split("/"))


def wrapped_ref(schema: dict[str, Any]) -> str | None:
    if "$ref" in schema:
        return str(schema["$ref"])
    parts = schema.get("allOf")
    if parts and len(parts) == 1 and "$ref" in parts[0] and "properties" not in schema:
        return str(parts[0]["$ref"])
    return None


def build_site_spec(
    base: dict[str, Any],
    pages: list[Page],
) -> tuple[dict[str, Any], list[ReportEntry]]:
    overlay = SiteOverlay(base, pages)
    overlay.run()
    return overlay.spec, overlay.report


class SiteOverlay:
    def __init__(self, base: dict[str, Any], pages: list[Page]) -> None:
        self.spec: dict[str, Any] = copy.deepcopy(base)
        self.pages = pages
        self.schemas: dict[str, Any] = self.spec["components"]["schemas"]
        self.report: list[ReportEntry] = []
        self.page = ""
        self.observations: dict[Key, dict[str, Counter[str]]] = defaultdict(
            lambda: defaultdict(Counter),
        )
        self.observed_on: dict[tuple[Key, str], set[str]] = defaultdict(set)
        self.site_texts: dict[tuple[Key, str, str], str] = {}
        self.seen_props: set[Pointer] = set()
        self.visited: dict[Pointer, set[str]] = defaultdict(set)
        self.additions: dict[tuple[Pointer, str], Addition] = {}
        self.seen_operations: dict[tuple[str, str], str] = {}
        self.seen_params: set[Pointer] = set()
        self.mapping_seen: dict[str, set[str]] = defaultdict(set)
        self.new_variants: dict[tuple[str, str], list[Param]] = {}
        self.variant_pages: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.new_param_ids: set[int] = set()

    def note(self, kind: str, pointer: Pointer, **details: Any) -> None:
        where = self.describe(pointer)
        pages = details.pop("pages", (self.page,) if self.page else ())
        self.report.append(ReportEntry(kind, where, tuple(pages), **details))

    def get(self, pointer: Pointer) -> Any:
        current: Any = self.spec
        for part in pointer:
            current = current[part]
        return current

    def target(self, pointer: Pointer) -> Pointer:
        schema = self.get(pointer)
        while True:
            ref = wrapped_ref(schema)
            if ref:
                pointer = ref_pointer(ref)
                schema = self.get(pointer)
                continue
            if schema.get("type") == "array" or (
                "items" in schema and "properties" not in schema
            ):
                pointer = (*pointer, "items")
                schema = self.get(pointer)
                continue
            return pointer

    def flatten(
        self,
        pointer: Pointer,
        out: dict[str, tuple[Pointer, Pointer]] | None = None,
    ) -> dict[str, tuple[Pointer, Pointer]]:
        out = {} if out is None else out
        schema = self.get(pointer)
        if "$ref" in schema:
            return self.flatten(ref_pointer(schema["$ref"]), out)
        for index in range(len(schema.get("allOf", []))):
            self.flatten((*pointer, "allOf", index), out)
        for name in schema.get("properties", {}):
            out[name] = ((*pointer, "properties", name), pointer)
        return out

    def discriminator(self, pointer: Pointer) -> dict[str, Any] | None:
        schema = self.get(pointer)
        if "$ref" in schema:
            return self.discriminator(ref_pointer(schema["$ref"]))
        if "discriminator" in schema:
            return schema["discriminator"]
        for index in range(len(schema.get("allOf", []))):
            found = self.discriminator((*pointer, "allOf", index))
            if found:
                return found
        return None

    def group_discriminator(self, group: str, container: Pointer) -> dict[str, Any]:
        pointer = (*SCHEMAS, group) if group in self.schemas else container
        return self.discriminator(pointer) or {}

    def observe(
        self,
        key: Key,
        fact: str,
        site: Any,
        base: Any,
        text: str | None = None,
    ) -> None:
        pair = json.dumps([site, base], ensure_ascii=False, sort_keys=True)
        self.observations[key][fact][pair] += 1
        self.observed_on[key, fact].add(self.page)
        if text is not None:
            value = json.dumps(site, ensure_ascii=False, sort_keys=True)
            self.site_texts.setdefault((key, fact, value), text)

    def effective(self, pointer: Pointer) -> Effective:
        chain: list[dict[str, Any]] = [self.get(pointer)]
        ref_name: str | None = None
        for _ in range(REF_DEPTH):
            ref = wrapped_ref(chain[-1])
            if not ref:
                break
            ref_name = ref_name or ref.rsplit("/", 1)[1]
            chain.append(self.get(ref_pointer(ref)))
        items_depth = 0
        node = chain[-1]
        item_chain: list[dict[str, Any]] = []
        while node.get("type") == "array":
            items_depth += 1
            node = node.get("items", {})
            item_chain.append(node)
            ref = wrapped_ref(node)
            if ref:
                ref_name = ref.rsplit("/", 1)[1]
                node = self.get(ref_pointer(ref))
                item_chain.append(node)

        def first(key: str, nodes: list[dict[str, Any]]) -> Any:
            for item in nodes:
                if key in item and item[key] not in ("", None):
                    return item[key]
            return None

        leaf = item_chain[-1] if item_chain else chain[-1]
        if ref_name and len(chain) > 1 and not items_depth:
            type_ = first("type", chain[1:]) or "object"
        else:
            type_ = first("type", chain) or (
                "object"
                if {"properties", "allOf", "discriminator"} & leaf.keys()
                else None
            )
        return Effective(
            description=first("description", chain),
            desc_owner=next(
                (index for index, item in enumerate(chain) if item.get("description")),
                None,
            ),
            descriptions=[
                item["description"] for item in chain if item.get("description")
            ],
            example=first("example", chain),
            chain=chain,
            nullable=bool(first("nullable", chain)),
            format=(
                first("format", item_chain)
                if items_depth
                else first("format", chain + item_chain[-1:])
            ),
            type=type_,
            array=items_depth,
            ref=ref_name,
            enum=first("enum", chain + item_chain),
            default=first("default", chain),
            pattern=first("pattern", chain + item_chain),
            limits={key: first(key, chain) for key in (*LENGTH_LIMITS, *RANGE_LIMITS)},
        )

    def compare_schema(
        self,
        key: Key,
        param: Param,
        effective: Effective,
        extra: dict[str, Any],
        description: str,
    ) -> None:
        info = parse_type(param.type)
        site_description = plain(description)
        known = [plain(text) for text in effective.descriptions]
        base_description = (
            site_description
            if site_description in known
            else plain(effective.description)
        )
        self.observe(
            key,
            "description",
            site_description,
            base_description,
            description,
        )
        self.observe(key, "nullable", info.nullable, effective.nullable)
        if info.base not in {"enum", "apiKey"} and info.minimum is None:
            self.observe(
                key,
                "format",
                None if info.array else info.format,
                None if effective.array else effective.format,
            )
        if info.base == "array" or effective.array:
            self.observe(key, "type", f"array{info.array}", f"array{effective.array}")
        elif info.base == "enum":
            self.observe(
                key,
                "type",
                "enum",
                "enum" if effective.enum else effective.type,
            )
        elif info.base == "object":
            self.observe(
                key,
                "type",
                "object",
                effective.type or ("object" if effective.ref else None),
            )
        else:
            self.observe(key, "type", info.base, effective.type)
        if info.name:
            self.observe(key, "ref", info.name, effective.ref)
        self.observe(key, "pattern", param.pattern, effective.pattern)
        for limit in LENGTH_LIMITS:
            if (
                extra.get(limit) is None
                and effective.limits[limit] is not None
                and limit not in effective.chain[0]
            ):
                continue
            self.observe(key, limit, extra.get(limit), effective.limits[limit])
        if info.minimum is not None or None not in (
            effective.limits["minimum"],
            effective.limits["maximum"],
        ):
            self.observe(key, "minimum", info.minimum, effective.limits["minimum"])
            self.observe(key, "maximum", info.maximum, effective.limits["maximum"])
        site_default = default_value(extra["default"]) if "default" in extra else None
        if not (site_default is None and effective.default is False):
            self.observe(key, "default", site_default, effective.default)
        if "enum" in extra or (effective.enum and not effective.array):
            self.observe(
                key,
                "enum",
                extra.get("enum"),
                [str(value) for value in effective.enum] if effective.enum else None,
            )
        if "example" in extra or effective.example is not None:
            example = effective.example
            if not (isinstance(example, str) or example is None):
                example = json.dumps(example, ensure_ascii=False)
            self.observe(key, "example", extra.get("example"), example)

    def walk(self, params: list[Param], container: Pointer) -> None:
        self.visited[container].add(self.page)
        props = self.flatten(container)
        for _, owner in props.values():
            self.visited[owner].add(self.page)
        names = {param.name for param in params}
        for param in params:
            hit = props.get(param.name)
            if hit is None:
                self.add_property(container, param)
                continue
            prop, owner = hit
            self.seen_props.add(prop)
            extra, description = split_description(param.description)
            key: Key = ("prop", prop)
            required = param.name in self.get(owner).get("required", [])
            self.observe(key, "required", not param.optional, required)
            self.compare_schema(key, param, self.effective(prop), extra, description)
            if param.children:
                self.walk(param.children, self.target(prop))
            if param.variants:
                self.walk_variants(param, container, names)

    def walk_variants(self, param: Param, container: Pointer, outer: set[str]) -> None:
        if param.selector is None or param.variants is None:
            return
        group = param.selector.group
        mapping = self.group_discriminator(group, container).get("mapping", {})
        self.mapping_seen[group].update(param.selector.values)
        for value, variant in param.variants.items():
            if value not in mapping:
                self.new_variants[group, value] = variant
                self.variant_pages[group, value].add(self.page)
                continue
            mapped = ref_pointer(mapping[value])
            self.walk(variant, mapped)
            for name, (pointer, _) in self.flatten(mapped).items():
                if name in outer:
                    self.seen_props.add(pointer)

    def add_property(self, container: Pointer, param: Param) -> None:
        addition = self.additions.setdefault((container, param.name), Addition(param))
        addition.pages.add(self.page)

    def schema_from_param(self, param: Param, pages: tuple[str, ...]) -> dict[str, Any]:
        info = parse_type(param.type)
        extra, description = split_description(param.description)
        inner: dict[str, Any]
        if info.name and info.name in self.schemas:
            inner = {"$ref": f"#/components/schemas/{info.name}"}
        elif param.children is not None or info.base == "object":
            inner = {
                "type": (
                    info.item_base
                    if info.base == "array" and info.item_base is not None
                    else "object"
                ),
            }
            if param.children:
                inner["properties"] = {
                    child.name: self.schema_from_param(child, pages)
                    for child in param.children
                }
                required = [
                    child.name for child in param.children if not child.optional
                ]
                if required:
                    inner["required"] = required
            if info.name:
                self.schemas[info.name] = inner
                self.note("added", (*SCHEMAS, info.name), pages=pages)
                inner = {"$ref": f"#/components/schemas/{info.name}"}
        else:
            inner = {
                "type": info.item_base
                or ("string" if info.base == "enum" else info.base),
            }
            if info.format:
                inner["format"] = info.format
        schema = inner
        for _ in range(info.array):
            schema = {"type": "array", "items": schema}
        if "$ref" in schema and (description or info.nullable):
            schema = {"allOf": [schema]}
        if description:
            schema["description"] = description
        if info.nullable:
            schema["nullable"] = True
        schema.update(
            {limit: extra[limit] for limit in LENGTH_LIMITS if limit in extra},
        )
        if "enum" in extra and "$ref" not in inner:
            schema["enum"] = extra["enum"]
        if "default" in extra:
            schema["default"] = default_value(extra["default"])
        if info.minimum is not None:
            schema["minimum"], schema["maximum"] = info.minimum, info.maximum
        if param.pattern:
            schema["pattern"] = param.pattern
        return schema

    def walk_params(self, params: list[Param], operation: Pointer, path: str) -> None:
        base_params = self.get(operation).setdefault("parameters", [])
        by_name = {
            item["name"]: index
            for index, item in enumerate(base_params)
            if "name" in item
        }
        for param in params:
            in_path = "{" + param.name + "}" in path
            if param.name not in by_name:
                new: dict[str, Any] = {
                    "name": param.name,
                    "in": "path" if in_path else "query",
                    "required": not param.optional or in_path,
                }
                schema = self.schema_from_param(param, (self.page,))
                if "description" in schema:
                    new["description"] = schema.pop("description")
                new["schema"] = schema
                base_params.append(new)
                self.new_param_ids.add(id(new))
                self.note("added", (*operation, "parameters", param.name))
                continue
            pointer = (*operation, "parameters", by_name[param.name])
            self.seen_params.add(pointer)
            base_param = base_params[by_name[param.name]]
            extra, description = split_description(param.description)
            key: Key = ("param", pointer)
            required = bool(base_param.get("required"))
            self.observe(key, "required", not param.optional, required)
            effective = self.effective((*pointer, "schema"))
            effective = replace(
                effective,
                description=base_param.get("description") or effective.description,
            )
            self.compare_schema(key, param, effective, extra, description)

    def run(self) -> None:
        for page in self.pages:
            self.page = page.key
            if page.method and page.path:
                self.run_method(page, page.method.lower(), page.path)
            else:
                self.run_object(page)
        self.page = ""
        self.finish()

    def run_object(self, page: Page) -> None:
        if page.title not in self.schemas:
            self.note("manual", (*SCHEMAS, page.title), fact="schema")
            return
        pointer = (*SCHEMAS, page.title)
        self.observe(
            ("schema", pointer),
            "description",
            plain(page.intro),
            plain(self.schemas[page.title].get("description")),
            page.intro,
        )
        for section in page.sections:
            self.walk(section.params, pointer)

    def run_method(self, page: Page, method: str, path: str) -> None:
        if method not in self.spec["paths"].get(path, {}):
            self.spec["paths"].setdefault(path, {})[method] = {
                "summary": page.title,
                "description": page.intro,
                "responses": {},
            }
            self.note("added", ("paths", path, method), fact="operation")
        operation: Pointer = ("paths", path, method)
        self.seen_operations[path, method] = page.key
        spec_operation = self.get(operation)
        self.observe(
            ("op", operation),
            "summary",
            " ".join(page.title.split()),
            " ".join((spec_operation.get("summary") or "").split()),
            " ".join(page.title.split()),
        )
        self.observe(
            ("op", operation),
            "description",
            plain(page.intro),
            plain(spec_operation.get("description")),
            page.intro,
        )
        for section in page.sections:
            if section.heading == "Параметры":
                self.walk_params(section.params, operation, path)
            elif section.heading == "Тело запроса":
                self.walk_body(section.params, operation)
            elif section.heading == "Результат":
                self.walk_result(section.params, operation)
        self.compare_codes(page, operation)

    def walk_body(self, params: list[Param], operation: Pointer) -> None:
        spec_operation = self.get(operation)
        content = spec_operation.get("requestBody", {}).get("content", {})
        if not content:
            spec_operation["requestBody"] = {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                param.name: self.schema_from_param(param, (self.page,))
                                for param in params
                            },
                        },
                    },
                },
            }
            self.note("added", (*operation, "requestBody"))
            return
        media = next(iter(content))
        schema = (*operation, "requestBody", "content", media, "schema")
        self.walk(params, self.target(schema))

    def walk_result(self, params: list[Param], operation: Pointer) -> None:
        responses = self.get(operation).get("responses", {})
        codes = sorted(code for code in responses if code.startswith("2"))
        if not codes:
            self.note("manual", (*operation, "responses"), fact="result")
            return
        response_pointer: Pointer = (*operation, "responses", codes[0])
        response = responses[codes[0]]
        if "$ref" in response:
            response_pointer = ref_pointer(response["$ref"])
            response = self.get(response_pointer)
        if not response.get("content"):
            self.note("manual", response_pointer, fact="result")
            return
        media = next(iter(response["content"]))
        schema = (*response_pointer, "content", media, "schema")
        self.walk(params, self.target(schema))

    def compare_codes(self, page: Page, operation: Pointer) -> None:
        responses = self.get(operation).setdefault("responses", {})
        for row in page.codes:
            response = responses.get(row.code)
            if response is None:
                responses[row.code] = {"description": row.description}
                self.note("added", (*operation, "responses", row.code))
                continue
            if "$ref" in response:
                response = self.get(ref_pointer(response["$ref"]))
            self.observe(
                ("resp", (*operation, "responses", row.code)),
                "description",
                plain(row.description),
                plain(response.get("description")),
                row.description,
            )
        site_codes = {row.code for row in page.codes}
        for code in responses:
            if page.codes and code not in site_codes:
                self.note("removed", (*operation, "responses", code))

    def finish(self) -> None:
        for change in self.collect_changes():
            applied = self.apply_change(change)
            self.note(
                "changed" if applied else "manual",
                change.pointer,
                pages=change.pages,
                fact=change.fact,
                site=change.site,
                base=change.base,
            )
        self.report_removals()
        self.apply_additions()
        self.apply_variants()
        self.report_unseen_operations()

    def collect_changes(self) -> list[Change]:
        changes = []
        for key, facts in self.observations.items():
            kind, pointer = key
            for fact, counter in facts.items():
                pairs = [(json.loads(pair), count) for pair, count in counter.items()]
                base = pairs[0][0][1]
                site_values: Counter[str] = Counter()
                for (site, _), count in pairs:
                    site_values[
                        json.dumps(site, ensure_ascii=False, sort_keys=True)
                    ] += count
                site = json.loads(site_values.most_common(1)[0][0])
                pages = tuple(sorted(self.observed_on[key, fact]))
                if len(site_values) > 1:
                    self.note(
                        "conflict",
                        pointer,
                        pages=pages,
                        fact=fact,
                        site=[json.loads(value) for value in site_values],
                    )
                if site == base or (fact == "description" and not (site or base)):
                    continue
                changes.append(Change(kind, pointer, fact, site, base, pages))
        return changes

    def apply_change(self, change: Change) -> bool:
        kind, pointer, fact = change.kind, change.pointer, change.fact
        site = json.dumps(change.site, ensure_ascii=False, sort_keys=True)
        text = self.site_texts.get(((kind, pointer), fact, site), change.site)
        if kind in {"op", "schema"}:
            self.get(pointer)[fact] = text
            return True
        if kind == "resp":
            response = self.get(pointer)
            if "$ref" in response:
                return False
            response["description"] = text
            return True
        if kind == "param":
            if fact in {"required", "description"}:
                self.get(pointer)[fact] = text if fact == "description" else change.site
                return True
            return self.set_schema_fact((*pointer, "schema"), change)
        if fact == "required":
            owner = self.get(pointer[:-2])
            required = owner.setdefault("required", [])
            name = pointer[-1]
            if change.site and name not in required:
                required.append(name)
            elif not change.site and name in required:
                required.remove(name)
            if not required:
                owner.pop("required")
            return True
        if fact == "description":
            self.set_description(pointer, text)
            return True
        return self.set_schema_fact(pointer, change)

    def set_description(self, pointer: Pointer, description: str) -> None:
        effective = self.effective(pointer)
        owner = effective.desc_owner
        if owner:
            holder = effective.chain[owner]
        else:
            holder = self.get(pointer)
            if "$ref" in holder:
                holder = self.unref(pointer)
        if description:
            holder["description"] = description
        else:
            holder.pop("description", None)

    def unref(self, pointer: Pointer) -> dict[str, Any]:
        prop = self.get(pointer)
        wrapped = {"allOf": [{"$ref": prop.pop("$ref")}], **prop}
        prop.clear()
        prop.update(wrapped)
        return prop

    def set_schema_fact(self, pointer: Pointer, change: Change) -> bool:
        fact, site = change.fact, change.site
        if fact in {"type", "ref"}:
            return False
        effective = self.effective(pointer)
        chain = effective.chain
        if fact == "enum":
            holder = next((item for item in chain if "enum" in item), None)
            if holder is None or site is None:
                return False
            current = holder["enum"]
            holder["enum"] = (
                [type(current[0])(value) for value in site] if current else site
            )
            return True
        if fact == "format" and effective.array:
            return False
        holder = next((item for item in chain if fact in item), None)
        if holder is None:
            holder = self.get(pointer)
            if "$ref" in holder:
                holder = self.unref(pointer)
        if site is None or site is False:
            holder.pop(fact, None)
            if fact == "nullable" and any(item.get("nullable") for item in chain):
                holder["nullable"] = False
        else:
            holder[fact] = site
        return True

    def addition_target(self, container: Pointer) -> dict[str, Any]:
        schema = self.get(container)
        if "allOf" not in schema:
            return schema
        parts = schema["allOf"]
        inline = [part for part in parts if "$ref" not in part]
        if inline:
            return inline[-1]
        parts.append({})
        return parts[-1]

    def apply_additions(self) -> None:
        for (container, name), addition in self.additions.items():
            pages = tuple(sorted(addition.pages))
            target = self.addition_target(container)
            target.setdefault("properties", {})[name] = self.schema_from_param(
                addition.param,
                pages,
            )
            if not addition.param.optional:
                target.setdefault("required", []).append(name)
            self.note(
                "added",
                (*container, "properties", name),
                pages=pages,
                fact=addition.param.type,
            )

    def apply_variants(self) -> None:
        for (group, value), params in self.new_variants.items():
            pages = tuple(sorted(self.variant_pages[group, value]))
            name = "".join(word.capitalize() for word in value.split("_")) + group
            if name in self.schemas:
                self.note(
                    "manual",
                    (*SCHEMAS, name),
                    pages=pages,
                    fact=f"{group}[{value}]",
                )
                continue
            self.schemas[name] = {
                "allOf": [
                    {"$ref": f"#/components/schemas/{group}"},
                    {
                        "properties": {
                            param.name: self.schema_from_param(param, pages)
                            for param in params
                        },
                        "required": [
                            param.name for param in params if not param.optional
                        ],
                    },
                ],
            }
            discriminator = self.discriminator((*SCHEMAS, group))
            if discriminator is not None:
                mapping = discriminator.setdefault("mapping", {})
                mapping[value] = f"#/components/schemas/{name}"
            self.note(
                "added",
                (*SCHEMAS, name),
                pages=pages,
                fact=f"{group}[{value}]",
            )
        for group, values in self.mapping_seen.items():
            if group not in self.schemas:
                continue
            mapping = (self.discriminator((*SCHEMAS, group)) or {}).get("mapping", {})
            for missing in sorted(set(mapping) - values):
                self.note("removed", (*SCHEMAS, group, "discriminator", missing))

    def report_removals(self) -> None:
        for owner, pages in sorted(self.visited.items(), key=lambda item: str(item[0])):
            try:
                schema = self.get(owner)
            except (KeyError, IndexError):
                continue
            for name in schema.get("properties", {}):
                pointer = (*owner, "properties", name)
                if pointer not in self.seen_props:
                    self.note("removed", pointer, pages=sorted(pages))

    def report_unseen_operations(self) -> None:
        for path, item in self.spec["paths"].items():
            for method in [method for method in item if method in HTTP_METHODS]:
                page = self.seen_operations.get((path, method))
                if page is None:
                    self.note("removed", ("paths", path, method), pages=())
                    continue
                params = item[method].get("parameters", [])
                for index, param in enumerate(params):
                    pointer = ("paths", path, method, "parameters", index)
                    if (
                        "name" in param
                        and param.get("in") != "header"
                        and id(param) not in self.new_param_ids
                        and pointer not in self.seen_params
                    ):
                        self.note(
                            "removed",
                            ("paths", path, method, "parameters", param["name"]),
                            pages=(page,),
                        )

    def describe(self, pointer: Pointer) -> str:
        parts: list[str | int] = list(pointer)
        for index, part in enumerate(parts[:-1]):
            if part == "parameters" and isinstance(parts[index + 1], int):
                param = self.get(pointer[: index + 2])
                parts[index + 1] = param.get("name", parts[index + 1])
        if parts[0] == "paths" and len(parts) > PATH_PARTS:
            rest = "/".join(map(str, parts[3:]))
            return f"{str(parts[2]).upper()} {parts[1]} {rest}".rstrip()
        if tuple(parts[:2]) == SCHEMAS:
            parts = parts[2:]
        return "/".join(map(str, parts))

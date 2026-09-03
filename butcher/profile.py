"""
maxo-профиль: превращает IR генератора в структуры, готовые к рендеру.

Генератор отдаёт нейтральный IR, а здесь применяется всё, чем maxo отличается
от голого свагера: enum'ы из дискриминаторов, `datetime` вместо int64-таймстемпов,
union-алиасы вместо ссылок на базу, пропуски, ручные добавки и фасады.
"""

import re
from dataclasses import dataclass, field

from unihttp_openapi_generator.ir.document import IRDocument
from unihttp_openapi_generator.ir.models import IRAlias, IREnum, IRField, IRModel
from unihttp_openapi_generator.ir.operations import (
    BodyKind,
    IROperation,
    ParamLocation,
)
from unihttp_openapi_generator.ir.types import (
    DATETIME,
    INT,
    IRType,
    Import,
    ListType,
    MappingType,
    OptionalType,
    RefType,
    UnionType,
)

from butcher import naming, overrides
from butcher.overrides import EnumExtras, EnumMember, UnionAlias, UnionFile

_MARKER_BY_LOCATION = {
    ParamLocation.PATH: "Path",
    ParamLocation.QUERY: "Query",
    ParamLocation.HEADER: "Header",
    ParamLocation.COOKIE: "Header",
}
_MARKER_ORDER = ("Header", "Path", "Query", "Body", "Form", "File")

OMIT_MODULE = "maxo.omit"
ERRORS_MODULE = "maxo.errors"
METHOD_BASE_MODULE = "maxo.bot.methods.base"
MARKERS_MODULE = "maxo.bot.methods.markers"
DOC_BASE_URL = "https://dev.max.ru/docs-api"


class ProfileError(Exception):
    """Профиль не может собрать корректный вывод по текущей спеке."""


# --- результат ---------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class Field:
    """Поле модели или параметр метода, уже готовое к печати."""

    name: str
    annotation: str
    description: str | None = None
    omittable: bool = False
    default: str | None = None
    marker: str | None = None
    bare_assignment: bool = False
    """Печатать как ``type = UpdateType.X`` - без аннотации."""
    comment: str | None = None
    """Хвостовой комментарий после объявления поля (``# ...``)."""

    @property
    def optional(self) -> bool:
        """Тип допускает ``None`` - поле рендерится с ``= None``."""
        return self.annotation.endswith(" | None")

    @property
    def unsafe(self) -> bool:
        """Нужно ли `unsafe_*`-свойство: значение может отсутствовать."""
        return (self.omittable or self.optional) and not self.bare_assignment

    @property
    def bare_annotation(self) -> str:
        """Аннотация без ``| None`` - тип возврата `unsafe_*`-свойства."""
        return self.annotation.removesuffix(" | None")


@dataclass(slots=True, frozen=True)
class Model:
    name: str
    base: str
    description: str | None
    field_groups: tuple[tuple[Field, ...], ...]
    """Группы полей: между ними при печати ставится пустая строка."""
    imports: frozenset[Import]
    mixins: tuple[str, ...] = ()
    type_aliases: tuple[tuple[str, str], ...] = ()
    """``(имя, комментарий)`` для ``Имя: TypeAlias = <Класс>`` в конце модуля."""

    @property
    def fields(self) -> tuple[Field, ...]:
        return _flatten(self.field_groups)

    @property
    def module_stem(self) -> str:
        return naming.module_stem(self.name)

    @property
    def bases(self) -> tuple[str, ...]:
        return (self.base, *self.mixins)

    @property
    def exported_names(self) -> tuple[str, ...]:
        return (self.name, *(alias for alias, _ in self.type_aliases))


@dataclass(slots=True, frozen=True)
class Enum:
    name: str
    description: str | None
    members: tuple[EnumMember, ...]
    extras: EnumExtras = field(default_factory=EnumExtras)

    @property
    def module_stem(self) -> str:
        return naming.module_stem(self.name)

    @property
    def exported_names(self) -> tuple[str, ...]:
        return (self.name, *(alias for alias, _ in self.extras.type_aliases))


@dataclass(slots=True, frozen=True)
class Union:
    name: str
    members: tuple[str, ...]
    annotate: bool


@dataclass(slots=True, frozen=True)
class Unions:
    module: str
    aliases: tuple[Union, ...]
    imports: frozenset[Import]

    @property
    def exported_names(self) -> tuple[str, ...]:
        return tuple(alias.name for alias in self.aliases)


@dataclass(slots=True, frozen=True)
class Method:
    name: str
    tag: str
    url: str
    http_method: str
    summary: str | None
    description: str | None
    returns: str
    doc_link: str
    field_groups: tuple[tuple[Field, ...], ...]
    imports: frozenset[Import]

    @property
    def fields(self) -> tuple[Field, ...]:
        return _flatten(self.field_groups)

    @property
    def module_stem(self) -> str:
        return naming.module_stem(self.name)


@dataclass(slots=True, frozen=True)
class MaxoDocument:
    enums: tuple[Enum, ...]
    models: tuple[Model, ...]
    unions: tuple[Unions, ...]
    methods: tuple[Method, ...]


# --- построение --------------------------------------------------------------


class _Profile:
    def __init__(self, document: IRDocument) -> None:
        self._document = document
        self._models: dict[str, IRModel] = {
            decl.name: decl
            for decl in document.declarations
            if isinstance(decl, IRModel)
        }
        self._ir_enums: dict[str, IREnum] = {
            decl.name: decl
            for decl in document.declarations
            if isinstance(decl, IREnum)
        }
        self._aliases: set[str] = {
            decl.name for decl in document.declarations if isinstance(decl, IRAlias)
        }
        self._skipped: set[str] = set()
        self._class_names: dict[str, str] = {}
        self._enums: dict[str, Enum] = {}
        self._tags: dict[str, tuple[str, str, str]] = {}
        self._union_modules: dict[str, str] = {}
        self._used_unions: set[str] = set()

    # -- подготовка --------------------------------------------------------

    def _collect_skipped(self) -> None:
        """Пропуски из таблиц плюс каскад: пропуск базы уносит всех её наследников."""
        self._skipped = set(overrides.SKIP_SCHEMAS) | set(overrides.SKIP_ENUMS)
        changed = True
        while changed:
            changed = False
            for name, model in self._models.items():
                if model.base_model in self._skipped and name not in self._skipped:
                    self._skipped.add(name)
                    changed = True

    def _collect_class_names(self) -> None:
        """Имя класса maxo для каждой схемы: у апдейтов снимается суффикс."""
        for name in self._models:
            if name in self._skipped:
                continue
            self._class_names[name] = (
                name.removesuffix(overrides.UPDATE_CLASS_SUFFIX)
                if self._is_update(name)
                else name
            )

    def _check_aliases(self) -> None:
        unsupported = sorted(
            self._aliases - self._skipped - overrides.INLINE_ALIASES.keys(),
        )
        if unsupported:
            raise ProfileError(
                f"IRAlias {unsupported} не поддерживаются профилем maxo. "
                f"Добавь их в INLINE_ALIASES или реализуй рендеринг.",
            )

    def _is_update(self, name: str) -> bool:
        seen: set[str] = set()
        current: str | None = name
        while current is not None and current not in seen:
            seen.add(current)
            model = self._models.get(current)
            if model is None:
                return False
            if model.base_model == overrides.UPDATE_BASE_SCHEMA:
                return True
            current = model.base_model
        return False

    def _collect_enums(self) -> None:
        """Enum'ы свагера плюс синтезированные из дискриминаторов."""
        for name, ir_enum in self._ir_enums.items():
            if name in self._skipped:
                continue
            members = tuple(
                EnumMember(name=member, value=str(value))
                for member, value in sorted(ir_enum.members, key=lambda item: item[0])
            )
            self._enums[name] = _make_enum(name, ir_enum.description, members)

        for base_name, model in self._models.items():
            if model.discriminator is None or base_name in overrides.SKIP_ENUMS:
                continue
            mapping = {
                tag: subtype
                for tag, subtype in model.discriminator.mapping.items()
                if subtype not in self._skipped
            }
            if not mapping:
                continue
            enum_name = naming.discriminator_enum(base_name)
            members = tuple(
                EnumMember(name=naming.enum_member(tag), value=tag)
                for tag in sorted(mapping)
            )
            self._enums[enum_name] = _make_enum(enum_name, model.description, members)
            property_name = model.discriminator.property_name
            for tag, subtype in mapping.items():
                self._tags[subtype] = (enum_name, property_name, tag)

    def _collect_union_modules(self) -> None:
        for union_file in overrides.UNION_FILES:
            for alias in union_file.aliases:
                self._union_modules[alias.name] = union_file.module

    # -- типы --------------------------------------------------------------

    def _annotate(self, ir_type: IRType, imports: set[Import]) -> str:
        """Аннотация maxo для IR-типа; нужные импорты складываются в `imports`."""
        if isinstance(ir_type, RefType):
            return self._annotate_ref(ir_type.name, imports)
        if isinstance(ir_type, OptionalType):
            return f"{self._annotate(ir_type.inner, imports)} | None"
        if isinstance(ir_type, ListType):
            return f"list[{self._annotate(ir_type.item, imports)}]"
        if isinstance(ir_type, MappingType):
            return f"dict[str, {self._annotate(ir_type.value, imports)}]"
        if isinstance(ir_type, UnionType):
            members = (self._annotate(member, imports) for member in ir_type.members)
            return " | ".join(members)
        # Литералы, примитивы и всё остальное аннотируются одинаково.
        imports.update(ir_type.imports())
        return ir_type.annotation()

    def _annotate_ref(self, name: str, imports: set[Import]) -> str:
        inlined = overrides.INLINE_ALIASES.get(name)
        if inlined is not None:
            return inlined

        union_expression = overrides.BASE_TO_UNION.get(name)
        if union_expression is not None:
            for alias in union_expression.split(" | "):
                module = self._union_modules.get(alias)
                if module is None:
                    message = f"union-алиас {alias!r} не объявлен в UNION_FILES"
                    raise ProfileError(message)
                imports.add(Import(f"{naming.TYPES_PACKAGE}.{module}", alias))
                self._used_unions.add(alias)
            return union_expression

        if name in self._enums:
            imports.add(Import(naming.enum_module(name), name))
            return name

        if name in self._skipped:
            raise ProfileError(
                f"тип {name!r} пропущен через SKIP_SCHEMAS, но на него ссылаются. "
                f"Убери его из таблицы или добавь запись в BASE_TO_UNION.",
            )

        class_name = self._class_names.get(name, name)
        imports.add(Import(naming.type_module(class_name), class_name))
        return class_name

    @staticmethod
    def _is_timestamp(ir_field: IRField) -> bool:
        """int64 с описанием про время - в maxo это `datetime`."""
        if ir_field.constraints.get("format") != "int64":
            return False
        return _has_timestamp_hint(ir_field.description)

    def _field_type(self, ir_field: IRField) -> IRType:
        return DATETIME if self._is_timestamp(ir_field) else ir_field.type

    @staticmethod
    def _parameter_type(ir_type: IRType, description: str | None) -> IRType:
        """
        То же правило для параметров и полей тела запроса.

        У `IRParameter`/`IRBodyField` нет `constraints`, поэтому формат int64 от
        int32 не отличить - хватает того, что тип целочисленный, а описание
        говорит про время.
        """
        if not _has_timestamp_hint(description):
            return ir_type
        if _is_int(ir_type):
            return DATETIME
        if isinstance(ir_type, OptionalType) and _is_int(ir_type.inner):
            return OptionalType(DATETIME)
        return ir_type

    # -- модели ------------------------------------------------------------

    def _build_models(self) -> tuple[Model, ...]:
        models: list[Model] = []
        for name, ir_model in self._models.items():
            if name in self._skipped or name in overrides.REPLACED_BASES:
                continue
            models.append(self._build_model(name, ir_model))
        return tuple(models)

    def _build_model(self, name: str, ir_model: IRModel) -> Model:
        imports: set[Import] = set()
        is_update = self._is_update(name)
        class_name = self._class_names[name]

        base_override = overrides.MODEL_BASE_OVERRIDES.get(class_name)
        replaced = overrides.REPLACED_BASES.get(ir_model.base_model or "")
        if base_override is not None:
            base = base_override
            imports.add(Import(naming.type_module(base), base))
        elif ir_model.base_model is None:
            base = overrides.ROOT_BASE_CLASS
            imports.add(Import(f"{naming.TYPES_PACKAGE}.base", base))
        elif replaced is not None:
            base = replaced
            imports.add(Import(f"{naming.TYPES_PACKAGE}.base", base))
        else:
            base = self._class_names[ir_model.base_model]
            imports.add(Import(naming.type_module(base), base))

        mixins = overrides.CLASS_MIXINS.get(class_name, ())
        for mixin in mixins:
            imports.add(Import(overrides.FACADES_MODULE, mixin))

        fields = tuple(
            self._build_model_field(name, ir_field, imports, is_update=is_update)
            for ir_field in ir_model.fields
        )
        self._add_field_helpers(fields, imports)
        return Model(
            name=class_name,
            base=base,
            description=ir_model.description,
            field_groups=_model_field_groups(fields),
            imports=frozenset(imports),
            mixins=mixins,
            type_aliases=overrides.TYPE_ALIASES.get(class_name, ()),
        )

    def _build_model_field(
        self,
        owner: str,
        ir_field: IRField,
        imports: set[Import],
        *,
        is_update: bool,
    ) -> Field:
        tag = self._tags.get(owner)
        if tag is not None and ir_field.wire_name == tag[1]:
            return self._build_tag_field(tag, imports, is_update=is_update)

        base_tag = self._base_discriminator(owner)
        if base_tag is not None and ir_field.wire_name == base_tag[1]:
            # Поле-дискриминатор самой базы: `type: AttachmentType`.
            enum_name = base_tag[0]
            imports.add(Import(naming.enum_module(enum_name), enum_name))
            return Field(
                name=ir_field.name,
                annotation=enum_name,
                description=ir_field.description,
            )

        class_name = self._class_names[owner]
        override = overrides.MODEL_FIELD_OVERRIDES.get((class_name, ir_field.name))
        field_type = self._field_type(ir_field)
        if override is not None and override.ref is not None:
            field_type = RefType(override.ref)
        annotation = self._annotate(field_type, imports)
        # Дефолты свагера игнорируем: необязательное поле - это `Omitted()`.
        omittable = not ir_field.required
        comment: str | None = None
        if override is not None:
            if override.annotation is not None:
                annotation = override.annotation
            if override.omittable is not None:
                omittable = override.omittable
            comment = override.comment
        return Field(
            name=ir_field.name,
            annotation=annotation,
            description=ir_field.description,
            omittable=omittable,
            comment=comment,
        )

    def _base_discriminator(self, name: str) -> tuple[str, str] | None:
        model = self._models.get(name)
        if model is None or model.discriminator is None:
            return None
        enum_name = naming.discriminator_enum(name)
        if enum_name not in self._enums:
            # Все подтипы базы пропущены - enum не собрался, типизировать поле
            # им нельзя: получился бы импорт несуществующего модуля.
            return None
        return enum_name, model.discriminator.property_name

    def _build_tag_field(
        self,
        tag: tuple[str, str, str],
        imports: set[Import],
        *,
        is_update: bool,
    ) -> Field:
        enum_name, property_name, value = tag
        imports.add(Import(naming.enum_module(enum_name), enum_name))
        default = f"{enum_name}.{naming.enum_member(value)}"
        # У апдейтов тип объявлен `ClassVar` в `MaxUpdate`, поэтому наследник
        # только присваивает значение.
        if is_update:
            return Field(
                name=overrides.UPDATE_TYPE_ATTR,
                annotation=enum_name,
                default=default,
                bare_assignment=True,
            )
        return Field(name=property_name, annotation=enum_name, default=default)

    @staticmethod
    def _add_field_helpers(fields: tuple[Field, ...], imports: set[Import]) -> None:
        if any(f.omittable for f in fields):
            imports.add(Import(OMIT_MODULE, "Omittable"))
            imports.add(Import(OMIT_MODULE, "Omitted"))
        if any(f.unsafe for f in fields):
            imports.add(Import(OMIT_MODULE, "is_defined"))
            imports.add(Import(ERRORS_MODULE, "AttributeIsEmptyError"))

    # -- union-алиасы ------------------------------------------------------

    def _build_unions(self) -> tuple[Unions, ...]:
        files = (self._build_union_file(item) for item in overrides.UNION_FILES)
        return tuple(item for item in files if item.aliases)

    def _build_union_file(self, union_file: UnionFile) -> Unions:
        imports: set[Import] = set()
        declared: set[str] = set()
        aliases: list[Union] = []
        for alias in union_file.aliases:
            members = self._union_members(alias, declared)
            if not members:
                continue
            for member in members:
                if member in declared:
                    continue  # алиас из этого же файла - импорт не нужен
                imports.add(Import(naming.type_module(member), member))
            declared.add(alias.name)
            aliases.append(
                Union(name=alias.name, members=members, annotate=alias.annotate),
            )
        return Unions(
            module=union_file.module,
            aliases=tuple(aliases),
            imports=frozenset(imports),
        )

    def _union_members(self, alias: UnionAlias, declared: set[str]) -> tuple[str, ...]:
        generated = set(self._class_names.values())
        # `include` перечисляет классы и объявленные выше алиасы того же файла;
        # то, чего в спеке нет, молча выпадает.
        members: list[str] = [
            name for name in alias.include if name in declared or name in generated
        ]
        if alias.base is not None:
            model = self._models.get(alias.base)
            if model is None:
                # Спека не описывает эту базу - алиас просто не собирается.
                return ()
            if model.discriminator is None:
                raise ProfileError(
                    f"{alias.base!r} перестала быть дискриминированной базой: "
                    f"алиас {alias.name!r} собрать нечем.",
                )
            subtypes = [
                self._class_names[subtype]
                for subtype in model.discriminator.mapping.values()
                if subtype not in self._skipped and subtype not in alias.exclude
            ]
            members.extend(sorted(subtypes) if alias.sort else subtypes)
        return tuple(members)

    # -- методы ------------------------------------------------------------

    def _build_methods(self) -> tuple[Method, ...]:
        return tuple(
            self._build_method(operation)
            for operation in self._document.operations
            if operation.class_name not in overrides.SKIP_OPERATIONS
        )

    def _build_method(self, operation: IROperation) -> Method:
        imports: set[Import] = {Import(METHOD_BASE_MODULE, "MaxoMethod")}
        returns = (
            self._annotate(operation.return_type, imports)
            if operation.return_type is not None
            else "None"
        )
        fields = self._build_method_fields(operation, imports)
        self._add_field_helpers(fields, imports)
        for marker in {f.marker for f in fields if f.marker}:
            imports.add(Import(MARKERS_MODULE, marker))
        return Method(
            name=operation.class_name,
            tag=operation.tag,
            url=_method_url(operation),
            http_method=operation.http_method.lower(),
            summary=operation.summary,
            description=operation.description,
            returns=returns,
            doc_link=_doc_link(operation),
            field_groups=_method_field_groups(fields),
            imports=frozenset(imports),
        )

    def _method_field_type(
        self,
        class_name: str,
        field_name: str,
        ir_type: IRType,
        description: str | None,
        imports: set[Import],
    ) -> str:
        # Замена обходит генератор, чтобы не тянуть его импорты (лишний `Any`).
        override = overrides.METHOD_FIELD_TYPES.get((class_name, field_name))
        if override is not None:
            return override
        return self._annotate(self._parameter_type(ir_type, description), imports)

    def _build_method_fields(
        self,
        operation: IROperation,
        imports: set[Import],
    ) -> tuple[Field, ...]:
        fields: list[Field] = []
        for parameter in operation.parameters:
            description = overrides.METHOD_FIELD_DESCRIPTIONS.get(
                (operation.class_name, parameter.name),
                parameter.description,
            )
            annotation = self._method_field_type(
                operation.class_name,
                parameter.name,
                parameter.type,
                description,
                imports,
            )
            fields.append(
                Field(
                    name=parameter.name,
                    annotation=annotation,
                    description=description,
                    # Дефолты свагера игнорируем: необязательный параметр - `Omitted()`.
                    omittable=not parameter.required,
                    marker=_MARKER_BY_LOCATION[parameter.location],
                ),
            )

        body = operation.body
        if body is None:
            return tuple(fields)

        if body.json_type is not None:
            raise ProfileError(
                f"метод {operation.class_name!r} использует сырое JSON-тело, "
                f"которое unihttp не умеет отправлять без обёртки",
            )

        for body_field in body.fields:
            description = overrides.METHOD_FIELD_DESCRIPTIONS.get(
                (operation.class_name, body_field.name),
                body_field.description,
            )
            annotation = self._method_field_type(
                operation.class_name,
                body_field.name,
                body_field.type,
                description,
                imports,
            )
            if body_field.is_file:
                marker = "File"
                imports.update(body_field.type.imports())
            else:
                marker = "Body" if body.kind is BodyKind.JSON else "Form"
            fields.append(
                Field(
                    name=body_field.name,
                    annotation=annotation,
                    description=description,
                    omittable=not body_field.required,
                    marker=marker,
                ),
            )
        return tuple(fields)

    # -- сборка ------------------------------------------------------------

    def build(self) -> MaxoDocument:
        self._collect_skipped()
        self._check_aliases()
        self._collect_class_names()
        self._collect_enums()
        self._collect_union_modules()
        unions = self._build_unions()
        document = MaxoDocument(
            enums=tuple(sorted(self._enums.values(), key=lambda item: item.name)),
            models=self._build_models(),
            unions=unions,
            methods=self._build_methods(),
        )
        self._check_union_imports(unions)
        return document

    def _check_union_imports(self, unions: tuple[Unions, ...]) -> None:
        """
        Каждый алиас, на который сослались аннотации, должен попасть в вывод.

        Алиас без членов молча выпадает из union-файла, а `_annotate_ref` всё
        равно импортирует его в каждую ссылающуюся модель - получился бы
        `ImportError` на импорте `maxo`.
        """
        generated = {name for item in unions for name in item.exported_names}
        missing = sorted(self._used_unions - generated)
        if missing:
            raise ProfileError(
                f"union-алиасы {missing} используются в аннотациях, но не "
                f"собрались. Проверь UNION_FILES и спеку.",
            )


def _model_field_groups(fields: tuple[Field, ...]) -> tuple[tuple[Field, ...], ...]:
    """С дефолтом, затем обязательные, nullable и omittable - внутри по алфавиту."""
    groups: list[list[Field]] = [[], [], [], []]
    for item in fields:
        if item.default is not None:
            groups[0].append(item)
        elif item.omittable:
            groups[3].append(item)
        elif item.optional:
            groups[2].append(item)
        else:
            groups[1].append(item)
    return tuple(tuple(sorted(group, key=_by_name)) for group in groups if group)


def _method_field_groups(fields: tuple[Field, ...]) -> tuple[tuple[Field, ...], ...]:
    """По маркерам, внутри маркера - обязательные, nullable, omittable."""
    groups: list[tuple[Field, ...]] = []
    for marker in _MARKER_ORDER:
        group = [item for item in fields if item.marker == marker]
        if not group:
            continue
        required = sorted(
            (f for f in group if not f.omittable and not f.optional),
            key=_by_name,
        )
        optional = sorted(
            (f for f in group if not f.omittable and f.optional),
            key=_by_name,
        )
        omittable = sorted((f for f in group if f.omittable), key=_by_name)
        groups.append((*required, *optional, *omittable))
    return tuple(groups)


def _is_int(ir_type: IRType) -> bool:
    """Целое число - как напрямую, так и через `INLINE_ALIASES` (схема `bigint`)."""
    if ir_type == INT:
        return True
    return (
        isinstance(ir_type, RefType)
        and overrides.INLINE_ALIASES.get(ir_type.name) == "int"
    )


def _has_timestamp_hint(description: str | None) -> bool:
    text = (description or "").lower()
    return any(
        re.search(rf"\b{re.escape(hint)}\b", text) for hint in overrides.TIMESTAMP_HINTS
    )


def _by_name(item: Field) -> str:
    return item.name


def _flatten(field_groups: tuple[tuple[Field, ...], ...]) -> tuple[Field, ...]:
    return tuple(item for group in field_groups for item in group)


def _make_enum(
    name: str,
    description: str | None,
    members: tuple[EnumMember, ...],
) -> Enum:
    """Собрать `Enum` с ручными добавками из `ENUM_EXTRAS`."""
    return Enum(
        name=name,
        description=description,
        members=members,
        extras=overrides.ENUM_EXTRAS.get(name, EnumExtras()),
    )


def _method_url(operation: IROperation) -> str:
    """URL для `__url__`: без ведущего слэша и с path-параметрами в snake_case."""
    url = operation.path.lstrip("/")
    for parameter in operation.parameters:
        if parameter.location is ParamLocation.PATH:
            url = url.replace(f"{{{parameter.wire_name}}}", f"{{{parameter.name}}}")
    return url


def _doc_link(operation: IROperation) -> str:
    # `{chatId}` в пути ссылки на доку записывается как `-chatId-`.
    path = re.sub(r"\{([^}]+)\}", r"-\1-", operation.path.lstrip("/"))
    return f"{DOC_BASE_URL}/methods/{operation.http_method.upper()}/{path}"


def build_profile(document: IRDocument) -> MaxoDocument:
    """Собрать maxo-представление документа."""
    return _Profile(document).build()

import functools
from collections.abc import Awaitable, Callable, Coroutine, Mapping
from inspect import Parameter, signature
from typing import TypeVar

_ReturnT = TypeVar("_ReturnT")


def inline_ctx(
    func: Callable[..., Awaitable[_ReturnT]],
) -> Callable[..., Coroutine[object, object, _ReturnT]]:
    parameters = tuple(signature(func).parameters.values())
    passed_parameters = tuple(
        parameter.name
        for parameter in parameters
        if parameter.name in {"self", "update"}
        and parameter.kind
        in {Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD}
    )
    inline_parameters = tuple(
        parameter.name
        for parameter in parameters
        if parameter.kind in {Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY}
        and parameter.name not in {"self", "update", "ctx"}
    )
    passes_ctx = any(parameter.name == "ctx" for parameter in parameters)

    @functools.wraps(func)
    async def wrapper(*args: object, **kwargs: object) -> _ReturnT:
        if "ctx" in kwargs:
            ctx = kwargs["ctx"]
        elif args:
            ctx = args[-1]
        else:
            msg = "Не передан обязательный параметр ctx"
            raise TypeError(msg)

        if not isinstance(ctx, Mapping):
            msg = "Параметр ctx должен быть отображением"
            raise TypeError(msg)

        inline_kwargs = {name: ctx[name] for name in inline_parameters if name in ctx}
        if passes_ctx:
            inline_kwargs["ctx"] = ctx
        return await func(*args[: len(passed_parameters)], **inline_kwargs)

    return wrapper

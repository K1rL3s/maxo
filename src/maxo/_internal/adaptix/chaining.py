from typing import Any, cast

from adaptix import Chain, Dumper, Loader, Provider
from adaptix._internal.morphing.json_schema.providers import (
    EraseJSONSchema,
    JSONSchemaOverrideProvider,
)
from adaptix._internal.morphing.request_cls import DumperRequest, LoaderRequest
from adaptix._internal.provider.essential import Mediator, Request, RequestHandler
from adaptix._internal.provider.facade.provider import bound
from adaptix._internal.provider.loc_stack_filtering import Pred
from adaptix._internal.provider.provider_wrapper import ChainingProvider, ConcatProvider
from adaptix._internal.provider.value_provider import ValueProvider


class CachingChainingProvider(ChainingProvider):
    """
    `ChainingProvider`, переиспользующий одну и ту же функцию-композицию.

    Штатный `ChainingProvider` на каждый запрос создаёт новый объект
    `chain_processor`. Adaptix кеширует сгенерированный код модели по набору
    загрузчиков её полей, поэтому свежая функция на каждое поле промахивается
    мимо кеша: одна и та же модель компилируется заново на каждом пути, по
    которому до неё можно дойти. На типах MAX это давало 551 скомпилированную
    функцию вместо 250 и лишние мегабайты RSS.

    Композиция чистая, для одной пары функций достаточно одного объекта.
    Кешируем её через `Mediator.cached_call`, то есть в `_call_cache` конкретного
    retort: так кеш живёт и умирает вместе с retort, а не вместе с провайдером,
    который в maxo объявлен на уровне модуля.
    """

    def _wrap_handler[ResponseT, RequestT: Request[Any]](
        self,
        handler: RequestHandler[ResponseT, RequestT],
    ) -> RequestHandler[ResponseT, RequestT]:
        def chaining_handler(
            mediator: Mediator[ResponseT],
            request: RequestT,
        ) -> ResponseT:
            current_processor = handler(mediator, request)
            next_processor = mediator.provide_from_next()

            if self._chain == Chain.FIRST:
                first, second = current_processor, next_processor
            elif self._chain == Chain.LAST:
                first, second = next_processor, current_processor
            else:
                raise ValueError(self._chain)

            # `ChainingProvider._make_chain` в adaptix не аннотирован,
            # поэтому `cached_call` выводится как `Any`.
            processor = mediator.cached_call(self._make_chain, first, second)
            return cast("ResponseT", processor)

        return chaining_handler


def _caching_chain(
    pred: Pred,
    request_cls: type[Request[Any]],
    func: Loader[Any] | Dumper[Any],
    chain: Chain,
) -> Provider:
    return bound(
        pred,
        ConcatProvider(
            CachingChainingProvider(chain, ValueProvider(request_cls, func)),
            JSONSchemaOverrideProvider(override=EraseJSONSchema()),
        ),
    )


def chained_loader(pred: Pred, func: Loader[Any], chain: Chain) -> Provider:
    """Аналог `adaptix.loader(..., chain=...)` с кешированием композиции."""
    return _caching_chain(pred, LoaderRequest, func, chain)


def chained_dumper(pred: Pred, func: Dumper[Any], chain: Chain) -> Provider:
    """Аналог `adaptix.dumper(..., chain=...)` с кешированием композиции."""
    return _caching_chain(pred, DumperRequest, func, chain)

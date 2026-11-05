import maxo
from maxo import bot as bot_package, errors, exceptions, filters, methods
from maxo.__meta__ import __version__
from maxo.bot.bot import Bot
from maxo.bot.methods import SendMessage
from maxo.enums import ChatType
from maxo.routing import filters as routing_filters
from maxo.routing.ctx import Ctx
from maxo.routing.dispatcher import Dispatcher
from maxo.routing.interfaces.middleware import BaseMiddleware
from maxo.routing.routers.simple import Router
from maxo.types import MessageCreated
from maxo.utils.text_decorations import html_decoration, markdown_decoration


def test_top_level_exports() -> None:
    assert maxo.Bot is Bot
    assert maxo.Dispatcher is Dispatcher
    assert maxo.Router is Router
    assert maxo.Ctx is Ctx
    assert maxo.BaseMiddleware is BaseMiddleware
    assert maxo.__version__ == __version__


def test_top_level_text_decorations() -> None:
    assert maxo.html is html_decoration
    assert maxo.md is markdown_decoration


def test_top_level_modules() -> None:
    assert maxo.types.MessageCreated is MessageCreated
    assert maxo.methods.SendMessage is SendMessage
    assert maxo.enums.ChatType is ChatType


def test_methods_module_mirrors_bot_methods() -> None:
    # Список имен в `maxo.methods` продублирован вручную, поэтому проверяем
    # и совпадение состава, и то, что каждое имя ведет на тот же объект.
    assert methods.__all__
    assert set(methods.__all__) == set(bot_package.methods.__all__)

    for name in methods.__all__:
        assert getattr(methods, name) is getattr(bot_package.methods, name)


def test_filters_module_mirrors_routing_filters() -> None:
    # Список имен в `maxo.filters` продублирован вручную, поэтому проверяем
    # и совпадение состава, и то, что каждое имя ведет на тот же объект.
    assert filters.__all__
    assert set(filters.__all__) == set(routing_filters.__all__)

    for name in filters.__all__:
        assert getattr(filters, name) is getattr(routing_filters, name)


def test_exceptions_module_mirrors_errors() -> None:
    assert exceptions.__all__
    assert set(exceptions.__all__) == set(errors.__all__)

    for name in exceptions.__all__:
        assert getattr(exceptions, name) is getattr(errors, name)


def test_delete_admins_keeps_singular_aliases() -> None:
    delete_admins = getattr(methods, "DeleteAdmins", None)

    assert delete_admins is not None
    assert methods.DeleteAdmin is delete_admins
    assert getattr(Bot, "delete_admins", None) is Bot.delete_admin


.. rst-class:: center

   .. image:: _static/maxo-logo.png
      :width: 200px
      :height: 200px
      :alt: maxo - асинхронный Python-фреймворк для ботов мессенджера MAX (max.ru)
      :align: center

==========================================================
maxo - асинхронный Python-фреймворк для ботов MAX (max.ru)
==========================================================

.. rst-class:: center

   |License| |Status| |PyPI| |Downloads| |Stars| |Versions| |Tests|

.. |License| image:: https://img.shields.io/pypi/l/maxo.svg?style=flat
   :target: https://github.com/K1rL3s/maxo/blob/master/LICENSE
   :alt: License

.. |Status| image:: https://img.shields.io/pypi/status/maxo.svg?style=flat
   :target: https://pypi.org/project/maxo/
   :alt: Status

.. |PyPI| image:: https://img.shields.io/pypi/v/maxo?label=pypi&style=flat
   :target: https://pypi.org/project/maxo/
   :alt: PyPI

.. |Downloads| image:: https://img.shields.io/pypi/dm/maxo?style=flat
   :target: https://pypi.org/project/maxo/
   :alt: Downloads

.. |Stars| image:: https://img.shields.io/github/stars/K1rL3s/maxo?style=flat
   :target: https://github.com/K1rL3s/maxo/stargazers
   :alt: GitHub Repo stars

.. |Versions| image:: https://img.shields.io/pypi/pyversions/maxo.svg?style=flat
   :target: https://pypi.org/project/maxo/
   :alt: Supported python versions

.. |Tests| image:: https://img.shields.io/github/actions/workflow/status/K1rL3s/maxo/analyze.yml?style=flat&label=tests
   :target: https://github.com/K1rL3s/maxo/actions
   :alt: Tests

.. rst-class:: lead

   Асинхронный Python-фреймворк для разработки `ботов <https://dev.max.ru/docs>`_ в `MAX <https://max.ru>`_

.. container:: buttons

   :doc:`pages/getting-started`
   `GitHub <https://github.com/K1rL3s/maxo>`_

Основные возможности:

.. grid:: 1 1 2 2
   :class-row: surface
   :padding: 0
   :gutter: 2

   .. grid-item-card:: :octicon:`zap` Асинхронность
      :link: pages/getting-started
      :link-type: doc

      Полностью асинхронный фреймворк, построенный на базе ``aiohttp`` и ``unihttp``.

   .. grid-item-card:: :octicon:`shield-check` Строгая типизация
      :link: pages/getting-started
      :link-type: doc

      100% покрытие типами. Использует ``adaptix`` для валидации данных и сериализации.

   .. grid-item-card:: :octicon:`comment-discussion` Диалоги
      :link: pages/getting-started
      :link-type: doc

      Мощная система диалогов, портированная из ``aiogram_dialog``.
      Создавайте сложные сценарии взаимодействия с пользователями легко и просто.

   .. grid-item-card:: :octicon:`plug` Интеграции
      :link: pages/getting-started
      :link-type: doc

      Поддержка Dependency Injection через ``dishka``, фильтрация с ``magic_filter``
      и работа с ``redis`` из коробки.

   .. grid-item-card:: :octicon:`rocket` Современный Python
      :link: pages/getting-started
      :link-type: doc

      Разработан для Python 3.12+. Использует все преимущества последних версий языка.

   .. grid-item-card:: :octicon:`book` Документация
      :link: pages/getting-started
      :link-type: doc

      Подробная документация и примеры для быстрого старта.


Если у вас есть вопросы, вы можете задать их в Телеграме `@maxo_py <https://t.me/maxo_py>`_ или `MAX <https://max.ru/join/rwJmWA4B5AipBiJdWRkORGjxFmqnJPUhJbQxxmscrnc>`__

Contributors
------------
Люди, которые сделали этот проект возможным.

.. container:: rounded-image

    .. contributors:: K1rL3s/maxo
        :avatars:
        :contributions:


.. toctree::
   :maxdepth: 2
   :caption: Начало работы
   :hidden:

   pages/getting-started

.. toctree::
   :maxdepth: 2
   :caption: Обработка событий
   :hidden:

   pages/event-handling/index
   pages/event-handling/routers
   pages/event-handling/filters
   pages/event-handling/middlewares
   pages/event-handling/handlers
   pages/event-handling/fsm
   pages/event-handling/facades
   pages/event-handling/errors
   pages/event-handling/signals
   pages/event-handling/long-polling
   pages/event-handling/webhooks
   pages/event-handling/bot-mixin

.. toctree::
   :maxdepth: 2
   :caption: Диалоги (maxo.dialogs)
   :hidden:

   pages/dialogs/index
   pages/dialogs/quickstart
   pages/dialogs/windows_and_dialogs
   pages/dialogs/widgets
   pages/dialogs/transitions
   pages/dialogs/data_and_context
   pages/dialogs/background_manager
   pages/dialogs/testing
   pages/dialogs/preview

.. toctree::
   :maxdepth: 2
   :caption: API Reference
   :hidden:

   pages/botapi/index

.. toctree::
   :maxdepth: 2
   :caption: Полезные заметки
   :hidden:

   pages/useful_notes

.. toctree::
   :maxdepth: 2
   :caption: Утилиты (maxo.utils)
   :hidden:

   pages/utils/link

.. toctree::
   :maxdepth: 1
   :caption: Релизы
   :hidden:

   pages/changelog

==============================
Превью диалогов и переходов
==============================

``maxo.dialogs.tools`` предоставляет два инструмента для визуальной отладки
диалогов без запуска бота: HTML-превью окон и PNG-диаграмму переходов между состояниями.

HTML-превью диалога
====================

HTML-превью отображает все окна диалога в браузере: текст, кнопки и медиа.
Удобно для ревью UI и проверки текстов без запуска бота.

Подготовка: ``preview_data``
-----------------------------

Окна с геттерами требуют данных для рендеринга. Добавьте параметр ``preview_data``
в ``Window`` - словарь с теми же ключами, которые возвращает геттер:

.. code-block:: python

    from maxo.dialogs import Window
    from maxo.dialogs.widgets.text import Format
    from maxo.dialogs.widgets.kbd import Button
    from maxo.dialogs.widgets.text import Const

    Window(
        Format("Привет, {name}!"),
        Button(Const("Продолжить"), id="next"),
        state=MySG.greeting,
        preview_data={"name": "Разработчик"},
    )

Генерация HTML-файла
---------------------

.. code-block:: python

    import asyncio
    from maxo.dialogs.tools.preview import render_preview

    asyncio.run(render_preview(router, "preview.html"))

Откройте `preview.html` в браузере - каждый диалог отображается как секция
с превью всех своих окон. Кнопки кликабельны и переключают окна:

.. image:: /_static/preview-demo.gif
   :alt: HTML-превью диалога
   :width: 520px

Для получения HTML-строки без записи в файл:

.. code-block:: python

    from maxo.dialogs.tools.preview import render_preview_content

    html = asyncio.run(render_preview_content(router, simulate_events=True))

Диаграмма переходов (PNG)
=========================

Диаграмма визуализирует состояния и переходы между ними как граф.
Каждый диалог - отдельная группа. Рёбра показывают тип перехода по цвету:

- **Зелёный** - ``Start`` (запуск нового диалога)
- **Синий** - ``SwitchTo`` / ``Next`` (переход в другое окно)
- **Серый** - ``Back`` / ``Cancel`` (возврат)

Требования
-----------

.. code-block:: bash

    pip install "maxo[preview]"     # или: uv add "maxo[preview]"
    brew install graphviz           # macOS
    # apt-get install graphviz      # Linux

Генерация диаграммы
--------------------

.. code-block:: python

    from maxo.dialogs.tools.transitions import render_transitions

    render_transitions(router, title="Мой бот", filename="transitions")
    # Сохраняет transitions.png в текущую директорию

.. image:: /_static/transitions-example.png
   :alt: Диаграмма переходов
   :width: 600px

Параметры:

- ``router`` - ``Dispatcher``, ``Router`` или ``Dialog``
- ``title`` - заголовок диаграммы
- ``filename`` - имя файла без расширения
- ``format`` - формат вывода (``"png"``, ``"svg"`` и др.)

Хинты для динамических переходов
----------------------------------

Переходы, реализованные в коде (не через виджеты ``Start``/``SwitchTo``),
невидимы для статического анализа. Подскажите их с помощью ``preview_add_transitions``:

.. code-block:: python

    from maxo.dialogs.widgets.kbd import Start

    Window(
        Const("Выберите действие"),
        state=MySG.menu,
        # Переход в EditSG.main происходит в коде - указываем явно для диаграммы
        preview_add_transitions=[Start(Const(""), id="_hint", state=EditSG.main)],
    )

Web-превью
==========

Команда ``maxo-dialog-preview`` запускает локальный веб-сервер с обоими инструментами
сразу - HTML-превью и диаграмма переходов доступны в браузере без генерации файлов.

.. code-block:: bash

    maxo-dialog-preview path/to/module.py:router_variable

Откройте в браузере:

- ``http://127.0.0.1:9876/`` - HTML-превью всех окон
- ``http://127.0.0.1:9876/transitions`` - PNG-диаграмма переходов

.. note::

    Для работы ``/transitions`` требуется установленный ``graphviz``
    и пакет ``maxo[preview]``.

Полный пример
=============

Рабочий пример с диалогом из двух групп состояний: демонстрирует генерацию
HTML-превью и PNG-диаграммы переходов, а также настройку роутера для команды
``maxo-dialog-preview``:
:download:`examples/dialogs_preview.py <../../../examples/dialogs_preview.py>`

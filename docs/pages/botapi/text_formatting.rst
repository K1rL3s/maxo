=======================
Форматирование текста
=======================

В этой странице описаны способы форматирования текста сообщений в MAX.

Поддерживаемые форматы
=======================

Подробная документация по форматированию: `dev.max.ru/docs <https://dev.max.ru/docs>`_.

В таблице перечислены все поддерживаемые элементы форматирования:

.. list-table::
   :header-rows: 1
   :widths: 20 30 25 25

   * - Элемент
     - HTML
     - Markdown
     - Примечание
   * - Жирный
     - ``<b>текст</b>``
     - ``**текст**``
     -
   * - Курсив
     - ``<i>текст</i>``
     - ``_текст_``
     -
   * - Подчёркнутый
     - ``<u>текст</u>``
     - ``++текст++``
     -
   * - Зачёркнутый
     - ``<s>текст</s>``
     - ``~~текст~~``
     -
   * - Заголовок
     - ``<h1>текст</h1>``
     - ``# текст``
     - только ``h1``; не задокументирован, работает
   * - Выделение
     - ``<mark>текст</mark>``
     - ``^^текст^^``
     - не отображается в web-версии; не задокументирован, работает
   * - Моноширинный
     - ``<code>текст</code>``
     - ```текст```
     - не отображается в web-версии
   * - Цитата
     - ``<blockquote>текст</blockquote>``
     - ``> текст``
     - не задокументирован, работает
   * - Ссылка
     - ``<a href="url">текст</a>``
     - ``[текст](url)``
     -
   * - Упоминание
     - ``<a href="max://user/ID">Полное имя</a>``
     - ``[Полное имя](max://user/ID)``
     - текст ссылки должен быть полным именем

.. note::

   ``<blockquote>`` не упомянут в официальной документации MAX, однако работает.

   ``<code>`` и ``<pre>`` (моноширинный) не отображаются в web-версии клиента.

.. note::

   Упоминание работает только если текст ссылки является полным именем пользователя.

   * ``<a href="max://user/1234567890">Иван Иванов</a>`` - сработает
   * ``<a href="max://user/1234567890">Любой другой текст</a>`` - нет

TextFormat
==========

``TextFormat`` определяет режим форматирования при отправке текста.

.. code-block:: python

    from maxo.enums import TextFormat
    from maxo.routing.updates import MessageCreated

    @router.message_created()
    async def handler(message: MessageCreated):
        await message.answer_text("<b>Привет!</b>", format=TextFormat.HTML)
        await message.answer_text("**Привет!**", format=TextFormat.MARKDOWN)

Text API (``maxo.utils.formatting``)
=====================================

Модуль ``maxo.utils.formatting`` позволяет составлять форматированные сообщения программно,
без написания HTML или Markdown строк вручную.

Классы разметки
---------------

* ``Text`` - базовый контейнер, принимает произвольные узлы
* ``Bold``, ``Italic``, ``Underline``, ``Strikethrough``, ``Monospaced``, ``BlockQuote``, ``Heading``, ``Highlighted`` - обёртки форматирования
* ``Link(*body, url="https://...")`` - ссылка
* ``Mention("Полное имя", user_id=123)`` - упоминание (текст должен быть полным именем)

.. code-block:: python

    from maxo.utils.formatting import Bold, Italic, Link, Mention

    text = Bold("Важное ", Italic("сообщение"), "!")
    link = Link("Библиотека maxo", url="https://github.com/K1rL3s/maxo")
    mention = Mention("Иван Иванов", user_id=1234567890)

Рендеринг и отправка
---------------------

Для отправки нужно сконвертировать ``Text`` объект в строку через ``.as_html()`` или ``.as_markdown()``:

.. code-block:: python

    from maxo.enums import TextFormat
    from maxo.routing.updates import MessageCreated
    from maxo.utils.formatting import Bold, Italic

    @router.message_created()
    async def handler(message: MessageCreated):
        text = Bold("Привет, ", Italic("мир"), "!")

        # HTML
        await message.answer_text(text.as_html(), format=TextFormat.HTML)

        # Markdown
        await message.answer_text(text.as_markdown(), format=TextFormat.MARKDOWN)

Метод ``.as_kwargs()`` возвращает ``{"text": "...", "format": None}`` - только текст без разметки
(entities не передаются). Подходит для отправки содержимого ``Text`` объекта как plain text.

Вспомогательные функции
------------------------

* ``as_line(*items, end="\n", sep="")`` - строка с разделителем и ``\n`` в конце
* ``as_list(*items, sep="\n")`` - элементы через ``\n``
* ``as_marked_list(*items, marker="- ")`` - список с маркером
* ``as_numbered_list(*items, start=1, fmt="{}. ")`` - нумерованный список
* ``as_section(title, *body)`` - секция с заголовком
* ``as_marked_section(title, *body, marker="- ")`` - секция с маркированным списком
* ``as_numbered_section(title, *body, start=1, fmt="{}. ")`` - секция с нумерованным списком
* ``as_key_value(key, value)`` - строка вида ``<b>key:</b> value``

.. code-block:: python

    from maxo.enums import TextFormat
    from maxo.routing.updates import MessageCreated
    from maxo.utils.formatting import Bold, as_key_value, as_marked_list, as_section

    @router.message_created()
    async def handler(message: MessageCreated):
        report = as_section(
            Bold("Отчёт"),
            as_key_value("Статус", "активен"),
            as_marked_list("Пункт 1", "Пункт 2", "Пункт 3"),
        )
        await message.answer_text(report.as_html(), format=TextFormat.HTML)

Проверка контакта
=================

Когда пользователь делится своим номером через кнопку ``request_contact``,
в ``ContactAttachmentPayload`` приходят ``vcf_info`` и ``hash``. ``hash`` - это
HMAC-SHA256 от ``vcf_info`` с токеном бота в качестве ключа, в hex. Совпадение
подтверждает, что номер привязан к аккаунту отправителя в MAX. У контакта,
отправленного из меню вложений или пересланного, ``hash`` нет, и проверка
возвращает ``False``.

.. code-block:: python

    from maxo import Bot, Router
    from maxo.types import MessageCreated
    from maxo.utils.contact import check_contact_hash

    router = Router()


    @router.message_created()
    async def on_message(update: MessageCreated, bot: Bot) -> None:
        contact = update.message.body.contact
        if contact and check_contact_hash(bot.token, contact.payload):
            ...

.. automodule:: maxo.utils.contact
   :members:
   :undoc-members:

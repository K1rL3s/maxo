Updates
=======

Апдейты живут в :mod:`maxo.types`. Импорт из ``maxo.routing.updates``
удалён - используйте ``maxo.types``.

.. autoclass:: maxo.types.BaseUpdate
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.MaxUpdate
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.MessageCreated
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.MessageCallback
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.MessageEdited
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.MessageRemoved
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.CommentCreated
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.CommentEdited
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.CommentRemoved
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.BotStarted
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.BotStopped
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.BotAddedToChat
   :members:
   :undoc-members:
   :show-inheritance:

С ноября 2026 года MAX присылает событие ``bot_added`` без поля ``user``.
Для старых событий поле доступно как ``Omittable[User]``. Если поле
отсутствует, контекст события содержит ``chat_id`` и тип чата, а ``user_id``
равен ``None``.

.. autoclass:: maxo.types.BotRemovedFromChat
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.BotAdminPermissionsChanged
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.UserAddedToChat
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.UserRemovedFromChat
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.ChatTitleChanged
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.DialogCleared
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.DialogMuted
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.DialogUnmuted
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.DialogRemoved
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: maxo.types.ErrorEvent
   :members:
   :undoc-members:
   :show-inheritance:

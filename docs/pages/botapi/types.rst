Types
=====

В ответах ``SimpleQueryResult`` и ``ModifyMembersResult`` поле ``code``
содержит код ошибки. Оно может отсутствовать или быть ``None``.
Свойство ``unsafe_code`` возвращает строку и вызывает
``AttributeIsEmptyError``, если код отсутствует или равен ``None``.

.. automodule:: maxo.types
   :members:
   :undoc-members:
   :show-inheritance:

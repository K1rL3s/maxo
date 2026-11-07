---
name: butcher-update
description: Используется при изменении контракта MAX Bot API в maxo: обновлении max-swagger.json или max-swagger.yaml, новом или изменённом типе, enum, методе, update либо регенерации src/maxo/types, src/maxo/enums, src/maxo/bot/methods
---

# Обновление MAX Bot API через butcher

Процедура, оверрайды и карта ручных регистраций - в `butcher/AGENTS.md`:
прочитай его целиком перед первым шагом и иди по разделу «Обновление
контракта». Генерация идёт только в сторону через `--output-dir`, в `src/maxo`
переносится дельта двух снимков.

Перечень ручного слоя, который генерация стирает, - в
`references/manual-layer.md`.

from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Body
from maxo.omit import Omittable, Omitted
from maxo.types.bot_command import BotCommand
from maxo.types.bot_commands_info import BotCommandsInfo


class EditMyCommands(MaxoMethod[BotCommandsInfo]):
    """
    Добавление, изменение и удаление команд бота

    Метод добавляет, изменяет или удаляет команды бота, отображаемые пользователю в качестве подсказок в диалогах и групповых чатах:
    • При вводе «/» - на платформах iOS, Android, десктоп
    • При нажатии кнопки с символом « / » в правом нижнем углу диалога с ботом - на платформе iOS

     Отображение команд **в каналах не поддерживается**. Функциональность доступна на платформах:
    • **Для диалогов** с ботом - iOS, Android, десктоп
    • **Для групповых чатов** с ботом - iOS, Android

    Чтобы удалить все команды, передайте пустой массив `commands`

    Подробнее о работе метода - [в разделе «Команды для чат-бота»](https://dev.max.ru/docs-api/use-cases/chatbot-commands)

    #### Пример запроса:
    ```bash
    curl -X PATCH "https://platform-api2.max.ru/me/commands" \
      -H "Authorization: {access_token}" \
      -H "Content-Type: application/json" \
      -d '{
            "commands": [
              {
                "name": "string",
                "description": "string"
              },
              {
                "name": "string",
                "description": "string"
              }
            ]
          }'
    ```

    Args:
        commands: Список команд и их описаний, отображаемых пользователю в подсказках при вводе « `/` »

    Источник: https://dev.max.ru/docs-api/methods/PATCH/me/commands
    """

    __url__ = "me/commands"
    __method__ = "patch"

    commands: Body[Omittable[list[BotCommand]]] = Omitted()
    """Список команд и их описаний, отображаемых пользователю в подсказках при вводе « `/` »"""

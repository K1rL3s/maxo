from maxo.bot.methods.base import MaxoMethod
from maxo.bot.methods.markers import Query
from maxo.enums.upload_type import UploadType
from maxo.types.upload_endpoint import UploadEndpoint


class GetUploadUrl(MaxoMethod[UploadEndpoint]):
    """
    Загрузка медиафайлов

    Метод возвращает URL для загрузки медиафайла и последующей отправки его во вложении к сообщению в чате или канале. После загрузки файлу присваивается токен, который нужно передать в запросе [POST /messages](https://dev.max.ru/docs-api/methods/POST/messages) или [PUT /messages](https://dev.max.ru/docs-api/methods/PUT/messages) в параметре `attachments.payload.token`

      По URL-ссылке, которая вернётся в ответ на запрос, можно загрузить только один файл. Если вы хотите загрузить ещё, отправьте повторно запрос `POST /uploads` и используйте новую URL-ссылку

     Подробные сценарии и примеры загрузки разных типов медиа смотрите [в разделе «Отправка сообщений с медиафайлами»](https://dev.max.ru/docs-api/mediafiles)

     #### Пример запроса для загрузки медиафайла

    ```bash
    curl -X POST "https://platform-api2.max.ru/uploads?type={type}" \
      -H "Authorization: {access_token}"
    ```

    ### Способы загрузки медиафайлов

    В ответ на текущий запрос `POST /uploads` в поле `url` вернётся URL для загрузки медиафайла - загрузить можно одним из двух способов:
    - **Resumable upload** - надёжный способ, если заголовок `Content-Type` не равен `multipart/form-data`. Этот способ позволяет загружать файл частями и возобновлять загрузку с последней успешно загруженной части в случае ошибок

     **Пример загрузки файла по URL**:

    ```bash
    curl -X POST "%UPLOAD_URL%" \
      -H "Authorization: {access_token}" \
      -F "data=@example.mp4"
    ```

    где `%UPLOAD_URL%` - это значение поля `url`, которое вернулось [в ответе](https://dev.max.ru/docs-api/methods/POST/uploads#Результат) на запрос `POST /uploads`
    - **Multipart upload** - более простой, но менее надёжный способ. В этом случае используется заголовок `Content-Type: multipart/form-data`. Файл отправляется целиком одним запросом. Если загрузка прервётся, невозможно её возобновить - придётся начать заново

     **Пример использования cURL для загрузки файла**:

    ```shell
    curl -i -X POST \
      -H "Content-Type: multipart/form-data" \
      -F "data=@movie.pdf" "%UPLOAD_URL%"
    ```

    где `%UPLOAD_URL%` - это значение поля `url`, которое вернулось [в ответе](https://dev.max.ru/docs-api/methods/POST/uploads#Результат) на запрос `POST /uploads`

    ## Обработка медиафайлов

    После успешной загрузки сервер обрабатывает файл. Файлы от нескольких мегабайт обрабатываются дольше

    > Для стабильной работы сервисов MAX убедитесь, что максимальное количество запросов в секунду на platform-api2.max.ru - 30 rps

    Если отправить сообщение с вложением сразу после загрузки, может возникнуть ошибка:

    ```json
    {
      "code": "attachment.not.ready",
      "message": "Key: errors.process.attachment.file.not.processed"
    }
    ```

    **Как избежать ошибки:**
    - После загрузки файла сделайте паузу перед отправкой сообщения
    - Если отправка не удалась, повторите попытку через некоторое время. Увеличивайте интервал с каждой попыткой
    - Загружайте часто используемые файлы заранее и переиспользуйте токен

    Args:
        type: Тип загружаемого файла. Возможные значения: `"image"`, `"video"`, `"audio"`, `"file"`

    Источник: https://dev.max.ru/docs-api/methods/POST/uploads
    """

    __url__ = "uploads"
    __method__ = "post"

    type: Query[UploadType]
    """Тип загружаемого файла. Возможные значения: `"image"`, `"video"`, `"audio"`, `"file"`"""

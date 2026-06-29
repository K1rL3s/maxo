from maxo.omit import Omittable, Omitted, is_defined
from maxo.types.base import MaxoType
from maxo.types.photo_token import PhotoToken


# Самодельный объект для UploadMedia
# https://dev.max.ru/docs-api/methods/POST/uploads
class UploadMediaResult(MaxoType):
    token: Omittable[str] = Omitted()
    photos: Omittable[dict[str, PhotoToken]] = Omitted()
    file_id: Omittable[int] = Omitted()  # ???

    @property
    def last_token(self) -> str:
        if is_defined(self.token):
            return self.token
        if is_defined(self.photos):
            return list(self.photos.values())[-1].token
        raise RuntimeError

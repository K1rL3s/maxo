from maxo.types.callback_button import CallbackButton
from maxo.types.clipboard_button import ClipboardButton
from maxo.types.link_button import LinkButton
from maxo.types.message_button import MessageButton
from maxo.types.open_app_button import OpenAppButton
from maxo.types.request_contact_button import RequestContactButton
from maxo.types.request_geo_location_button import RequestGeoLocationButton

InlineButtons = (
    CallbackButton
    | ClipboardButton
    | LinkButton
    | MessageButton
    | OpenAppButton
    | RequestContactButton
    | RequestGeoLocationButton
)

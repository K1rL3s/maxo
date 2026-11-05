import hashlib
import hmac

from maxo.omit import is_defined
from maxo.types import ContactAttachmentPayload


def check_contact_hash(token: str, payload: ContactAttachmentPayload) -> bool:
    if not is_defined(payload.hash) or not is_defined(payload.vcf_info):
        return False
    expected = hmac.new(
        token.encode(),
        payload.vcf_info.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected.encode(), payload.hash.lower().encode())

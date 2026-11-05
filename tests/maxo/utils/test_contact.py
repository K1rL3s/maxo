import pytest

from maxo.types import ContactAttachmentPayload
from maxo.utils.contact import check_contact_hash

VCF_INFO = "BEGIN:VCARD\nTEL;TYPE=CELL:+1 (234) 567-890\nEND:VCARD"
VCF_HASH = "ee3d82750cc421d596d2bac3350e80c763406417768bbba9292ed95463139807"


@pytest.mark.parametrize("hash_", [VCF_HASH, VCF_HASH.upper()])
def test_check_contact_hash_accepts_hash_of_vcf_info(hash_: str) -> None:
    payload = ContactAttachmentPayload(vcf_info=VCF_INFO, hash=hash_)

    assert check_contact_hash("secret", payload) is True


@pytest.mark.parametrize(
    "payload",
    [
        ContactAttachmentPayload(vcf_info=VCF_INFO, hash=VCF_HASH.replace("e", "f")),
        ContactAttachmentPayload(vcf_info=VCF_INFO + "\n", hash=VCF_HASH),
        ContactAttachmentPayload(vcf_info=VCF_INFO),
        ContactAttachmentPayload(vcf_info=VCF_INFO, hash=None),
        ContactAttachmentPayload(hash=VCF_HASH),
        ContactAttachmentPayload(vcf_info="ВКАРД", hash="хеш"),
    ],
)
def test_check_contact_hash_rejects_mismatch(payload: ContactAttachmentPayload) -> None:
    assert check_contact_hash("secret", payload) is False


def test_check_contact_hash_depends_on_token() -> None:
    payload = ContactAttachmentPayload(vcf_info=VCF_INFO, hash=VCF_HASH)

    assert check_contact_hash("other", payload) is False

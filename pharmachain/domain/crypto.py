from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def generate_keypair() -> tuple[str, str]:
    private_key = Ed25519PrivateKey.generate()

    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    return private_bytes.hex(), public_bytes.hex()


def sign_message(private_key_hex: str, message: bytes) -> str:
    private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(private_key_hex))

    return private_key.sign(message).hex()


def verify_signature(
    public_key_hex: str,
    message: bytes,
    signature_hex: str,
) -> bool:
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))

        public_key.verify(
            bytes.fromhex(signature_hex),
            message,
        )

        return True

    except (InvalidSignature, ValueError):
        return False

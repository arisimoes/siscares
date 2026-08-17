import bcrypt
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# Inicializa Fernet com a chave do .env.
# Se a chave não for válida, levanta exceção para forçar configuração segura.
fernet = Fernet(settings.CRYPTO_KEY)


def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(token: str) -> str:
    return fernet.decrypt(token.encode("utf-8")).decode("utf-8")


def _load_signing_private_key():
    if not settings.SIGNING_PRIVATE_KEY:
        return None
    pem = base64.b64decode(settings.SIGNING_PRIVATE_KEY)
    return serialization.load_pem_private_key(pem, password=None)


def _load_signing_public_key():
    if not settings.SIGNING_PUBLIC_KEY:
        return None
    pem = base64.b64decode(settings.SIGNING_PUBLIC_KEY)
    return serialization.load_pem_public_key(pem)


def sign_value(value: str) -> str:
    """Assina um valor com a chave privada do servidor (RSA-PSS + SHA256)."""
    key = _load_signing_private_key()
    if key is None:
        raise RuntimeError("SIGNING_PRIVATE_KEY não configurada")
    signature = key.sign(
        value.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode("utf-8")


def verify_signature(value: str, signature_b64: str) -> bool:
    """Verifica a assinatura de um valor com a chave pública do servidor."""
    key = _load_signing_public_key()
    if key is None:
        raise RuntimeError("SIGNING_PUBLIC_KEY não configurada")
    try:
        key.verify(
            base64.b64decode(signature_b64),
            value.encode("utf-8"),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
        return True
    except Exception:
        return False

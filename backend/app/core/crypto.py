import bcrypt
from cryptography.fernet import Fernet
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

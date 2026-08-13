from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> tuple[bool, str | None]:
    """Verify a password and return a replacement hash when parameters changed."""
    try:
        return password_hasher.verify_and_update(password, password_hash)
    except UnknownHashError:
        return False, None

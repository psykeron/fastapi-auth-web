import os
from hashlib import scrypt


class InvalidPasswordHashException(Exception):
    pass


class InvalidPasswordException(Exception):
    pass


def hash_password(password: str):
    if not password:
        raise InvalidPasswordException()

    salt = os.urandom(32)
    hashed_password = __hash_with_scrypt(
        password.encode("utf-8", errors="strict"), salt=salt
    )
    return format_hashed_password(
        algorithm="scrypt", salt=salt, hashed_password=hashed_password
    )


def __hash_with_scrypt(password: bytes, salt: bytes) -> bytes:
    return scrypt(password, salt=salt, n=2**14, r=8, p=1, dklen=64)


def format_hashed_password(algorithm: str, salt: bytes, hashed_password: bytes) -> str:
    return f"{algorithm}/{salt.hex()}/{hashed_password.hex()}"


def verify_password(password: str | None, hashed_password: str | None) -> bool:
    if not password:
        raise InvalidPasswordException()

    if not hashed_password:
        raise InvalidPasswordHashException()

    algorithm, salt_hex, hashed_key_hex = hashed_password.split("/")

    if len(salt_hex) != 64 or algorithm != "scrypt" or len(hashed_key_hex) != 128:
        raise InvalidPasswordHashException()

    if __hash_with_scrypt(
        password.encode("utf-8", errors="strict"), salt=bytes.fromhex(salt_hex)
    ) == bytes.fromhex(hashed_key_hex):
        return True

    raise InvalidPasswordException()

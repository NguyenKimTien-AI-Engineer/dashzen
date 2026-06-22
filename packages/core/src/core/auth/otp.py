import secrets

from core.auth.password import hash_password, verify_password


def generate_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_verification_code(code: str) -> str:
    return hash_password(code)


def verify_verification_code(plain: str, hashed: str) -> bool:
    return verify_password(plain, hashed)

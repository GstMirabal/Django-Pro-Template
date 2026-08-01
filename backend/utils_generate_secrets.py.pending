import secrets
import string

from cryptography.fernet import Fernet


def generate_django_secret_key():
    """Generates a 50-character random string suitable for DJANGO_SECRET_KEY."""
    chars = "abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)"
    return "".join(secrets.choice(chars) for i in range(50))


def generate_master_key():
    """Generates a valid Fernet key (32 bytes, url-safe base64 encoded)."""
    return Fernet.generate_key().decode()


def generate_encryption_pepper():
    """Generates a random 32-byte hex string for the blind index pepper."""
    return secrets.token_hex(32)


def generate_jwt_signing_key():
    """Generates a signing key for JWT access and refresh tokens (ADR-0003)."""
    return secrets.token_urlsafe(64)


def generate_postgres_password():
    """Generates a secure random password."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for i in range(20))


def main():
    print("=" * 60)
    print("🔐  USER-APP-TEMPLATE SECRET GENERATOR  🔐")
    print("=" * 60)
    print("\nCopy these values into your 'config.toml' or '.env' file.\n")

    print("[django_settings]")
    print(f'DJANGO_SECRET_KEY = "{generate_django_secret_key()}"')

    print("\n[security]")
    print(f'MASTER_KEY = "{generate_master_key()}"')
    print(f'ENCRYPTION_PEPPER = "{generate_encryption_pepper()}"')
    print(f'JWT_SIGNING_KEY = "{generate_jwt_signing_key()}"')

    print("\n[DB] (Optional generated password)")
    print(f'POSTGRES_PASSWORD = "{generate_postgres_password()}"')

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

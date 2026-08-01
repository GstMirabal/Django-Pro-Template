"""Generate the secrets this project needs, so none is invented by hand.

A hand-picked secret is the one nobody admits to. This prints values from
`secrets`, which is the CSPRNG, rather than leaving a developer to type
something memorable into `config.toml`.

Run it, copy the output, and keep the values out of version control:

    python backend/utils/generate_secrets.py

The optional section covers `django-users-app`. Those two keys are printed
because generating them wrongly is worse than not generating them at all —
`MASTER_KEY` must be a valid Fernet key, and there is no rotation path once
data is encrypted under it.
"""

import secrets
import string


def django_secret_key() -> str:
    """Return a 50-character key for `DJANGO_SECRET_KEY`.

    Returns:
        str: A random string from Django's own alphabet for this setting.
    """
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(alphabet) for _ in range(50))


def postgres_password() -> str:
    """Return a URL-safe database password.

    URL-safe matters: the value ends up inside a connection string, and a
    password containing `@` or `/` truncates it silently.

    Returns:
        str: A random URL-safe string.
    """
    return secrets.token_urlsafe(32)


def redis_password() -> str:
    """Return a URL-safe password for a Redis instance.

    Returns:
        str: A random URL-safe string.
    """
    return secrets.token_urlsafe(24)


def fernet_master_key() -> str:
    """Return a Fernet key for `MASTER_KEY`, if `cryptography` is installed.

    Only relevant when an application performing encryption at rest is
    installed. Generated here rather than by hand because Fernet requires a
    32-byte urlsafe-base64 key, and an invalid one fails at first decrypt
    rather than at startup.

    Returns:
        str: A Fernet key, or an explanatory line when `cryptography` is
            absent, since this template does not depend on it.
    """
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        return '<install `cryptography` to generate, or use the app that needs it>'
    return Fernet.generate_key().decode()


def encryption_pepper() -> str:
    """Return a pepper for HMAC blind indexing.

    Returns:
        str: 64 hex characters.
    """
    return secrets.token_hex(32)


def main() -> None:
    """Print every generated secret, grouped by the section it belongs to."""
    print('=' * 64)
    print('  SECRET GENERATOR')
    print('=' * 64)
    print('\nCopy these into config.toml or .env. Never commit them.\n')

    print('[django_settings]')
    print(f'DJANGO_SECRET_KEY = "{django_secret_key()}"')

    print('\n[DB]')
    print(f'POSTGRES_PASSWORD = "{postgres_password()}"')

    print('\n[cache]')
    print(f'# REDIS_URL = "redis://:{redis_password()}@redis:6379/0"')

    print('\n# --- Only if an app requiring encryption at rest is installed ---')
    print('# (django-users-app: see its USERS_CONTRACT.md, Host requirements)')
    print(f'MASTER_KEY = "{fernet_master_key()}"')
    print(f'ENCRYPTION_PEPPER = "{encryption_pepper()}"')

    print('\n' + '=' * 64)
    print('  MASTER_KEY has no rotation path once data is encrypted under it.')
    print('  Losing it makes that data unrecoverable, not merely unreadable.')
    print('=' * 64)


if __name__ == '__main__':
    main()

"""Test settings.

Imports the real configuration and overrides only what must not reach external
infrastructure, so the suite runs without Docker or a reachable PostgreSQL.

`agents.md §3 local_testing` requires the database to be instantiated in RAM
rather than against the native URL. Everything else — middleware, the
authentication backends, the five password validators, the security headers —
stays exactly as production defines it, so the tests exercise the real stack.
"""

from .settings import *  # noqa: F403

# In-RAM database (agents.md §3 local_testing).
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# The breach-corpus validator performs an outbound HTTPS request to the Have I
# Been Pwned range API. Tests must not depend on network reachability, so it is
# dropped here; ADR-0004 documents the production chain and CORE_BLUEPRINT
# asserts its order.
AUTH_PASSWORD_VALIDATORS = [  # noqa: F405
    validator
    for validator in AUTH_PASSWORD_VALIDATORS  # noqa: F405
    if 'PwnedPasswords' not in validator['NAME']
]

# Argon2 is deliberately slow; the suite creates many users and does not
# measure hashing strength.
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']

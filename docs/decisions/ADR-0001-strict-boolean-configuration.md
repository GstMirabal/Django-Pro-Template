# 📜 ADR-0001: Strict boolean parsing for security-relevant configuration
**Status**: `Accepted`
**Date**: 2026-07-31
**Triggers**: 3 (`rules/documentation_standard.md §3.1`)

---

## 1. Context

Configuration arrives from `config.toml` through `envtoml`, which interpolates `$VAR` placeholders from the environment. Values templated as `DEBUG = "$DEBUG"` therefore reach Python as **strings**, not booleans.

Four settings in this project decide security posture rather than behaviour detail:

| Setting | What it gates |
| :--- | :--- |
| `DEBUG` | The entire `if not DEBUG:` block — HSTS, CSP, secure cookies, Permissions-Policy — plus the `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` and production email guards |
| `TRUST_PROXY_SSL_HEADER` | Whether `X-Forwarded-Proto` is trusted to mean "this request arrived over TLS" |
| `CROSS_SITE_FRONTEND` | Whether session and CSRF cookies are issued with `SameSite=None` |
| `EMAIL_USE_TLS` | Whether outbound SMTP is encrypted |

Every non-empty string is truthy in Python. A value of `"false"` used unconverted evaluates to `True`.

## 2. Decision

A single helper, `_parse_strict_bool(value, key)` in `backend/config/settings.py`, converts each of these four values. It accepts only the exact strings `"true"` and `"false"`, case-insensitively, and raises `ImproperlyConfigured` on anything else — including `"1"`, `"0"`, `"yes"`, `""` and `None`.

The process therefore refuses to start rather than boot with an ambiguous security setting.

## 3. Consequences

**Easier.** A misconfiguration surfaces at import time with the offending key named, instead of silently selecting the insecure branch. All four settings share one code path, so the rule cannot drift between them.

**Harder.** The accepted vocabulary is narrower than most Django projects expect: an operator writing `DEBUG = "1"` — valid in many toolchains — gets a hard failure. That is deliberate, because the alternative is guessing, but it is a real friction cost for anyone arriving from a project with looser parsing, and it must stay documented in `config.toml.example`.

The strictness applies only to these four values. Other configuration keys are consumed as read, so the guarantee is narrow and should not be assumed project-wide.

## 4. Deciders

Repository owner.

## 5. Considered Options

| Option | Pros | Cons |
| :--- | :--- | :--- |
| **Strict parser, hard failure on anything ambiguous** (chosen) | The insecure branch cannot be selected by accident; one code path for all four | Rejects spellings other projects accept |
| Permissive parser (`"1"`, `"yes"`, `"on"` truthy) | Familiar to operators | Widens the set of inputs whose meaning must be guessed; the guess is what causes the defect |
| `bool()` on the raw value | No code | `"false"` is truthy — the exact failure this ADR exists to prevent |
| Native TOML booleans, no interpolation | No parsing at all | Loses `$VAR` interpolation, which is how secrets stay out of the tracked `config.toml.example` |

---
*Immutable once Accepted — a changed decision gets a new ADR that supersedes this one, never an in-place edit (`rules/documentation_standard.md §3`).*

# 📜 ADR-0002: Proxy TLS trust and cross-site cookies are opt-in
**Status**: `Accepted`
**Date**: 2026-07-31
**Triggers**: 3 (`rules/documentation_standard.md §3.1`)

---

## 1. Context

Two settings widen a trust boundary, and both are tempting to enable by default because they remove friction for a common deployment shape.

**`SECURE_PROXY_SSL_HEADER`.** Behind a TLS-terminating proxy, Django sees plain HTTP and believes the request is insecure, which breaks `SECURE_SSL_REDIRECT` and secure-cookie issuance. The fix is to trust `X-Forwarded-Proto`. But that header is an ordinary request header: with no proxy actually overwriting it, any client can send `X-Forwarded-Proto: https` and Django will treat a plaintext request as encrypted.

**`SESSION_COOKIE_SAMESITE` / `CSRF_COOKIE_SAMESITE`.** A decoupled frontend on a genuinely different registrable domain cannot authenticate by session cookie, because browsers never attach a `SameSite=Lax` cookie — Django's default — to a cross-site `fetch` or `XHR`. Setting `None` fixes it. But the same-site-but-cross-origin cases that most projects actually have (`localhost:3000` calling `localhost:8000`, or a different subdomain) already work with the default and gain nothing.

## 2. Decision

Both stay **off unless explicitly enabled**, through `TRUST_PROXY_SSL_HEADER` and `CROSS_SITE_FRONTEND` respectively. Both are parsed by the strict boolean helper of [ADR-0001](ADR-0001-strict-boolean-configuration.md), so neither can be switched on by a stray string.

## 3. Consequences

**Easier.** A deployment without a proxy cannot be tricked into believing plaintext requests are TLS. A project whose frontend is same-site keeps the stronger `SameSite=Lax` default rather than inheriting a weakening it never needed.

**Harder.** Both defaults produce a symptom that looks like a bug to whoever hits it first. Behind a proxy with `TRUST_PROXY_SSL_HEADER` unset, the app redirect-loops or refuses to set secure cookies. With a cross-site frontend and `CROSS_SITE_FRONTEND` unset, login appears to succeed and then every subsequent request is anonymous. Neither failure names its cause, so both must stay documented in `config.toml.example` and in the deployment guide — the cost of this decision is paid in documentation, and it is only correct while that documentation exists.

Enabling `CROSS_SITE_FRONTEND` also implies `Secure` cookies and therefore HTTPS in development, which complicates local work against a remote API.

## 4. Deciders

Repository owner.

## 5. Considered Options

| Option | Pros | Cons |
| :--- | :--- | :--- |
| **Both opt-in** (chosen) | Neither trust boundary widens without an explicit decision; safe default for the majority shape | Two failure modes whose symptom does not name the cause |
| Enable `SECURE_PROXY_SSL_HEADER` by default | Works behind a proxy out of the box | Any client can spoof TLS when no proxy strips the header |
| Enable `SameSite=None` by default | Any frontend topology works immediately | Weakens CSRF-adjacent protection for every project that did not need it |
| Auto-detect the proxy | No configuration | There is no reliable signal: detection means trusting a header, which is the vulnerability itself |

---
*Immutable once Accepted — a changed decision gets a new ADR that supersedes this one, never an in-place edit (`rules/documentation_standard.md §3`).*

# 📜 ADR-0004: Layered password policy, structural plus breach-corpus
**Status**: `Accepted`
**Date**: 2026-07-31
**Triggers**: 3 (`rules/documentation_standard.md §3.1`)

---

## 1. Context

Structural password rules — length, character classes — and breach-corpus checks fail in opposite directions.

Structural rules alone accept `Password1!`, which satisfies every complexity requirement and appears in essentially every public breach corpus. Breach checks alone accept a password absent from those corpora but trivially guessable for a specific target, and they depend on a third-party API being reachable.

## 2. Decision

`AUTH_PASSWORD_VALIDATORS` chains five validators, in this order:

1. `UserAttributeSimilarityValidator` — rejects passwords derived from the account's own data
2. `MinimumLengthValidator`
3. `CommonPasswordValidator` — Django's bundled list
4. `apps.core.validators.PasswordComplexityValidator` — uppercase, lowercase, digit, non-alphanumeric, each with its own error `code`
5. `pwned_passwords_django.validators.PwnedPasswordsValidator` — Have I Been Pwned range API

The breach check is **last**. The cheap local checks reject the obvious cases first, so the network call only happens for passwords that already passed everything else.

## 3. Consequences

**Easier.** Neither failure mode is left open. Coded errors on the complexity validator let a client localise its messages instead of parsing English strings. Ordering keeps the outbound request off the common rejection path.

**Harder.** Registration now depends on an external API for its final check. The `pwned-passwords-django` validator fails open on network error — it allows the password rather than blocking signup during an outage — so the guarantee is best-effort, not absolute. That is the right trade for availability, but it means "we check against breach corpora" is true on a normal day and not on a bad one.

Each password change also sends a k-anonymity prefix to a third party. The password never leaves the process, but the fact that a check occurred is observable by that provider.

Five validators is a strict policy. It will reject passwords real users consider reasonable, and the template ships that strictness as its default.

## 4. Deciders

Repository owner.

## 5. Considered Options

| Option | Pros | Cons |
| :--- | :--- | :--- |
| **Five-validator chain, breach check last** (chosen) | Covers both failure directions; network call only on the uncommon path | External dependency on the final check; fails open |
| Structural rules only | No external dependency; deterministic | Accepts `Password1!` and every other structurally-valid breached password |
| Breach corpus only | Catches what actually gets guessed in practice | Accepts targeted-guessable passwords; useless during an outage |
| Breach check first | Rejects the worst passwords soonest | An outbound request on every attempt, including ones a local rule would have rejected instantly |

---
*Immutable once Accepted — a changed decision gets a new ADR that supersedes this one, never an in-place edit (`rules/documentation_standard.md §3`).*

# 📋 Sprint Log: #001 — Backend / Reference Scaffold
**Sprint ID**: 001
**Stack / Layer**: backend / reference-scaffold
**Date**: 2026-08-01
**Branch**: `ai-sprint/001` (RA-12)
**Status**: `CLOSED`

---

## 1. Purpose

Establish this repository as the backend scaffold the other Django hosts copy from, and close it against an explicit exit criterion rather than a judgement call.

The trigger: a sibling repository, `User-APP-Template` (renamed `django-users-app` in its Sprint #004), was found to duplicate this project's scaffold — 15 shared files, all diverged — and to have accumulated genuine improvements this repository lacked. Propagating from here requires this repository to be the more advanced of the two first.

## 2. Sequence

Documentation before fixes, and dependencies before the audit, so what gets audited is the code in its final form.

| Phase | Content | Gate |
| :--- | :--- | :--- |
| 1.1 | Documentation verified against the graph; governance; ADRs; Vale; banner | Freshness gate green |
| 1.2 | pytest harness | 13 tests collected and passing |
| 1.3 | Dependency upgrade | Suite green on the new stack |
| 1.4 | Deep audit, full protocol | Report published |
| 1.5 | Fixes | Zero blocking findings open |
| 1.6 | Full verification | Twelve exit criteria |
| 1.7 | Publication as reference scaffold | Reusable workflow, template flag |

## 3. What the audit found

Eight findings, in `docs/audits/AUDIT_001_BACKEND.md`. Three were fixed as prerequisites for later phases; the rest in 1.5.

| ID | Finding | Severity |
| :--- | :--- | :--- |
| F-001 | Application loggers reached no handler | High, latent |
| F-002 | Optional boolean keys could not reach their default | High |
| F-003 | `.env` loaded only by `manage.py` | High |
| F-004 | No health endpoint | Medium |
| F-005 | No `CACHES` configuration | Medium |
| F-006 | `.gitignore` pointed at the wrong log directory | Low |
| F-007 | Workflows inherited default token permissions | Medium |
| F-008 | `dependabot.yml` groups nothing | Low, open |

**F-003 was the one that mattered most.** `envtoml` interpolates `$VAR` from the environment while reading `config.toml`, so the environment has to be populated before that read — and for every entrypoint. It was populated in `manage.py` alone, which meant WSGI, ASGI and pytest all booted with an empty environment. Docker hid it, because container runtimes inject the variables directly. A gunicorn deployment on a host with a `.env` file did not start.

**F-002 is the one an operator would have hit first.** Following this project's own README — copy `config.toml.example`, set the required variables — aborted startup on `TRUST_PROXY_SSL_HEADER`, because `envtoml` interpolates an unset variable to an empty string and `dict.get(key, fallback)` never reaches its fallback when the key exists. CI masked it by setting both optional flags explicitly.

## 4. A regression introduced and caught inside this sprint

Moving `.env` loading into `settings.py` left the original loader in `manage.py`, which used plain assignment and ran first. The file therefore overwrote variables already present in the real environment, and `DEBUG=false manage.py check --deploy` silently read `DEBUG` back as `true`, reporting five security warnings.

It was caught by the phase 1.6 sweep — running everything rather than only what had just been touched — which is the reason that phase exists.

## 5. Metrics

| Metric | Before | After |
| :--- | ---: | ---: |
| Tests | 13 (via `manage.py test`) | 19 (via pytest, in-RAM SQLite) |
| Working entrypoints | 1 of 4 | 4 of 4 |
| Django | 5.2.16 | 6.0.7 |
| ADRs | 0 | 4 |
| `ruff` findings | 0 | 0 |
| `check --deploy` under a real `DEBUG=false` | 5 warnings | 0 |

## 6. Verified and found correct

An audit that lists only problems misrepresents its subject. The existing documentation was checked claim by claim against the code and **no false statement was found**; every `.py` file under `backend/` is documented; no secret has ever been committed, confirmed over the whole history and independently by GitHub secret scanning; and Django 6.0.7 required no application-code change.

## 7. Open

- F-008: `dependabot.yml` has no grouping and no PR limit. Now that Dependabot is enabled at the repository level, a routine week can open one pull request per package.
- C4 Level 3 stays advisory: `backend/apps/` holds one container, below the five-container floor.

---
*Closed under RA-05: Blueprint, Walkthrough, Roadmap and Master Ledger all updated.*

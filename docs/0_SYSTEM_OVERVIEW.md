# 🧭 System Overview: Django Pro Template
**Last Audit Sprint**: #002
**Last Audit Date**: 2026-08-02
**Last Audit Commit SHA**: b6ff56c

This is the **Documentation Entry Point**. `agents.md §0 (Entry Point)` requires every session to read this file before anything else. It is intentionally short — for the full component inventory, see `.agents/docs/architecture/topology_map.md`.

---

## 1. What this is
This project uses the **Token-Optimized Agent Pipeline (`.agents`)** framework as a git submodule: a governance layer that determines how AI subagents plan, execute, and hand off work here.

The host project itself is **Django Pro Template**: a production-ready Django 6.0 backend scaffold. Its design goal is a secure, scalable starting point — configuration through `config.toml` + `.env` with a hard failure on a missing secret, hardened security defaults, structured logging, and a `apps.core` app carrying the pieces every project needs.

It is also the **reference scaffold** for the other Django repositories in this account. `django-users-app` is installed into it by a CI job on every run, which is the only thing that proves the pairing works; `Tradingview2EXCH` calls its reusable CI workflow rather than copying one.

## 2. Architecture at a glance (C4 Level 1-2)

**Level 1 — Context**: this system and who/what it talks to outside its own boundary.

```
[Browser / API client] --HTTP--> [Django Pro Template backend] --SQL--> [PostgreSQL]
                                          |
                                          +--SMTP--> [Email provider] (production only)
```

**Level 2 — Container**: the deployable pieces this system is built from.

```
backend/            Django project (WSGI app via gunicorn in production).
  config/           Project-level settings, URL root, WSGI/ASGI entrypoints.
                    Security middleware stack: SecurityMiddleware, whitenoise,
                    CSP (django-csp), Permissions-Policy
                    (django-permissions-policy), CORS (django-cors-headers),
                    CSRF, brute-force lockout (django-axes) on every auth view
                    including /admin/login/.
  apps/core/         The only installed local app. Holds the health endpoint
                     (/health/, 200 healthy and 503 degraded), core.E001 — a
                     system check that constructs every registered admin form
                     and formset so a broken one fails at check time rather
                     than on a 500 — and PasswordComplexityValidator, wired
                     into AUTH_PASSWORD_VALIDATORS. 20 tests.
Dockerfile          Multi-stage production image (non-root, gunicorn,
                    docker-entrypoint.sh runs migrate+collectstatic on start).
                    Optional `backend` service in docker-compose.yml builds
                    from it; local dev still runs Django outside Docker via
                    `venv` against just the `db` service. See docs/guides/CORE_DEPLOYMENT_GUIDE.md.
PostgreSQL          External datastore, configured via dj_database_url from config.toml/.env.
CI (GitHub Actions) The pipeline lives in django-ci.yml as a *reusable*
                    workflow other repositories call rather than copy, and
                    ci.yml is a thin caller. Lint, system checks, a
                    missing-migration check, the suite, the documentation
                    freshness gate, and a production boot under a real
                    DEBUG=false. A second job vendors django-users-app into
                    this template and runs both suites together.
```

Component-level (Level 3) detail, where required, lives per-module in the relevant `[MODULE]_BLUEPRINT.md` — see `rules/documentation_standard.md §2.1` for which modules require it. `code_containers` is declared (`backend/apps/`) but only one container (`core`) exists today, so Level 3 stays advisory (below the 5-container safety floor).

## 3. The governance hierarchy
| Layer | Location | Role |
| :--- | :--- | :--- |
| **Governance Rules** | `.agents/agents.md` | The absolute, transversal rules. Nothing overrides this. |
| **Rules** | `.agents/rules/*.md` | Domain-specific standards (QA, topology, skills, security, documentation). |
| **Workflows** | `.agents/workflows/*.md` | Step-by-step protocols, invoked as `/agents:<name>` slash commands. |
| **Subagents** | `.agents/agents/*.md` | The roles that execute workflow steps (Principal, Orchestrator, QA, Tester, etc.). |
| **Skills** | `.agents/skills/*/` | Concrete tools subagents call into (linters, scaffolders, auditors). |

## 4. How a session starts
Run `/agents:start`. It will:
1. Read `agents.md` and this file (Zero-Memory anchor).
2. Install/verify the Claude Code bridge (`.agents/scripts/install_claude.sh`) if not already done.
3. On a brand-new project, scaffold `docs/active_state.json` and the rest of the `docs/` tree — see `.agents/workflows/start_workflow.md`.
4. Hand off to the Principal Agent for Planning (drafting the Implementation Plan with you).

## 5. Where state lives
- `docs/active_state.json` — this project's own session anchor. Tracked here since Sprint #001: the freshness gate reads its sprint number, and a gitignored anchor means the gate silently skips its only blocking check on a fresh clone. Never committed to `.agents`, which keeps its own.
- `CHANGELOG.md` (root) — the **Master Ledger**: sprint entries at close, version seals at deployment.
- `docs/roadmaps/`, `docs/sprints/` — this project's own historical record.
- `.agents/docs/` — the framework's own (separate) self-documentation; not this project's (its changelog is `.agents/CHANGELOG.md`, a different jurisdiction).

## 6. Full inventory
For the detailed component-by-component map (what lives where inside `.agents/`, current status of each piece), read `.agents/docs/architecture/topology_map.md`. For this project's own inventory, see `docs/architecture/CORE_BLUEPRINT.md` and `docs/architecture/CONFIG_BLUEPRINT.md`, plus `docs/active_state.json`'s `topology_map` key. Five ADRs live in `docs/decisions/`.

## 7. Onboarding note
This project predates the `.agents` framework (Onboarding Scenario C: mature project, no prior agentic traces). `docs/architecture/CORE_BLUEPRINT.md` and `docs/walkthroughs/CORE_WALKTHROUGH.md` were generated by Full Reverse Engineering of the existing codebase rather than by executing a Sprint.

Sprint #001 (`docs/sprints/001-backend-reference-scaffold/`) closed that gap: it made every entrypoint boot, added the health endpoint and `core.E001`, raised the stack to Django 6, and published the reusable CI workflow. Sprint #002 added `CONFIG_BLUEPRINT.md`, the cache ADR and the integration job.

# 🚑 Hotfix: H-002-Backend
**File**: `docs/hotfixes/H-002-Backend.md` (RA-03 emergency naming — sanctioned exception to RA-06)
**Severity**: `CRITICAL`
**Detected**: 2026-07-29 · **Resolved**: 2026-07-29

---

## 1. Symptom
Dependabot PR #6 (`envtoml` 0.1.2 → 0.4.0) failed both `lint-and-test` and `deploy-check` CI jobs with `TypeError: File must be opened in binary mode, e.g. use 'rb'`, raised out of `envtoml.load()` during Django settings import — the app would fail to boot entirely on this dependency version, in CI and in production alike.

## 2. Root Cause
`envtoml` 0.4.0 changed its file-handling contract to require a binary-mode file object. `backend/config/settings.py:46` opened `config.toml` in text mode (`config_path.open('r', encoding='utf-8')`), which was correct for `envtoml` 0.1.2 (a thin wrapper over the third-party `toml` package, text-mode only) but incompatible with 0.4.0.

## 3. Fix Applied
| File | Change |
| :--- | :--- |
| `backend/config/settings.py` | `config_path.open('r', encoding='utf-8')` → `config_path.open('rb')` (binary mode, no explicit encoding — `envtoml` 0.4.0 decodes internally). |

Branch/commit: `dependabot/pip/envtoml-0.4.0` (Dependabot PR #6) → `d796bdf`

## 4. Verification
- Installed `envtoml==0.4.0` in the local venv (matching the version this Dependabot PR bumps to).
- `python manage.py check` → `System check identified no issues (0 silenced)` (previously raised `TypeError` at import time).
- `python manage.py test apps.core` → 13 tests, `OK`.
- `ruff check .` → `All checks passed!`.
- No new regression test added: the failure is a file-open-mode contract change in a third-party library, not application logic with a unit to pin. The existing test suite already exercises every code path through `settings.py` (it has to import successfully for any test to run at all), so a `TypeError` here fails the entire suite — that IS the regression guard.

## 5. Rule Amendment Check
- [x] Is this failure class systemic (a process pattern, not a one-off)? **Yes** — a Dependabot bump for a config-loading library can break app boot in a way unrelated to the bump's own changelog scope (no application code diff triggered this, only the dependency version changed). Dependabot PRs for libraries touched by `settings.py`'s fail-fast config loader (`envtoml`, `dj-database-url`) warrant a manual boot-check (`manage.py check`) before merge, not just a green CI that happened to predate the same class of break. Flagged for `governance_learner` to evaluate at next `extract` cycle.
- [ ] Does the root cause reveal a design decision worth recording (not a process pattern — a specific architectural choice)? **N/A** — this is a third-party API compatibility fix, not a design decision in this project.
- [x] Master Ledger entry added under `[Unreleased]`.

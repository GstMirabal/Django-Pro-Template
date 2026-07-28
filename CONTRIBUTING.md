# Contributing to Django Pro Template

Thanks for considering a contribution! This project is a reusable Django backend template, so contributions should keep it generic and useful as a starting point — not add project-specific business logic.

## Ground rules

- Be respectful. This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
- Keep changes focused. One logical change per pull request.
- Prefer configuration over hardcoding. If a change is deployment-specific, it should go through `config.toml`/`.env`, following the existing pattern in `backend/config/settings.py`.

## Getting started

1. Fork the repository and clone your fork.
2. Follow the [Getting Started](README.md#getting-started) section of the README to set up your local environment.
3. Create a branch: `git checkout -b feature/short-description` or `fix/short-description`.

## Before opening a pull request

```bash
# Lint
ruff check .

# Tests
cd backend && python manage.py test apps.core

# Simulate a production boot (catches config regressions unit tests can't)
cd backend && DEBUG=false python manage.py check --deploy
```

CI runs all of the above automatically on every push/PR (`.github/workflows/ci.yml`) — a red CI check means the PR isn't mergeable yet.

## Commit messages

Use clear, descriptive commit messages in English. [Conventional Commits](https://www.conventionalcommits.org/) style (`fix:`, `feat:`, `docs:`, `chore:`) is welcome but not required.

## Reporting bugs / requesting features

Use the issue templates (`.github/ISSUE_TEMPLATE/`). For security vulnerabilities, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Pull request process

1. Fill out the pull request template.
2. Ensure CI passes.
3. A maintainer will review and may request changes.
4. Once approved, a maintainer will merge.

By contributing, you agree that your contributions will be licensed under this project's [MIT License](LICENSE.txt).

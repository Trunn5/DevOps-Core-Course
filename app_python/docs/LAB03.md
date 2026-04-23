# Lab 03 - CI/CD with GitHub Actions

## Overview

- **Testing**: pytest + httpx (FastAPI test client)
- **Linting**: ruff
- **Versioning**: CalVer (`YYYY.MM.sha`)
- **Triggers**: push to main/master/lab03, PRs to main/master (path-filtered to `app_python/`)

---

## Workflow Structure

```
python-ci.yml
├── test       → Install deps, lint (ruff), run tests (pytest)
├── security   → Snyk vulnerability scan (needs: test)
└── docker     → Build & push to Docker Hub (needs: test, push only)
```

---

## Versioning: CalVer

| Tag | Example |
|-----|---------|
| `YYYY.MM.sha` | `2026.02.a1b2c3d` |
| `YYYY.MM` | `2026.02` |
| `latest` | always latest push |

**Why CalVer:** This is a service, not a library. Date-based versions show when it was deployed.

---

## Best Practices

| Practice | Why |
|----------|-----|
| **Dependency caching** | `actions/setup-python` caches pip — faster CI runs |
| **Path filters** | Only runs when `app_python/` changes |
| **Job dependencies** | Docker push only after tests pass |
| **Conditional push** | Only push images on `push`, not on PRs |
| **Snyk scanning** | Catches vulnerable dependencies |
| **Status badge** | Shows CI health in README |
| **Docker layer cache** | Reuses layers from registry for faster builds |

---

## Snyk

- Severity threshold: `high`
- `continue-on-error: true` — warns but doesn't block deploy

---

## Key Decisions

- **pytest over unittest**: simpler syntax, fixtures, plugins
- **ruff over flake8/pylint**: fast, all-in-one linter
- **CalVer over SemVer**: continuous deployment model, date = release time
- **Path filters**: monorepo — don't rebuild Python when only docs change

---

## Workflow Evidence

- Workflow: `.github/workflows/python-ci.yml`
- Docker Hub: `https://hub.docker.com/r/dmitry567/devops-info-service`


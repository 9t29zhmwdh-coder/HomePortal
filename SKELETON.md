# HomePortal: Professional Repo Skeleton

**Generated:** 2026-06-16 | **Earliest commit:** 2026-06-15 | **Release:** v0.1.0

## Files Added

- SKELETON.md ✅
- ARCHITECTURE.md ✅
- PRIVACY.md ✅
- ROADMAP.md ✅
- CONTRIBUTING.md ✅
- CODE_OF_CONDUCT.md ✅
- SECURITY.md ✅
- CHANGELOG.md ✅
- .github/ISSUE_TEMPLATE/bug_report.md ✅
- .github/ISSUE_TEMPLATE/feature_request.md ✅
- .github/PULL_REQUEST_TEMPLATE.md ✅
- .github/workflows/ci.yml ⚠️ requires `workflows` OAuth scope

## CI Workflow

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest
```

## Canonical File Tree

```
HomePortal/
├── app/
│   ├── main.py
│   ├── routers/
│   └── static/
├── nginx/
│   └── default.conf
├── tests/
├── ARCHITECTURE.md
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── PRIVACY.md
├── README.md
├── ROADMAP.md
├── SECURITY.md
└── SKELETON.md
```

---
*HomePortal: RayStudio · Rafael Yilmaz · MIT License · 2026*

# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 2.x     | ✅        |
| < 2.0   | ❌        |

## Reporting a vulnerability

Please do **not** open a public issue for security vulnerabilities.
Report privately via the GitHub repository's Security tab or contact the maintainer directly.

I aim to respond within 72 hours and provide a fix within 14 days for confirmed vulnerabilities.

## How Home Portal is protected

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for the STRIDE analysis, the
trust boundaries and the residual risks. Every change is written to the audit
log (`docker compose logs app`), and each release carries a CycloneDX SBOM.

## Known unfixable advisories

None. `pip-audit` runs against `requirements.lock` on every pull request.

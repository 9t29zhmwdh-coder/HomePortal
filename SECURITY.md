# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | ✅ Yes    |
| Older   | ❌ No     |

Security fixes are only applied to the latest release.

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, report it privately via [GitHub Security Advisory](https://github.com/9t29zhmwdh-coder/HomePortal/security/advisories/new) or contact the maintainer via the GitHub profile.

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

A response within **48 hours** is the target, and the issue will be worked on promptly.

## How Home Portal is protected

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for the STRIDE analysis, the
trust boundaries and the residual risks. Every change is written to the audit
log (`docker compose logs app`), and each release carries a CycloneDX SBOM.

## Known unfixable advisories

None. `pip-audit` runs against `requirements.lock` on every pull request.

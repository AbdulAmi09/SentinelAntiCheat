# Security Policy

Sentinel Anti-Cheat is pre-production software under active development.
It is not currently deployed against live federation or tournament data.

## Reporting a Vulnerability

If you discover a security vulnerability, please report it privately rather
than opening a public issue.

- Email: amisuabdulsemiu09@gmail.com
- Please include: a description of the issue, steps to reproduce, and the
  potential impact.

We aim to acknowledge reports within 5 business days.

## Scope

- API authentication/authorization (`backend/src/sentinel/services/authz.py`)
- Credential handling and secret storage
- Injection or data-integrity issues in the analysis or audit pipeline
- Anything that could let a party bypass or tamper with the immutable
  audit trail

## Out of scope

- Vulnerabilities in third-party dependencies with no working exploit
  against this codebase (report upstream instead)
- Missing security hardening on local/dev-only configuration

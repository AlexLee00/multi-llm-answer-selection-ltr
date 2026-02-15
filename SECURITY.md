# Security Policy

## Supported Versions

Currently supported:

- main branch (latest)

## Reporting a Vulnerability

If you discover a security vulnerability:

- Do NOT open a public issue.
- Contact the maintainer directly.

## Sensitive Data Policy

This repository is public.

The following must NEVER be committed:

- `.env` files
- API keys
- Raw user-identifiable data
- Unmasked feedback logs

## Data Masking

All archived data must:

- Remove raw question text
- Store hashes only
- Avoid personally identifiable information
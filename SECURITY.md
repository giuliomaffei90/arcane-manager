# Security Policy

Arcane Manager is a local macOS desktop app. It does not authenticate users, store account credentials, or send session data to a hosted service. The OWASP Top 10 still helps guide hardening work, especially around configuration, supply chain, data integrity, logging, and exceptional conditions.

## Supported Build

Security fixes target the source on `main` and the latest GitHub Release build.

## Reporting a Vulnerability

Please open a private security advisory on GitHub if available, or contact the maintainers privately before publishing details.

## OWASP-Oriented Controls

- Broken Access Control: no remote API or multi-user authorization boundary is exposed.
- Security Misconfiguration: the app runs as a regular Dock app and builds from a documented script.
- Software Supply Chain Failures: `requirements.lock.txt` pins the build environment used for the packaged app; compiled `.app` and `.zip` artifacts are distributed as Release assets instead of being committed.
- Cryptographic Failures: the app does not manage passwords, sessions, payment data, or encrypted user data. Release notarization is still recommended before wide distribution.
- Injection: spell and monster data are parsed as JSON only; text is displayed as text in native controls or sanitized local WebKit views, not executed as user-provided code. The loaders bound and sanitize untrusted JSON fields.
- Insecure Design: campaign tools run locally, release artifacts are built from pinned dependencies, and any local helper server is bound to `127.0.0.1` for bundled dice assets only.
- Authentication Failures: not applicable; the app has no login or account model.
- Software or Data Integrity Failures: bundled spell data is included at build time; untrusted replacement JSON is size-limited, type-checked, and sanitized.
- Security Logging & Alerting Failures: startup and operational events are logged to `~/Library/Logs/Arcane Manager/arcane_manager.log` with user-only permissions.
- Mishandling of Exceptional Conditions: invalid JSON, oversized data files, missing resources, and unavailable platform features produce controlled errors instead of uncaught crashes where practical.

## Distribution Notes

- Share packaged builds from GitHub Releases, not from a Git commit.
- The current local build is ad-hoc signed. For broader distribution, use an Apple Developer ID certificate and notarize the app.
- Review third-party dependency updates before refreshing `requirements.lock.txt`.

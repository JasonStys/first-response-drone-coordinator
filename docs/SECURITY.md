# Threat model and privacy

By Jason Stys. This is a testable defense-in-depth boundary, not a claim of complete safety or independent certification.

## Assets and trust

Protect credential hashes, opaque sessions, workspace scenarios, review notes and audit history. The local OS owner, CLI provisioner and database administrator are trusted and **can access stored workspace information**. All provisioned users share one exercise workspace; observer means read-only, not separate ownership or tenant isolation. Do not enter real applicant, patient, victim, location or incident information. Source and public demo credentials are not private account data.

## Tested protections

Passwords use Argon2id (64 MiB, time cost 3, parallelism 1), never plaintext. Unknown users use dummy verification; errors are generic. Public API has no account-creation endpoint. Login attempts are stored per hashed direct client address (20/minute, 1,000 active address keys); forwarded IP headers are not trusted. One-hour absolute sessions use random opaque tokens; only their SHA256 digest is stored. Tokens contain no role claims. Roles are looked up server-side, sign-out revokes immediately, and expired sessions fail closed. At most ten live sessions per account are retained.

Cookies are HttpOnly/SameSite=Strict and Secure for an explicitly configured HTTPS origin. Local HTTP is loopback-only; it is not appropriate for remote deployment. Every mutation requires an exact configured Origin; authenticated mutations also require a per-session CSRF header and server-side role check. Host headers must match the configured authority, reducing DNS-rebinding exposure. There is no permissive CORS policy. Request bodies are limited to 64 KiB, including streams, and must be JSON. Strict schemas bound lists, numeric ranges, IDs and task windows. Validation responses do not reflect supplied credential or document content.

SQL uses bound parameters; scenario text is never executed. React escapes values and there is no `dangerouslySetInnerHTML`, third-party script, telemetry or remote font. CSP forbids frames, inline scripts, arbitrary connections and external active content. Additional no-store, nosniff, no-referrer and restrictive permissions headers are applied. HTTPS origins additionally receive HSTS. No ads or popup providers are installed; these controls cannot protect a compromised browser or OS.

All state writes use optimistic revision checks under a SQLite write transaction. Reviews have a separate role and must come from a different identity than the author. Stored allocations are revalidated before review. No path accepts shell commands, arbitrary downloads, untrusted code execution, model APIs, vehicle commands or radio packets.

## Remaining risks / nonclaims

This is not internet-hardened: no MFA/SSO, email recovery, distributed rate limiting, encrypted application-level database, remote security monitoring or independent penetration test. Login hashing and planning still consume bounded but meaningful CPU/memory; the CLI limits concurrency and should never be exposed publicly. Trusted host administrators can alter the database and audit trail. Hashes bind scenario identity but do not cryptographically sign evidence. Clocks, operator qualifications, authorization flags and conditions are trusted inputs, not verified facts. Disk encryption, strong OS accounts, private backups and updates remain the user's responsibility.

Browser offline detection is advisory; a network transport failure is reported and never presented as a successful saved write. If an interrupted request might have committed, refresh before retrying. Double review is rejected; duplicate generation is permitted and audited, not idempotently collapsed.

Dependency audits and CodeQL cover known advisories and query classes at the time of the scan. They are not proof of absence of vulnerabilities. CI uses full Action commit hashes, minimal permissions and no cache/artifact uploads. Public repository workflows use only synthetic data and credentials. Never upload runtime databases, cookies, account passwords or downloaded evidence to GitHub.

The required npm advisory gate uses the official Google OSV scanner, a fixed release and pinned SHA256 verified before execution. Every locked identity must be present in its live report, and any finding or scanner/inventory error fails. The explicit configuration must parse to an empty object: no advisory ignores or package suppressions are accepted. No offline advisory snapshot substitutes for live success. Python dependencies have a separate pip-audit gate. npm's own optional diagnostic remains fail-closed during its observed outages; that unavailable result is not presented as a successful npm audit.

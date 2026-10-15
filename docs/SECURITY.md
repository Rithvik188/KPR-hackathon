# Security and privacy

SevaiCheck handles ID documents, so security is part of the design, not an add-on. No system can honestly be
called "unbreachable". What we can show is **defence in depth**: every layer assumes the one before it might fail,
known attack paths are closed and tested, and we say plainly what a production government deployment still needs.

## What an attacker would want, and how each is protected

| Asset | Threat | Protection in SevaiCheck |
|---|---|---|
| Aadhaar numbers | Leak from the database, logs or API | **Never stored, logged or returned in full.** Display is `XXXX XXXX 1234`; duplicates are found with a keyed **HMAC-SHA256** (server secret), not a plain hash, because 10¹² numbers would be brute-forceable. |
| Phone numbers | Leak, or enumerating citizens | Stored only as a keyed HMAC (lookup key) plus the masked form `98XXXXXX21`. |
| ID-card photos | Theft from disk or via the API | **Encrypted at rest** (Fernet, AES-128 + HMAC), **deleted automatically** when the officer approves or rejects. The image endpoint is permission-checked, and returns "not found" (not "forbidden") for other people's images, so it doesn't reveal that an image exists. |
| Applications, CAN profiles | Mass scraping, reading other citizens' data | **Server-side login + a central permission table on every API route, deny by default** (below). CAN numbers are random, not sequential. |
| Decisions (approve / reject) | Forged approvals | Only a signed-in **Tahsildar** can approve or reject; VAO and RI can only forward, and only at their own stage. The role comes from the **signed token**; a role written into the request is ignored or rejected. Every action is written to the application's history. |
| Staff accounts | Password guessing | Passwords are checked with **PBKDF2-SHA256 (200,000 rounds)**, compared in constant time, and **rate limited** (10 tries/min per IP, 5 per 5 min per ID). Errors don't reveal whether the ID exists. |
| Citizen sign-in | Account takeover | One-time password: 6 digits, **5-minute expiry, single use, 5 tries**, rate limited per phone and per IP. Stored only as an HMAC. |
| Sessions | Forged or stolen tokens | Tokens are **HMAC-signed** with a key derived from the server secret, **expire** (citizens 2 h, staff 10 h), and carry no personal data. |
| The web app | XSS, clickjacking, sniffing, caching | **Content-Security-Policy** (only our own scripts; no inline scripts), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: no-referrer`, **HSTS** on HTTPS, and `Cache-Control: no-store` on every API response. React escapes all output. |
| The server | Malicious uploads, overload | Only real JPEG/PNG (magic bytes checked, not just the extension), a **10 MB cap** enforced before reading, a **decompression-bomb limit** (40 MP), rate limits on all API calls and submissions, SQL only through parameterised queries (SQLModel), no stack traces in errors, API docs hidden in production. |
| Secrets | Leak through the code repository | Kept only in `.env` (git-ignored), shared person to person. The app **refuses to start** with missing or weak secrets. |
| Transport | Eavesdropping | HTTPS end to end for public access (the ngrok tunnel terminates TLS; production would use the department's TLS certificate). |

## Who can do what (enforced on the server, `engine/app/core/policy.py`)

| Action | Citizen | e-Sevai operator | VAO | RI | Tahsildar | Not signed in |
|---|---|---|---|---|---|---|
| Health, office list, accuracy metrics | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Report a problem at a centre | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (rate limited) |
| Create own CAN / application | own phone only | own centre only | – | – | – | – |
| Upload documents | own application | own centre | – | – | – | – |
| Read an application / card image | own only | own centre | ✓ | ✓ | ✓ | – |
| Officer queue, notifications, issue reports | – | – | ✓ | ✓ | ✓ | – |
| Forward | – | – | at VAO stage | at RI stage | – | – |
| Approve / reject | – | – | – | – | ✓ | – |
| District dashboard / notices | – | own centre's notices | ✓ | ✓ | ✓ | – |

Any route not in the table is **denied**. `tests/test_security.py` checks each row: anonymous access, forged and
tampered tokens, wrong passwords, rate limits, cross-citizen and cross-centre access, spoofed roles, and headers.

## Verified

- **131 automated tests**, including 17 security tests. With `AUTH_REQUIRED=1`, every endpoint that exposed data
  before now returns `401` to an anonymous caller.
- **Privacy audit** (`scripts/privacy_audit.py`): signs in as an officer, reads every application in the database
  plus the server logs, and searches for any of the ~390 generated Aadhaar numbers or any 12-digit number. Result:
  clean.
- No real ID documents are in the repository; all test data is synthetic `SPECIMEN` material.

## What is prototype-only (stated honestly)

| In this prototype | In a real government deployment |
|---|---|
| Demo staff accounts share one password from `.env` | Government single sign-on (**e-Pramaan / Parichay**) with individual accounts and 2FA |
| Citizen OTP is shown on screen (`DEMO_OTP_IN_RESPONSE=1`) because there is no SMS gateway | A real SMS gateway (NIC / TNeGA), or Aadhaar e-KYC |
| Secrets in a `.env` file on the server | Keys in a **hardware security module or cloud KMS**, rotated on a schedule |
| SQLite file on one laptop; names and dates of birth are not encrypted at column level | Managed PostgreSQL with **encryption at rest**, backups and least-privilege database users |
| In-memory rate limits | A **web application firewall** and API gateway (rate limits, bot and DDoS protection) |
| Logs on local disk | Centralised, tamper-evident audit logs (SIEM), monitored by the State SOC |
| Self-tested | An independent **CERT-In empanelled security audit** before go-live, as required for government applications, plus **DPDP Act 2023** compliance (purpose limitation, retention limits, breach reporting) |

## Settings

| `.env` key | Meaning |
|---|---|
| `AUTH_REQUIRED` | `1` (default): login and permissions enforced on every API route. `0` only for local development. |
| `STAFF_DEMO_PASSWORD` | Password of the demo staff accounts (at least 10 characters). Never shown in the UI. |
| `DEMO_OTP_IN_RESPONSE` | `1` returns the citizen OTP in the response (no SMS gateway). Must be `0` in production. |
| `AADHAAR_HMAC_SECRET`, `IMAGE_ENC_KEY` | Keyed hashing and image encryption. The app refuses to start if they are missing or weak. |

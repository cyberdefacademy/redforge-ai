# REDFORGE AI — Tool Adapter Architecture (v1.0.0)

## Registry (`backend/app/tools/registry/registry.py`)

11 tools with risk, timeout, and approval flags. `/api/v1/tools` reports live
`status: ready | not_installed` (binary presence check):

| Tool | Category | Risk | Timeout | Approval | Image status |
|---|---|---|---|---|---|
| nmap | reconnaissance | low | 300s | no | ✅ ready |
| masscan | reconnaissance | medium | 600s | yes | ❌ Go binary — follow-up |
| amass | reconnaissance | low | 600s | no | ❌ Go binary — follow-up |
| subfinder | reconnaissance | low | 300s | no | ❌ Go binary — follow-up |
| nuclei | vulnerability | medium | 600s | yes | ❌ Go binary — follow-up |
| gobuster | web | medium | 300s | yes | ❌ Go binary — follow-up |
| feroxbuster | web | medium | 600s | yes | ❌ Go binary — follow-up |
| nikto | web | medium | 600s | yes | ✅ ready (upstream tarball, Debian trixie dropped the package) |
| whatweb | reconnaissance | low | 120s | no | ✅ ready |
| hydra | password_auditing | high | 900s | yes | ✅ ready |
| sqlmap | web | high | 900s | yes | ✅ ready |

Medium/high = approval-gated. High-volume scanners (nikto/nuclei/dir-bust) are
medium even though read-only — a full run sends thousands of requests and has
been observed crashing fragile apps.

## Execution Pipeline

```
Structured action → Engagement authorized? → Kill switch? → Scope Guard (deny-by-default)
  → Risk Engine → Approval (second-person, lead/admin) → validate_params (fused into build)
  → Sandbox (allowlist, secret-stripped env, timeout) → SHA-256 + artifact → AuditLog
```

Never `shell=True` (`asyncio.create_subprocess_exec` with arg lists). `build_command`
refuses to build unvalidated params (no TOCTOU split).

## Adapter notes

- `nmap`: `-sV -Pn [-p ports] target`; strict port validation (1–65535, no reversed ranges).
- `nikto`: optional validated `tuning` param (`-Tuning`, Nikto codes `0-9a-dx`) so scans
  can be limited (e.g. `123b` = files/misconfig/disclosure/ident, no injection/DoS).
- `masscan`: `--top-ports 100 --rate 1000` default when no ports given.
- Targets: bare hosts strictly validated; `http(s)` URLs allow query chars (`?=&%#`)
  but still block shell metachars and `file/gopher/ftp/dict/ldap/jar/javascript/data` schemes.

## Sandbox (`backend/app/tools/sandbox/executor.py`)

- Executable allowlist (name + `/usr/bin|/usr/local/bin|/bin|/opt` prefixes); bare names
  resolved via `PATH`, relative paths rejected.
- Traversal-safe engagement dirs (unsafe IDs hashed); secret-stripped child env
  (`*_KEY`, `*_SECRET`, DB/Redis URLs removed); `PATH` pinned.
- Timeout clamp 1–1800s (exit 124); stdout/stderr caps; provenance + SHA-256 per run;
  artifacts persisted to `$EVIDENCE_DIR/{engagement}/` (best-effort).
- WhatWeb fix (baked into image): `resolv-replace` disabled — its pure-Ruby DNS is
  AAAA-first with no connect fallback and breaks scans in dual-stack Docker networks.
- Resource limits (CPU/mem), net-namespaces, and cgroups are **not** implemented —
  isolation relies on container boundaries (tracked limitation).

## Parsers (`backend/app/tools/parsers/`, via `engine/recon.py`)

`nmap, nuclei, gobuster, nikto, whatweb` → normalized `{ports, findings, paths, vulns, tech}`.
Web parsers strip ANSI color codes (tools emit them even when piped). `recon/ingest`
persists evidence + creates Host/Port/Service/Finding rows, including `tech` stack findings.

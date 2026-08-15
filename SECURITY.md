# Security Policy for RecallBox

RecallBox is designed as a **privacy-first, local-first personal memory system**. Because personal memories, notes, snippets, and browsing context contain sensitive information, security is a fundamental architectural requirement.

---

## Supported Versions

Only the latest active release and master branch receive security patches.

| Version | Supported |
| :--- | :---: |
| `0.1.x` | ✅ Supported |
| `< 0.1.0` | ❌ End of Life |

---

## Core Security Controls in RecallBox

1. **Local-First Isolation**: By default, RecallBox binds exclusively to loopback (`127.0.0.1:8765`). Zero memory data, search telemetry, or analytics are uploaded to any external server.
2. **Local API Authorization**: All sensitive CRUD, search, and export API operations require a cryptographically generated local token (`X-RecallBox-Key`) stored in `data/auth_token` (file permission `0o600`).
3. **Cross-Origin Request Protection**: Cross-Origin Resource Sharing (CORS) is restricted to local user interface origins (`localhost:3000`, `localhost:5173`) and browser extension protocols. Untrusted external websites cannot exfiltrate or manipulate local memories.
4. **Untrusted Content Sanitization & Safe Highlighting**: Web content scraped from the internet is treated as untrusted. HTML tags are stripped during ingestion, and search highlights are rendered using safe React tokenization (without `dangerouslySetInnerHTML`) to prevent Stored Cross-Site Scripting (XSS).
5. **Hop-by-Hop SSRF Protection**: Backend URL ingestion strictly blocks requests to internal IP subnets, loopbacks (`127.0.0.0/8`, `::1`), RFC1918 addresses, and cloud metadata services (`169.254.169.254`), with DNS re-checks on every HTTP 302 redirect hop.
6. **MCP Destructive Gating**: Model Context Protocol (MCP) destructive tools (`forget`) are disabled by default (`RECALLBOX_MCP_ALLOW_DESTRUCTIVE=false`) to defend against indirect prompt injection.

---

## Reporting a Security Vulnerability

If you discover a security vulnerability in RecallBox:

1. **Do NOT disclose the vulnerability publicly in GitHub Issues, Discussions, or social media.**
2. Use **[GitHub Private Vulnerability Reporting](https://github.com/OTAKUWeBer/RecallBox/security/advisories/new)** to submit your report securely.
3. Include:
   - Detailed description of the vulnerability and affected components (backend, web, extension, MCP, CLI).
   - Step-by-step reproduction steps or a minimal Proof of Concept (PoC).
   - Potential impact and any suggested mitigations.

### Response Timeline
- **Initial Acknowledgment**: Within 48 hours.
- **Triage & Validation**: Within 5 business days.
- **Fix & Advisory Release**: Coordinated with the finder prior to public disclosure.

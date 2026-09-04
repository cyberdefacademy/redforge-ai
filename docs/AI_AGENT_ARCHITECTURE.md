# REDFORGE AI — AI Agent Architecture

## Provider Abstraction (ai/providers)
Supports OpenAI-compatible, Ollama, LM Studio, local HTTP endpoints.
Config per agent: provider, model, endpoint, api_key, temperature, timeout.

## Agents

| Agent | Responsibility | Tools |
|-------|---------------|-------|
| Recon | passive recon, DNS, asset discovery | amass, subfinder, dnsx, whois, whatweb |
| Network | network/service enumeration | nmap, masscan, netcat |
| Web | app mapping, auth, injection | nuclei, gobuster, zap, nikto |
| AD | domain/privilege graph | (adapters: bloodhound, ldap) |
| Cloud | IAM, exposure | (cloud adapters) |
| Vuln Validation | correlate, dedupe, verify | nuclei, searchsploit |
| Attack Path | graph + prioritization | internal graph engine |
| Reporting | executive/technical/narrative | evidence + findings DB |

## Decision Loop
```
OBSERVE → COLLECT EVIDENCE → ANALYZE → UPDATE GRAPH → GENERATE ACTIONS
→ RISK EVAL → SCOPE VAL → POLICY VAL → APPROVAL → EXECUTE → VERIFY → STORE → REASSESS
```

Each decision stored as: discovered, hypothesis, next_action, target, risk, supporting_evidence, invalidating_evidence.

## MCP Integration
- Tool/MCP Orchestration layer routes structured actions to either:
  - MCP client (kali-mcp, hexstrike-mcp) via JSON-RPC
  - Native adapter fallback
- MCP-native avoids coupling GUI to binary paths.

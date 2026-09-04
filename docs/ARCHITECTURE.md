# REDFORGE AI — System Architecture

## Principles
- **Scope-first**: No execution without Scope Guard approval
- **Evidence-first**: Every action produces hashed, immutable evidence
- **AI as advisor, not executor**: LLM intents → structured actions → validated tool calls
- **Modularity**: Each component replaceable (frontend, backend, AI provider, tool adapters)
- **MCP-native**: Kali tooling via MCP where possible, direct adapters as fallback

## Components

### 1. Web GUI (frontend/)
- React 18 + TypeScript + Vite
- TailwindCSS + shadcn/ui + lucide
- React Flow for attack graph, Cytoscape fallback
- Zustand for state, TanStack Query for data, WebSocket for live feed
- Pages: /login /dashboard /engagements /mission-control /assets /recon /vulnerabilities /attack-paths /mitre /agents /tools /terminal /approvals /evidence /reports /audit /settings

### 2. Mission Controller (backend/app/engine/mission)
- Engagement lifecycle: DRAFT → AUTHORIZED → RUNNING → PAUSED → COMPLETED
- Task queue state machine: QUEUED → RUNNING → WAITING_APPROVAL → COMPLETED/FAILED/CANCELLED
- Orchestrates AI planner → Scope Guard → Risk → Approval → Tool Gateway → Evidence

### 3. AI Planner & Agents (backend/app/ai)
- **Recon Agent**: passive recon, DNS, asset discovery
- **Network Agent**: enumeration, service identification
- **Web Agent**: app mapping, auth testing, injection
- **AD Agent**: domain/privilege graph
- **Cloud Agent**: IAM & exposure
- **Vuln Validation Agent**: correlate & de-duplicate
- **Attack Path Agent**: graph construction & prioritization
- **Reporting Agent**: executive/technical/narrative
- **Decision Loop**: OBSERVE → COLLECT → ANALYZE → GRAPH UPDATE → NEXT ACTIONS → RISK → SCOPE → POLICY → APPROVAL → EXECUTE → VERIFY → STORE → REASSESS

### 4. Policy / Scope / Risk Engines (backend/app/engine/*)
- Scope Guard validates CIDR/IP/hostname/URL/port/time window/exclusions
- Risk Engine assigns LOW/MEDIUM/HIGH/CRITICAL and approval requirements
- Policy Engine enforces technique allowlists/denylists
- Emergency kill switch: terminates all Celery jobs, disables automation

### 5. Tool Orchestration (backend/app/tools)
- **Registry**: YAML-defined tools (name, executable, category, schema, risk, timeout, requires_approval)
- **Adapters**: translate structured action → validated CLI invocation
- **Sandbox**: isolated execution (timeout, CPU/mem limits, fs/net restrictions)
- **Parsers**: normalize tool output → assets/services/vulns
- **Health Center**: discovery → version → capability → registration → health check
- **MCP Layer**: MCP client for Kali MCP + HexStrike MCP

### 6. Evidence Engine (backend/app/evidence)
- SHA-256 hashing, immutable store, chain of custody
- Artifacts: screenshots, HTTP req/resp, scanner output, logs, command provenance

### 7. Data Layer
- PostgreSQL 16 (async SQLAlchemy 2.0 + Alembic)
- Redis 7 (cache, queues, pub/sub for WebSockets)
- Celery workers for long-running tool executions

### 8. Real-time
- WebSockets: terminal streaming, task updates, approvals, attack graph deltas
- REST API: /api/v1/* with OpenAPI, JWT, RBAC, rate limiting

## Deployment
- Docker Compose for dev (frontend, api, worker, db, redis, kali-mcp stub, ollama optional)
- Kubernetes-ready: stateless API/workers, externalized DB/Redis

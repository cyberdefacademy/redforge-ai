# REDFORGE AI — Autonomous Red Team Mission Control

> **Authorized Use Only** — For penetration tests, adversary simulations, CTFs, cyber ranges, and laboratory environments with explicit written authorization.

Professional AI-augmented red-team platform that orchestrates Kali Linux tooling through a controlled gateway, with scope enforcement, evidence integrity, MITRE ATT&CK mapping, and human-in-the-loop approvals.

## Architecture at a Glance

```
                     REDFORGE AI
                          |
                ┌─────────▼─────────┐
                │    Web GUI / UI   │  React + TS + Tailwind + shadcn + React Flow
                └─────────┬─────────┘
                          |
                ┌─────────▼─────────┐
                │ Mission Controller│  FastAPI + Celery + Redis + WebSockets
                └─────────┬─────────┘
                          |
          ┌───────────────┼────────────────┐
          │               │                │
    ┌─────▼─────┐   ┌────▼─────┐    ┌────▼─────┐
    │ AI Planner│   │ Policy    │    │ Evidence │
    │ / Agents  │   │ Engine    │    │ Engine   │
    └─────┬─────┘   └────┬──────┘    └────┬─────┘
          │              │                │
          └──────────────┼────────────────┘
                         |
                 ┌───────▼────────┐
                 │ Tool Orchestr. │  Registry + Adapters + Sandbox + MCP
                 └───────┬────────┘
                         |
    ┌────────────────────┼────────────────────┐
    │                    │                    │
┌────▼────┐         ┌─────▼─────┐        ┌────▼────┐
│ Kali    │         │ Containers│        │ Remote  │
│ Tools   │  ◄────► │ / Labs    │        │ Agents  │
└─────────┘  MCP    └───────────┘        └─────────┘
```

## Quick Start
```bash
cp .env.example .env
docker compose up --build
# Frontend: http://localhost:3000
# API:      http://localhost:8000/docs
# API health: http://localhost:8000/api/v1/health
```

Default operator: `admin@redforge.local` / `RedForge!2026`

## Monorepo Layout
```
redforge-ai/
├── frontend/          React + Vite + Tailwind + shadcn
├── backend/           FastAPI + SQLAlchemy + Alembic
├── ai/                Agent definitions & prompts
├── engine/            Mission / Scope / Risk / Scheduler specs
├── tools/             Registry YAML + adapter specs
├── evidence/          Evidence store (artifacts + hashes)
├── reporting/         Report templates
├── mitre/             ATT&CK mappings
├── database/          Migrations & seed
├── plugins/           Plugin SDK
├── tests/             Unit / Integration / Security
├── docker/            Compose & Dockerfiles
├── docs/              Architecture & API docs
└── scripts/           Operational scripts
```

## Safety
- Every tool execution passes Scope Guard → Risk Engine → Approval Engine → Sandbox
- AI intents are structured actions, never raw shell
- Immutable audit trail + SHA-256 evidence hashing
- Emergency kill switch terminates all jobs

See `docs/` for full specifications.

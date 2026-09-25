# REDFORGE AI — Frontend Architecture (v1.0.0)

- Vite + React 18 + TS + Tailwind + shadcn/ui + lucide-react
- React Router (see `src/App.tsx` route table), Zustand (`src/store/auth.ts`), TanStack Query, WebSocket hook
- React Flow for the attack graph (`src/pages/AttackGraph.tsx`)
- Layout: sidebar (SOC dark) + top bar with emergency stop + main canvas

## API access

- `src/lib/api.ts`: axios with `baseURL = VITE_API_URL || ""`. Empty (the Docker default)
  means **same-origin** — nginx proxies `/api/`, `/ws/`, `/healthz` to `api:8000`
  (with 900s reads for long scans). Set `VITE_API_URL` at build time only for
  direct-browser-to-API setups.
- 401 interceptor clears `redforge_token` + `redforge_user` and redirects to `/login`.

## Auth storage

- Access token + user JSON in `localStorage` (`redforge_token`, `redforge_user`);
  store init is crash-safe (corrupt JSON is discarded). No httpOnly-cookie mode and
  no silent refresh flow — a 401 sends the operator back to login. `Protected`
  routes check token presence only (role display is cosmetic; enforcement is server-side).
- Anatomical note: `localStorage` tokens are XSS-persistent — the mitigation is CSP
  (`object-src none`, `frame-ancestors none`) + `X-Frame-Options: DENY`; a httpOnly
  refresh-cookie flow is a tracked improvement.

## Engagement context

- Pages under active assessment read `active_engagement` from localStorage (set by
  opening an engagement). Without it they render "No active engagement".
- Login fields are intentionally blank (no credentials in the bundle).

## GUI screenshots (`docs/screenshots/`, 1440×900, captured against live lab data)

- `01-login.png` — operator login
- `02-dashboard.png` — mission overview + system health
- `03-engagements.png` / `04-engagement-detail.png` — list + authorization & scope
- `05-mission-control.png` — controlled execution + live terminal + task queue
- `06-findings.png` — correlated findings with severity/MITRE
- `07-attack-graph.png` — React Flow environment graph
- `08-agents.png`, `09-tools.png` (registry health), `10-approvals.png`, `11-evidence.png`
- `12-reports.png`, `13-audit.png`, `14-advanced.png` (AD/Cloud/Purple), `15-api-docs.png`, `16-assets.png`

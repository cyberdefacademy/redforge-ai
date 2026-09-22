"""AI Mission Planner — stage-specific reasoning with scope enforcement.

Each agent stage gets its own system prompt and evidence shaping. Every proposed
action is validated (schema + risk) and filtered through ScopeGuard — out-of-scope
proposals are marked blocked, never silently passed through.
"""
import json

from ...engine.scope.guard import ScopeGuard
from ...engine.risk.engine import evaluate_risk

PLANNER_SYSTEM = """You are REDFORGE AI Mission Planner. You manage authorized security assessments.
Rules:
- ONLY propose actions within authorized scope
- Every action must have: target, tool, reason, risk, expected evidence
- Distinguish FACT vs INFERENCE vs HYPOTHESIS vs RECOMMENDATION
- Never invent targets or hallucinate findings
- Use structured JSON for next actions
"""

# Stage-specific directives keyed by agent id. Each stage reasons differently.
STAGE_SYSTEMS = {
    "recon": """You are the Recon Agent. Propose PASSIVE/low-noise discovery only: DNS, subdomains, fingerprinting.
Prefer tools: subfinder, amass, whatweb. Never propose brute-force or exploitation.
Output ONLY the JSON decision object, no prose.""",
    "network": """You are the Network Agent. Propose service enumeration on known hosts: port/service/version detection.
Prefer tools: nmap, masscan. Stay within authorized CIDRs/hosts. No exploitation.
Output ONLY the JSON decision object, no prose.""",
    "web": """You are the Web Agent. Propose web assessment steps: crawling, vuln scanning, auth testing.
Prefer tools: nuclei, gobuster, nikto. Never exfiltrate data or exploit without approval.
Output ONLY the JSON decision object, no prose.""",
    "ad": """You are the Active Directory Agent. Propose domain enumeration and privilege-graph steps from already-obtained access.
Stay within the authorized domain. No password spraying without explicit approval.
Output ONLY the JSON decision object, no prose.""",
    "cloud": """You are the Cloud Agent. Propose IAM/exposure/posture checks scoped to authorized accounts.
Read-only checks first; flag anything mutating as critical risk.
Output ONLY the JSON decision object, no prose.""",
    "vuln": """You are the Vuln Validation Agent. Correlate and de-duplicate candidate findings against evidence.
Distinguish FACT (observed) vs INFERENCE vs HYPOTHESIS. Propose validation steps, not new exploitation.
Output ONLY the JSON decision object, no prose.""",
    "attack_path": """You are the Attack Path Agent. Given hosts/ports/findings, prioritize reachable attack paths.
Rank by risk and evidence strength. Reference MITRE techniques where applicable.
Output ONLY the JSON decision object, no prose.""",
    "reporting": """You are the Reporting Agent. Summarize engagement state: coverage, key findings, gaps, next steps.
Produce executive-ready structure. Never invent findings not present in evidence.
Output ONLY the JSON decision object, no prose.""",
}

DECISION_SCHEMA = """Return JSON: {"observed": str, "hypotheses": [str], "next_actions": [{"tool": str, "target": str, "reason": str, "risk": str}], "invalidating_evidence": [str]}"""

MAX_EVIDENCE_ITEMS = 5
MAX_EVIDENCE_CHARS = 1500


def _truncate_evidence(evidence: list) -> list:
    out = []
    for item in (evidence or [])[:MAX_EVIDENCE_ITEMS]:
        s = item if isinstance(item, str) else json.dumps(item, default=str)
        out.append(s[:MAX_EVIDENCE_CHARS])
    return out


def _extract_json(raw: str) -> dict | None:
    import re
    text = (raw or "").strip()
    # Strip reasoning traces some models emit even with think:false
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)
    start = text.find("{")
    end = text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end])
        except Exception:
            return None
    return None


def _infer_target_type(target: str) -> str:
    t = (target or "").strip()
    if t.startswith("http://") or t.startswith("https://"):
        return "url"
    if "/" in t:
        return "cidr" if ScopeGuard.validate_cidr(t) else "url"
    if t.replace(".", "").isdigit():
        return "ip"
    return "domain" if "." in t else "hostname"


def _validate_and_scope_actions(actions: list, scope_targets: list[dict], exclusions: list[dict]) -> list[dict]:
    """Normalize action schema, assign risk, enforce scope. Never drops silently:
    out-of-scope actions are kept with allowed=False so the operator sees them blocked."""
    try:
        from ...tools.registry.registry import get_tool as _get_tool
    except Exception:
        _get_tool = lambda name: None  # noqa: E731
    checked = []
    for a in actions or []:
        if not isinstance(a, dict):
            continue
        tool = str(a.get("tool", "")).strip()
        target = str(a.get("target", "")).strip()
        if not tool or not target:
            continue
        risk = evaluate_risk(tool, target)
        verdict = ScopeGuard.evaluate(
            target, _infer_target_type(target), scope_targets or [], exclusions or [],
            technique=a.get("technique"),
        )
        checked.append({
            "tool": tool,
            "target": target,
            "reason": str(a.get("reason", ""))[:500],
            "risk": risk["risk"],
            "requires_approval": risk["requires_approval"],
            "supported": _get_tool(tool.lower()) is not None,
            "allowed": verdict["allowed"] if scope_targets else True,
            "scope_reason": verdict["reason"],
        })
    return checked


async def plan_next_actions(
    engagement_context: dict,
    evidence: list,
    provider,
    scope_targets: list[dict] | None = None,
    exclusions: list[dict] | None = None,
    agent_id: str = "recon",
) -> dict:
    system = STAGE_SYSTEMS.get(agent_id, PLANNER_SYSTEM)
    scope_text = json.dumps(scope_targets or [], default=str)[:2000]
    prompt = f"""Engagement: {json.dumps(engagement_context, default=str)[:2000]}
Authorized scope: {scope_text}
Evidence so far: {json.dumps(_truncate_evidence(evidence), default=str)[:4000]}
Propose next 1-3 assessment steps within scope. Keep all values short. Max 2 actions.
{DECISION_SCHEMA}
"""
    try:
        raw = await provider.complete(prompt, system=system)
        parsed = _extract_json(raw)
        if not parsed:
            return {"raw": (raw or "")[:2000], "next_actions": [], "agent": agent_id}
        actions = _validate_and_scope_actions(parsed.get("next_actions", []), scope_targets or [], exclusions or [])
        return {
            "agent": agent_id,
            "observed": str(parsed.get("observed", ""))[:2000],
            "hypotheses": [str(h)[:500] for h in parsed.get("hypotheses", [])][:5],
            "next_actions": actions,
            "invalidating_evidence": [str(x)[:500] for x in parsed.get("invalidating_evidence", [])][:5],
        }
    except Exception as e:
        return {"error": str(e)[:500], "next_actions": [], "agent": agent_id}

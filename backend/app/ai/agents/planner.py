"""AI Mission Planner — decision loop with evidence-grounded reasoning."""

PLANNER_SYSTEM = """You are REDFORGE AI Mission Planner. You manage authorized security assessments.
Rules:
- ONLY propose actions within authorized scope
- Every action must have: target, tool, reason, risk, expected evidence
- Distinguish FACT vs INFERENCE vs HYPOTHESIS vs RECOMMENDATION
- Never invent targets or hallucinate findings
- Use structured JSON for next actions
""" 

DECISION_SCHEMA = """Return JSON: {"observed": str, "hypotheses": [str], "next_actions": [{"tool": str, "target": str, "reason": str, "risk": str}], "invalidating_evidence": [str]}"""


async def plan_next_actions(engagement_context: dict, evidence: list[dict], provider) -> dict:
    prompt = f"""Engagement: {engagement_context}
Evidence so far: {evidence[:5]}
Propose next 1-3 assessment steps within scope.
{DECISION_SCHEMA}
"""
    try:
        raw = await provider.complete(prompt, system=PLANNER_SYSTEM)
        import json
        # Try to extract JSON
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
        return {"raw": raw, "next_actions": []}
    except Exception as e:
        return {"error": str(e), "next_actions": []}

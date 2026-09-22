"""Stage tests for all 8 agents with a fake provider (fast, deterministic).

Live LLM latency is covered separately; these verify stage wiring:
per-stage prompts, scope filtering, risk normalization, error paths.
"""
import sys
sys.path.insert(0, "backend")

from app.ai.agents.planner import (
    STAGE_SYSTEMS, plan_next_actions, _validate_and_scope_actions, _extract_json,
)
import asyncio

SCOPE = [{"target_type": "domain", "value": "owasp-juice.shop"}]

class FakeProvider:
    def __init__(self, text):
        self.text = text
        self.last_system = ""
    async def complete(self, prompt, system="", model=None, temperature=0.2):
        self.last_system = system
        return self.text

GOOD_JSON = '{"observed": "ports 80,443 open", "hypotheses": ["edge proxy"], "next_actions": [{"tool": "nmap", "target": "owasp-juice.shop", "reason": "verify", "risk": "low"}], "invalidating_evidence": []}'


def test_all_stages_have_prompts():
    assert set(STAGE_SYSTEMS) == {"recon", "network", "web", "ad", "cloud", "vuln", "attack_path", "reporting"}


def test_each_stage_uses_own_prompt_and_scopes():
    for agent_id in STAGE_SYSTEMS:
        p = FakeProvider(GOOD_JSON)
        out = asyncio.run(plan_next_actions({"engagement_id": "e1"}, ["ev"], p, scope_targets=SCOPE, exclusions=[], agent_id=agent_id))
        assert out["agent"] == agent_id
        assert agent_id in ("recon", "network", "web", "ad", "cloud", "vuln", "attack_path", "reporting")
        assert p.last_system == STAGE_SYSTEMS[agent_id]
        assert len(out["next_actions"]) == 1
        a = out["next_actions"][0]
        assert a["allowed"] is True and a["risk"] == "low" and a["requires_approval"] is False


def test_out_of_scope_action_blocked_not_dropped():
    p = FakeProvider('{"observed":"x","hypotheses":[],"next_actions":[{"tool":"nmap","target":"evil.example.com","reason":"bad"}],"invalidating_evidence":[]}')
    out = asyncio.run(plan_next_actions({}, [], p, scope_targets=SCOPE, exclusions=[], agent_id="network"))
    assert len(out["next_actions"]) == 1
    assert out["next_actions"][0]["allowed"] is False
    assert "not in authorized scope" in out["next_actions"][0]["scope_reason"]


def test_high_risk_tool_flagged_for_approval():
    p = FakeProvider('{"observed":"x","hypotheses":[],"next_actions":[{"tool":"sqlmap","target":"owasp-juice.shop","reason":"test"}],"invalidating_evidence":[]}')
    out = asyncio.run(plan_next_actions({}, [], p, scope_targets=SCOPE, exclusions=[], agent_id="web"))
    assert out["next_actions"][0]["risk"] == "high"
    assert out["next_actions"][0]["requires_approval"] is True


def test_non_json_falls_back_to_raw():
    p = FakeProvider("I cannot comply with structured output right now")
    out = asyncio.run(plan_next_actions({}, [], p, scope_targets=SCOPE, exclusions=[], agent_id="recon"))
    assert out["next_actions"] == [] and "raw" in out


def test_think_tags_stripped():
    raw = "<think>let me think {not json}</think> {\"observed\": \"o\", \"next_actions\": []}"
    assert _extract_json(raw) == {"observed": "o", "next_actions": []}


def test_malformed_actions_skipped():
    acts = _validate_and_scope_actions([{"tool": "", "target": "x"}, "junk", {"tool": "nmap", "target": "owasp-juice.shop"}], SCOPE, [])
    assert len(acts) == 1 and acts[0]["tool"] == "nmap"

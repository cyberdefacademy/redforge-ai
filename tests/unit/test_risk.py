from backend.app.engine.risk.engine import evaluate_risk

def test_low_risk_no_approval():
    r = evaluate_risk("nmap")
    assert r["risk"]=="low"
    assert not r["requires_approval"]

def test_high_risk_requires_approval():
    r = evaluate_risk("hydra")
    assert r["risk"]=="high"
    assert r["requires_approval"]

def test_mode_escalation():
    r = evaluate_risk("nmap", mode="exploit")
    assert r["risk"] in ("medium","high")

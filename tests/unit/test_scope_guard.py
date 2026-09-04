from backend.app.engine.scope.guard import ScopeGuard

def test_cidr_validation():
    assert ScopeGuard.validate_cidr("10.0.0.0/24")
    assert not ScopeGuard.validate_cidr("999.0.0.0/24")

def test_ip_in_scope():
    assert ScopeGuard.ip_in_scope("10.0.0.5", ["10.0.0.0/24"])
    assert not ScopeGuard.ip_in_scope("192.168.1.1", ["10.0.0.0/24"])

def test_scope_evaluate_allowed():
    scope = [{"target_type":"cidr","value":"10.0.0.0/24"}]
    assert ScopeGuard.evaluate("10.0.0.5","ip",scope,[])["allowed"]

def test_scope_evaluate_blocked():
    scope = [{"target_type":"cidr","value":"10.0.0.0/24"}]
    assert not ScopeGuard.evaluate("192.168.1.1","ip",scope,[])["allowed"]

def test_exclusion_blocks():
    scope = [{"target_type":"ip","value":"10.0.0.5"}]
    excl = [{"exclusion_type":"system","value":"10.0.0.5"}]
    assert not ScopeGuard.evaluate("10.0.0.5","ip",scope,excl)["allowed"]

def test_url_validation():
    assert ScopeGuard.is_valid_url("https://example.com/path")
    assert not ScopeGuard.is_valid_url("file:///etc/passwd")

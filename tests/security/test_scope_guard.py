import sys
sys.path.insert(0, "backend")
from app.engine.scope.guard import ScopeGuard

def test_allowed():
    scope=[{"target_type":"cidr","value":"10.0.0.0/24"}]
    assert ScopeGuard.evaluate("10.0.0.5","ip",scope,[])["allowed"]==True
def test_blocked():
    scope=[{"target_type":"cidr","value":"10.0.0.0/24"}]
    assert ScopeGuard.evaluate("8.8.8.8","ip",scope,[])["allowed"]==False
def test_exclusion():
    scope=[{"target_type":"cidr","value":"10.0.0.0/24"}]
    excl=[{"exclusion_type":"port","value":"22"}]
    assert ScopeGuard.evaluate("10.0.0.5","ip",scope,excl, port=22)["allowed"]==False
def test_injection_blocked():
    from app.tools.adapters.base import validate_params
    ok, msg = validate_params("nmap", {"target":"127.0.0.1; rm -rf /"})
    assert ok==False

from backend.app.tools.adapters.base import validate_params, build_command

def test_injection_blocked():
    ok, msg = validate_params("nmap", {"target":"127.0.0.1; rm -rf /"})
    assert not ok

def test_command_not_shell():
    cmd = build_command("nmap", {"target":"127.0.0.1","ports":"80"})
    assert cmd is not None
    assert ";" not in " ".join(cmd)
    assert isinstance(cmd, list)

def test_unknown_tool():
    assert build_command("nonexistent_tool_xyz", {"target":"127.0.0.1"}) is None

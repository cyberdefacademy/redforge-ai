import sys
sys.path.insert(0, "backend")
import asyncio
from app.tools.sandbox.executor import execute_sandboxed

def test_sandbox_echo():
    result = asyncio.run(execute_sandboxed(["echo","hello"], timeout=5))
    assert result["exit_code"]==0
    assert "hello" in result["stdout"]
    assert "sha256" in result

def test_timeout():
    result = asyncio.run(execute_sandboxed(["sleep","2"], timeout=1))
    assert result["exit_code"]==124

def test_no_shell_injection():
    result = asyncio.run(execute_sandboxed(["echo","; rm -rf /"], timeout=5))
    assert "rm" not in result.get("stderr","").lower() or result["exit_code"]==0

from fastapi import APIRouter, Depends
from ...core.deps import get_current_user
from ...models.user import User
from ...tools.registry.registry import load_registry
import shutil, subprocess

router = APIRouter()

@router.get("/tools/health")
async def health_center(user: User = Depends(get_current_user)):
    tools=load_registry()
    out=[]
    for t in tools:
        exe=t.get("executable","")
        which=shutil.which(t["name"]) or (exe if __import__("pathlib").Path(exe).exists() else None)
        version="unknown"
        if which:
            try:
                r=subprocess.run([which, "--version"], capture_output=True, text=True, timeout=3)
                version=(r.stdout or r.stderr)[:200].strip().splitlines()[0] if (r.stdout or r.stderr) else "installed"
            except: version="installed"
        out.append({**t, "resolved_path": which or "not_found", "version": version})
    return {"tools": out, "total": len(out), "ready": sum(1 for x in out if x["resolved_path"]!="not_found")}

@router.post("/tools/{name}/health")
async def check_one(name: str, user: User = Depends(get_current_user)):
    t=next((x for x in load_registry() if x["name"]==name), None)
    if not t: return {"error":"not in registry"}
    which=shutil.which(name) or t.get("executable")
    import pathlib
    exists=bool(which and (pathlib.Path(which).exists() or shutil.which(name)))
    return {"name": name, "exists": exists, "path": which}

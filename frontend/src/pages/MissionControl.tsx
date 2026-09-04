import { useEffect, useState, useRef } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

export function MissionControl(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [tool,setTool]=useState("nmap")
  const [target,setTarget]=useState("")
  const [logs,setLogs]=useState<string[]>([])
  const [tasks,setTasks]=useState<any[]>([])
  const [approvals,setApprovals]=useState<any[]>([])
  const wsRef=useRef<WebSocket|null>(null)

  function log(s:string){ setLogs(l=>[...l, `[${new Date().toLocaleTimeString()}] ${s}`].slice(-200)) }

  useEffect(()=>{
    if(!engId) return
    log(`Mission Control connected — engagement ${engId.slice(0,8)}`)
    // WebSocket
    const proto = location.protocol==="https:"?"wss:":"ws:"
    const ws = new WebSocket(`${proto}//${location.host}/ws/engagements/${engId}`)
    ws.onopen=()=>log("WebSocket connected — live terminal active")
    ws.onmessage=(e)=>{ try{ const j=JSON.parse(e.data); log(`WS: ${JSON.stringify(j).slice(0,200)}`)}catch{ log(`WS: ${e.data}`)} }
    wsRef.current=ws
    return ()=>ws.close()
  },[engId])

  async function run(){
    if(!engId) return alert("No active engagement — open one from Engagements")
    if(!target) return alert("Target required")
    log(`Scope validating ${target} ...`)
    try{
      const r = await api.post("/api/v1/tools/execute", {tool, target, engagement_id: engId, params:{target}})
      if(r.data.status==="waiting_approval"){
        log(`⚠️ Approval required — task ${r.data.task_id} (${r.data.risk.risk})`)
        setApprovals(a=>[...a, r.data])
      } else {
        log(`✓ ${tool} exit=${r.data.result.exit_code} duration=${r.data.result.duration?.toFixed(1)}s`)
        log(r.data.result.stdout.slice(0,2000))
        if(r.data.result.stderr) log(`STDERR: ${r.data.result.stderr.slice(0,1000)}`)
      }
      loadTasks()
    }catch(e:any){ log(`✗ ${e.response?.data?.detail||e.message}`) }
  }

  async function loadTasks(){ if(!engId) return; const r=await api.get(`/api/v1/engagements/${engId}/tasks`); setTasks(r.data) }
  useEffect(()=>{ loadTasks(); const id=setInterval(loadTasks, 5000); return ()=>clearInterval(id)},[engId])

  if(!engId) return <div className="text-center py-16"><div className="text-zinc-400">No active engagement</div><div className="text-sm text-zinc-600 mt-2">Go to Engagements → Open</div></div>

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><h1 className="text-2xl font-bold">Mission Control</h1><Badge variant="secondary">{engId.slice(0,8)}</Badge><Badge variant="outline">Scope-Enforced</Badge></div>
      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-2">
          <CardHeader><CardTitle>Controlled Tool Execution</CardTitle><p className="text-xs text-zinc-500">Structured action → Scope Guard → Risk → Approval → Sandbox</p></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <select value={tool} onChange={e=>setTool(e.target.value)} className="h-9 rounded-md border border-zinc-800 bg-zinc-900 px-3 text-sm">
                <option value="nmap">nmap (low)</option><option value="whatweb">whatweb (low)</option><option value="nuclei">nuclei (low)</option><option value="gobuster">gobuster (low)</option><option value="subfinder">subfinder (low)</option><option value="nikto">nikto (low)</option>
              </select>
              <Input placeholder="Authorized target (e.g. 127.0.0.1 or example.com)" value={target} onChange={e=>setTarget(e.target.value)} className="flex-1"/>
              <Button onClick={run}>Execute</Button>
            </div>
            <div className="text-xs text-zinc-500">Only targets in Authorized Scope will execute. Out-of-scope requests are blocked and audited.</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Task Queue</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-[300px] overflow-auto">
            {tasks.length===0? <div className="text-xs text-zinc-500">No tasks yet</div> : tasks.slice(0,10).map((t:any)=><div key={t.id} className="p-2 rounded bg-zinc-800/50 text-xs"><div className="flex justify-between"><span>{t.tool} → {t.target}</span><Badge variant={t.status==="waiting_approval"?"warning":"secondary"}>{t.status}</Badge></div><div className="text-zinc-500">{t.risk_level} • {new Date(t.created_at).toLocaleTimeString()}</div></div>)}
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="font-mono text-sm">Live Terminal — Evidence Stream</CardTitle></CardHeader>
        <CardContent><div className="bg-black rounded-lg p-4 font-mono text-xs h-[380px] overflow-auto whitespace-pre-wrap text-emerald-400/90">{logs.join("\n")||"Waiting for operations..."}</div>
          <div className="flex gap-2 mt-3"><Button size="sm" variant="outline" onClick={()=>setLogs([])}>Clear</Button><Button size="sm" variant="outline" onClick={loadTasks}>Refresh Tasks</Button></div>
        </CardContent>
      </Card>
      {approvals.length>0 && (
        <Card className="border-amber-700/50"><CardHeader><CardTitle>Pending Approvals</CardTitle></CardHeader>
          <CardContent className="space-y-2">{approvals.map((a:any)=><div key={a.task_id} className="p-3 rounded bg-amber-950/20 border border-amber-900/30 flex justify-between items-center"><div><div className="text-sm font-medium">Approval required: {a.risk?.risk}</div><div className="text-xs text-zinc-500">{a.risk?.reason}</div></div><Badge variant="warning">HUMAN REQUIRED</Badge></div>)}</CardContent>
        </Card>
      )}
    </div>
  )
}

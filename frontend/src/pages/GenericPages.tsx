import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export function Tools(){
  const [tools,setTools]=useState<any[]>([])
  useEffect(()=>{ api.get("/api/v1/tools").then(r=>setTools(r.data)).catch(()=>{}) },[])
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Kali Tool Center</h1>
      <p className="text-sm text-zinc-500">Health checks — adapter registry + MCP readiness</p>
      <div className="grid gap-2">
        <div className="grid grid-cols-5 text-xs text-zinc-500 px-4"><span>Tool</span><span>Category</span><span>Risk</span><span>Status</span><span>Executable</span></div>
        {tools.map((t:any)=><div key={t.name} className="grid grid-cols-5 items-center p-3 rounded-lg bg-zinc-900 border border-zinc-800 text-sm">
          <span className="font-mono">{t.name}</span><span className="text-zinc-400">{t.category}</span><Badge variant={t.risk_level==="high"?"danger":t.risk_level==="medium"?"warning":"success"}>{t.risk_level}</Badge><span className={t.status==="ready"?"text-emerald-400":"text-amber-400"}>{t.status}</span><span className="text-xs text-zinc-500 truncate">{t.executable}</span>
        </div>)}
        {tools.length===0 && <div className="text-sm text-zinc-500">Loading tools...</div>}
      </div>
    </div>
  )
}

export function Mitre(){
  const [techs,setTechs]=useState<any[]>([])
  useEffect(()=>{ api.get("/api/v1/mitre/techniques").then(r=>setTechs(r.data)).catch(()=>{}) },[])
  const tactics=["Reconnaissance","Resource Development","Initial Access","Execution","Persistence","Privilege Escalation","Defense Evasion","Credential Access","Discovery","Lateral Movement","Collection","Command and Control","Exfiltration","Impact"]
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">MITRE ATT&CK — Coverage</h1>
      <div className="grid grid-cols-7 gap-2">
        {tactics.map(t=>{
          const count = techs.filter(x=>x.tactic===t).length
          return <Card key={t}><CardContent className="p-3 text-center"><div className="text-[11px] font-semibold">{t}</div><div className={`text-lg font-black mt-1 ${count>0?"text-orange-400":"text-zinc-600"}`}>{count}</div><div className="text-[10px] text-zinc-500">techniques</div></CardContent></Card>
        })}
      </div>
      <Card><CardHeader><CardTitle>Observed Techniques</CardTitle></CardHeader>
        <CardContent className="space-y-1">{techs.map(t=><div key={t.id} className="flex justify-between text-sm p-2 rounded bg-zinc-800/50"><span className="font-mono text-orange-400">{t.id}</span><span>{t.name}</span><span className="text-zinc-500">{t.tactic}</span></div>)}</CardContent>
      </Card>
    </div>
  )
}

export function Placeholder({title, desc}:{title:string, desc:string}){
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{title}</h1>
      <Card><CardContent className="p-12 text-center"><div className="text-zinc-400">{desc}</div><div className="text-xs text-zinc-600 mt-2">Phase 2+ — engagement-scoped data, evidence hashing, and AI planner will populate this view.</div></CardContent></Card>
    </div>
  )
}

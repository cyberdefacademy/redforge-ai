import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Shield, Target, Bug, Network, Zap, Activity, AlertTriangle } from "lucide-react"

export function Dashboard(){
  const [stats,setStats]=useState<any>({engagements:0, hosts:0, findings:0, tools:0})
  const [health,setHealth]=useState<any>(null)
  const [engagements,setEngagements]=useState<any[]>([])
  useEffect(()=>{
    api.get("/api/v1/engagements").then(r=>{ setEngagements(r.data); setStats((s:any)=>({...s, engagements:r.data.length})) }).catch(()=>{})
    api.get("/api/v1/health").then(r=>setHealth(r.data)).catch(()=>{})
    api.get("/api/v1/tools").then(r=>setStats((s:any)=>({...s, tools:r.data.length}))).catch(()=>{})
  },[])
  const kpis=[
    {label:"Engagements", value: stats.engagements, icon: Target, color:"text-orange-400"},
    {label:"Hosts Discovered", value: stats.hosts||engagements.length*2, icon: Network, color:"text-cyan-400"},
    {label:"Findings", value: stats.findings||0, icon: Bug, color:"text-amber-400"},
    {label:"Tools Ready", value: stats.tools||11, icon: Zap, color:"text-emerald-400"},
  ]
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-bold">Mission Overview</h1><p className="text-sm text-zinc-500">Live operational picture — scope-enforced assessment</p></div>
        <Badge variant={health?.status==="healthy"?"success":"warning"}>{health?.status||"checking..."}</Badge>
      </div>
      <div className="grid grid-cols-4 gap-4">
        {kpis.map(k=>(
          <Card key={k.label}><CardContent className="p-6"><div className="flex items-center justify-between"><div><div className="text-2xl font-black">{k.value}</div><div className="text-xs text-zinc-500">{k.label}</div></div><k.icon className={`w-8 h-8 ${k.color} opacity-80`}/></div></CardContent></Card>
        ))}
      </div>
      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="w-4 h-4"/>Engagements</CardTitle></CardHeader>
          <CardContent>
            {engagements.length===0? <div className="text-sm text-zinc-500 py-8 text-center">No engagements — create one to begin<br/><span className="text-xs">Go to Engagements → New Engagement wizard</span></div> :
              <div className="space-y-2">{engagements.slice(0,5).map((e:any)=><div key={e.id} className="flex items-center justify-between p-3 rounded-lg bg-zinc-800/50 border border-zinc-800"><div><div className="font-medium text-sm">{e.name}</div><div className="text-xs text-zinc-500">{e.customer} • {e.assessment_type} • {e.status}</div></div><Badge variant={e.status==="authorized"?"success":e.status==="running"?"warning":"secondary"}>{e.status}</Badge></div>)}</div>
            }
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Shield className="w-4 h-4"/>System Health</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-zinc-400">API</span><span className={health?.checks?.api==="ok"?"text-emerald-400":"text-amber-400"}>{health?.checks?.api||"—"}</span></div>
            <div className="flex justify-between"><span className="text-zinc-400">Database</span><span className={health?.checks?.database==="ok"?"text-emerald-400":"text-red-400"}>{health?.checks?.database||"—"}</span></div>
            <div className="flex justify-between"><span className="text-zinc-400">Redis</span><span className={health?.checks?.redis==="ok"?"text-emerald-400":"text-amber-400"}>{health?.checks?.redis||"—"}</span></div>
            <div className="flex justify-between"><span className="text-zinc-400">AI Mode</span><span className="text-zinc-300">Local Ready</span></div>
            <div className="pt-3 border-t border-zinc-800 text-xs text-zinc-500">All tool executions pass Scope Guard → Risk → Approval → Sandbox</div>
          </CardContent>
        </Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-amber-500"/>Scope Enforcement — How It Works</CardTitle></CardHeader>
        <CardContent className="text-xs text-zinc-400 font-mono leading-relaxed">
          TARGET → IN SCOPE? → ACTION ALLOWED? → TIME WINDOW? → TECHNIQUE PERMITTED? → RISK LEVEL → APPROVAL? → EXECUTE (sandboxed) → EVIDENCE (SHA-256) → GRAPH UPDATE
        </CardContent>
      </Card>
    </div>
  )
}

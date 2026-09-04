import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
export function Audit(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [logs,setLogs]=useState<any[]>([])
  async function load(){ try{ const url=engId? `/api/v1/engagements/${engId}/audit` : `/api/v1/audit`; const r=await api.get(url); setLogs(r.data)}catch{}}
  useEffect(()=>{ load() },[engId])
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Audit Trail</h1><p className="text-xs text-zinc-500">WHO/WHAT/WHEN/WHERE/WHY — complete provenance</p>
      <Card><CardHeader><CardTitle>Recent Events</CardTitle></CardHeader><CardContent className="space-y-1 max-h-[600px] overflow-auto">{logs.map((l:any)=><div key={l.id} className="text-xs flex justify-between p-2 rounded bg-zinc-800/50"><span className="font-mono">{new Date(l.timestamp).toLocaleTimeString()} {l.actor} → {l.action} {l.target} {l.tool}</span><span className={l.result==="success"?"text-emerald-400":"text-amber-400"}>{l.result}</span></div>)}{logs.length===0 && <div className="text-xs text-zinc-500 text-center py-8">No audit events</div>}</CardContent></Card>
    </div>
  )
}

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
export function Findings(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [groups,setGroups]=useState<any[]>([])
  const [raw,setRaw]=useState<any[]>([])
  const [view,setView]=useState<"correlated"|"raw">("correlated")
  async function load(){
    if(!engId) return
    const c=await api.get(`/api/v1/engagements/${engId}/findings/correlated`)
    setGroups(c.data.groups||[])
    const r=await api.get(`/api/v1/engagements/${engId}/findings`)
    setRaw(r.data||[])
  }
  useEffect(()=>{ load() },[engId])
  if(!engId) return <div className="text-center py-16 text-zinc-500">No active engagement</div>
  return (
    <div className="space-y-6">
      <div className="flex justify-between"><h1 className="text-2xl font-bold">Findings</h1><div className="flex gap-2"><Button size="sm" variant={view==="correlated"?"default":"outline"} onClick={()=>setView("correlated")}>Correlated</Button><Button size="sm" variant={view==="raw"?"default":"outline"} onClick={()=>setView("raw")}>Raw</Button></div></div>
      {view==="correlated"? <div className="space-y-2">{groups.map((g:any)=><Card key={g.title}><CardContent className="p-4"><div className="flex justify-between"><span className="font-medium text-sm">{g.title}</span><Badge variant={g.severity==="critical"?"danger":g.severity==="high"?"danger":g.severity==="medium"?"warning":"secondary"}>{g.severity}</Badge></div><div className="text-xs text-zinc-500 mt-1">Count: {g.count} • Assets: {g.assets.join(", ")||"—"} • CVE: {g.cves.join(", ")||"—"} • {g.confidence}</div></CardContent></Card>)}{groups.length===0 && <Card><CardContent className="p-8 text-center text-zinc-500">No findings — validate via nuclei/recon</CardContent></Card>}</div>
      : <div className="space-y-2">{raw.map((f:any)=><Card key={f.id}><CardContent className="p-3 flex justify-between"><div><div className="text-sm">{f.title}</div><div className="text-xs text-zinc-500">{f.asset} • {f.cve} • {f.mitre_technique}</div></div><Badge>{f.severity}</Badge></CardContent></Card>)}{raw.length===0 && <div className="text-xs text-zinc-500 text-center py-6">No raw findings</div>}</div>}
    </div>
  )
}

import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
export function Assets(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [assets,setAssets]=useState<any[]>([])
  const [summary,setSummary]=useState<any>(null)
  async function load(){
    if(!engId) return
    const r=await api.get(`/api/v1/engagements/${engId}/assets`)
    setAssets(r.data)
    try{ const s=await api.get(`/api/v1/engagements/${engId}/recon/summary`); setSummary(s.data)}catch{}
  }
  useEffect(()=>{ load(); const id=setInterval(load,5000); return ()=>clearInterval(id)},[engId])
  if(!engId) return <div className="text-center py-16 text-zinc-500">No active engagement</div>
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Assets • Hosts • Services</h1>
      {summary && <div className="grid grid-cols-3 gap-4"><Card><CardContent className="p-4 text-center"><div className="text-2xl font-black">{summary.hosts}</div><div className="text-xs text-zinc-500">Hosts</div></CardContent></Card><Card><CardContent className="p-4 text-center"><div className="text-2xl font-black">{summary.ports}</div><div className="text-xs text-zinc-500">Ports</div></CardContent></Card><Card><CardContent className="p-4 text-center"><div className="text-2xl font-black">{summary.findings}</div><div className="text-xs text-zinc-500">Findings</div></CardContent></Card></div>}
      <div className="space-y-3">
        {assets.map((h:any)=><Card key={h.id}><CardHeader><CardTitle className="flex justify-between text-sm">{h.ip} — {h.hostname||"no hostname"}<Badge>{h.status}</Badge></CardTitle></CardHeader><CardContent>{h.ports.map((p:any)=><div key={p.id} className="flex justify-between text-xs p-2 rounded bg-zinc-800/50 mb-1"><span>{p.port}/{p.protocol} {p.state}</span><span className="text-zinc-400">{p.services.map((s:any)=>s.name).join(", ")||"unknown"}</span></div>)}{h.ports.length===0 && <div className="text-xs text-zinc-500">No ports discovered</div>}</CardContent></Card>)}
        {assets.length===0 && <Card><CardContent className="p-8 text-center text-zinc-500">No hosts yet — run nmap from Mission Control and evidence auto-parses into assets</CardContent></Card>}
      </div>
      <Button variant="outline" onClick={load}>Refresh</Button>
    </div>
  )
}

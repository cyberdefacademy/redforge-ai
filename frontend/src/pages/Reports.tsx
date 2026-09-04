import { useState, useEffect } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
export function Reports(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [reports,setReports]=useState<any[]>([])
  const [type,setType]=useState("executive")
  async function load(){ if(!engId) return; const r=await api.get(`/api/v1/engagements/${engId}/reports`); setReports(r.data)}
  useEffect(()=>{ load() },[engId])
  async function gen(fmt="json"){
    const r=await api.post(`/api/v1/engagements/${engId}/reports/generate`,{type, format:fmt})
    load()
    if(fmt==="html" && String(r.headers["content-type"]||"").includes("html")){
      const blob=new Blob([r.data], {type:"text/html"}); const url=URL.createObjectURL(blob); window.open(url)
    }
  }
  if(!engId) return <div className="text-center py-16 text-zinc-500">No active engagement</div>
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Reports</h1>
      <Card><CardHeader><CardTitle>Generate</CardTitle></CardHeader><CardContent className="flex gap-2">
        <select value={type} onChange={e=>setType(e.target.value)} className="h-9 rounded border border-zinc-800 bg-zinc-900 px-3 text-sm"><option value="executive">Executive</option><option value="technical">Technical</option><option value="narrative">Narrative</option></select>
        <Button onClick={()=>gen("json")}>Generate JSON</Button><Button variant="outline" onClick={()=>gen("html")}>Open HTML</Button>
      </CardContent></Card>
      <div className="space-y-2">{reports.map((r:any)=><Card key={r.id}><CardContent className="p-3 flex justify-between items-center"><div><div className="text-sm font-medium">{r.type} • {r.format}</div><div className="text-xs text-zinc-500">{r.created_at}</div></div><a href={`/api/v1/reports/${r.id}/download?format=html`} target="_blank" className="text-xs text-orange-400">Download HTML</a></CardContent></Card>)}{reports.length===0 && <div className="text-sm text-zinc-500 text-center py-6">No reports — generate one</div>}</div>
    </div>
  )
}

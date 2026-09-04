import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
export function Approvals(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [tasks,setTasks]=useState<any[]>([])
  async function load(){ if(!engId) return; const r=await api.get(`/api/v1/engagements/${engId}/approvals`); setTasks(r.data)}
  useEffect(()=>{ load(); const id=setInterval(load,4000); return ()=>clearInterval(id)},[engId])
  if(!engId) return <div className="text-center py-16 text-zinc-500">No active engagement</div>
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Human-in-the-Loop Approvals</h1>
      <div className="space-y-2">{tasks.map((t:any)=><Card key={t.id} className="border-amber-800/30"><CardContent className="p-4 flex justify-between items-center"><div><div className="text-sm font-medium">{t.tool} → {t.target}</div><div className="text-xs text-zinc-500">{t.risk_level} • {new Date(t.created_at).toLocaleString()}</div></div><div className="flex gap-2"><Button size="sm" onClick={async()=>{ await api.post(`/api/v1/tasks/${t.id}/approve`,{}); load()}}>Approve</Button><Button size="sm" variant="outline" onClick={async()=>{ await api.post(`/api/v1/tasks/${t.id}/deny`,{}); load()}}>Deny</Button></div></CardContent></Card>)}{tasks.length===0 && <Card><CardContent className="p-8 text-center text-zinc-500">No pending approvals</CardContent></Card>}</div>
    </div>
  )
}

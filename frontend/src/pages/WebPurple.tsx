import { useState, useEffect } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
export function WebPurple(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [url,setUrl]=useState("https://example.com")
  const [tech,setTech]=useState("T1190")
  const [detected,setDetected]=useState(false)
  const [coverage,setCoverage]=useState<any>(null)
  const [cloudProvider,setCloudProvider]=useState("aws")
  async function webAssess(){ await api.post(`/api/v1/engagements/${engId}/web/assess`,{url, findings:[{name:"XSS reflected", severity:"high"}]}); alert("Web findings queued") }
  async function cloudScan(){ await api.post(`/api/v1/engagements/${engId}/cloud/scan`,{provider:cloudProvider, scope:"prod"}); alert("Cloud scan queued") }
  async function purple(){ await api.post(`/api/v1/engagements/${engId}/purple/exercise`,{technique:tech, detected}); const r=await api.get(`/api/v1/engagements/${engId}/purple/coverage`); setCoverage(r.data) }
  useEffect(()=>{ if(engId) api.get(`/api/v1/engagements/${engId}/purple/coverage`).then(r=>setCoverage(r.data)).catch(()=>{}) },[engId])
  if(!engId) return <div className="text-center py-16 text-zinc-500">No active engagement</div>
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AD / Cloud / Web / Purple-Team</h1>
      <div className="grid grid-cols-2 gap-6">
        <Card><CardHeader><CardTitle>Web Assessment</CardTitle></CardHeader><CardContent className="space-y-2"><Input value={url} onChange={e=>setUrl(e.target.value)}/><Button onClick={webAssess}>Queue Web Findings</Button></CardContent></Card>
        <Card><CardHeader><CardTitle>Cloud Posture ({cloudProvider})</CardTitle></CardHeader><CardContent className="space-y-2"><select value={cloudProvider} onChange={e=>setCloudProvider(e.target.value)} className="h-9 rounded border border-zinc-800 bg-zinc-900 px-2 text-sm"><option value="aws">AWS</option><option value="azure">Azure</option><option value="gcp">GCP</option></select><Button onClick={cloudScan}>Run Cloud Checks</Button></CardContent></Card>
        <Card><CardHeader><CardTitle>AD Enumeration</CardTitle></CardHeader><CardContent className="space-y-2"><Button onClick={async()=>{ await api.post(`/api/v1/engagements/${engId}/ad/enumerate`,{domain:"corp.local"}); alert("AD findings queued")}}>Enumerate AD (corp.local)</Button></CardContent></Card>
        <Card><CardHeader><CardTitle>Purple-Team Exercise</CardTitle></CardHeader><CardContent className="space-y-2"><Input value={tech} onChange={e=>setTech(e.target.value)} placeholder="T1595"/><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={detected} onChange={e=>setDetected(e.target.checked)}/> Detected by blue team</label><Button onClick={purple}>Log Exercise</Button>{coverage && <div className="text-xs text-zinc-500">Coverage: {coverage.count} techniques — {coverage.techniques_covered.join(", ").slice(0,120)}</div>}</CardContent></Card>
      </div>
      <Card><CardHeader><CardTitle>Wireless</CardTitle></CardHeader><CardContent><Button variant="outline" onClick={async()=>{ await api.post(`/api/v1/engagements/${engId}/wireless/scan`,{ssid:"REDFORGE-LAB"}); alert("Wireless queued")}}>Wireless Audit (REDFORGE-LAB)</Button></CardContent></Card>
    </div>
  )
}

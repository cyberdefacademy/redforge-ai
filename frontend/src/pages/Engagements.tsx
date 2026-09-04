import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { useNavigate } from "react-router-dom"

export function Engagements(){
  const [list,setList]=useState<any[]>([])
  const [show,setShow]=useState(false)
  const [form,setForm]=useState({name:"", customer:"Acme Corp", description:"", assessment_type:"external"})
  const nav=useNavigate()
  async function load(){ const r=await api.get("/api/v1/engagements"); setList(r.data) }
  useEffect(()=>{ load() },[])
  async function create(){
    if(!form.name) return alert("Name required")
    await api.post("/api/v1/engagements", form)
    setShow(false); setForm({name:"", customer:"Acme Corp", description:"", assessment_type:"external"}); load()
  }
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between"><h1 className="text-2xl font-bold">Engagements</h1><Button onClick={()=>setShow(!show)}>{show?"Cancel":"New Engagement"}</Button></div>
      {show && (
        <Card><CardHeader><CardTitle>Step 1 — Engagement</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div><label className="text-xs text-zinc-400">Engagement Name *</label><Input value={form.name} onChange={e=>setForm({...form,name:e.target.value})} placeholder="External Assessment — Acme"/></div>
              <div><label className="text-xs text-zinc-400">Customer</label><Input value={form.customer} onChange={e=>setForm({...form,customer:e.target.value})}/></div>
            </div>
            <div><label className="text-xs text-zinc-400">Description</label><Input value={form.description} onChange={e=>setForm({...form,description:e.target.value})} placeholder="Authorized scope description"/></div>
            <div><label className="text-xs text-zinc-400">Assessment Type</label>
              <select value={form.assessment_type} onChange={e=>setForm({...form,assessment_type:e.target.value})} className="w-full h-9 rounded-md border border-zinc-800 bg-zinc-900 px-3 text-sm">
                <option value="external">External Pentest</option><option value="internal">Internal Pentest</option><option value="web">Web App</option><option value="api">API</option><option value="ad">Active Directory</option><option value="cloud">Cloud</option><option value="red_team">Red Team</option><option value="purple_team">Purple Team</option><option value="ctf">CTF / Lab</option>
              </select>
            </div>
            <Button onClick={create} className="w-full">Create Engagement</Button>
            <p className="text-xs text-zinc-500">Step 2 (Authorization & Scope) is configured inside the engagement detail.</p>
          </CardContent>
        </Card>
      )}
      <div className="grid gap-3">
        {list.map(e=>(
          <Card key={e.id} className="hover:border-orange-600/30 cursor-pointer" onClick={()=>nav(`/engagements/${e.id}`)}>
            <CardContent className="p-4 flex items-center justify-between">
              <div><div className="font-semibold">{e.name}</div><div className="text-xs text-zinc-500">{e.customer} • {e.assessment_type} • {new Date(e.created_at).toLocaleString()}</div></div>
              <div className="flex items-center gap-2"><Badge variant={e.status==="authorized"?"success":"secondary"}>{e.status}</Badge><Button size="sm" variant="outline" onClick={(ev)=>{ev.stopPropagation(); localStorage.setItem("active_engagement", e.id); nav("/mission-control")}}>Open</Button></div>
            </CardContent>
          </Card>
        ))}
        {list.length===0 && <div className="text-sm text-zinc-500 text-center py-12">No engagements yet — create your first above.</div>}
      </div>
    </div>
  )
}

export function EngagementDetail(){
  const id = location.pathname.split("/")[2]
  const [eng,setEng]=useState<any>(null)
  const [targets,setTargets]=useState<any[]>([])
  const [excls,setExcls]=useState<any[]>([])
  const [newTarget,setNewTarget]=useState({target_type:"cidr", value:""})
  const [newExcl,setNewExcl]=useState({exclusion_type:"system", value:""})
  async function load(){
    const r=await api.get(`/api/v1/engagements/${id}`); setEng(r.data)
    const t=await api.get(`/api/v1/engagements/${id}/scope/targets`); setTargets(t.data)
    const ex=await api.get(`/api/v1/engagements/${id}/scope/exclusions`); setExcls(ex.data)
  }
  useEffect(()=>{ load() },[id])
  if(!eng) return <div className="text-zinc-500">Loading...</div>
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3"><h1 className="text-2xl font-bold">{eng.name}</h1><Badge>{eng.status}</Badge></div>
      <Card><CardHeader><CardTitle>Step 2 — Authorization & Scope</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="text-sm text-zinc-400">Customer: {eng.customer} • Type: {eng.assessment_type} • Operator: {eng.operator_id.slice(0,8)}</div>
          <Button variant={eng.status==="draft"?"default":"outline"} onClick={async()=>{ await api.post(`/api/v1/engagements/${id}/authorize`,{scope_summary:"Authorized via GUI"}); load()}} disabled={eng.status!=="draft"}>{eng.status==="draft"?"Confirm Authorization — Enable Engagement":"✓ Authorized"}</Button>
          <p className="text-xs text-zinc-500">Do not start assessment until authorization is confirmed. Scope validation blocks all out-of-scope execution.</p>
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-6">
        <Card><CardHeader><CardTitle>Authorized Targets</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <select value={newTarget.target_type} onChange={e=>setNewTarget({...newTarget,target_type:e.target.value})} className="h-9 rounded-md border border-zinc-800 bg-zinc-900 px-2 text-sm"><option value="cidr">CIDR</option><option value="ip">IP</option><option value="domain">Domain</option><option value="url">URL</option></select>
              <Input placeholder="10.0.0.0/24 or example.com" value={newTarget.value} onChange={e=>setNewTarget({...newTarget,value:e.target.value})} className="flex-1"/>
              <Button size="sm" onClick={async()=>{ if(!newTarget.value) return; await api.post(`/api/v1/engagements/${id}/scope/targets`, newTarget); setNewTarget({...newTarget,value:""}); load()}}>Add</Button>
            </div>
            <div className="space-y-1">{targets.map((t:any)=><div key={t.id} className="flex justify-between text-sm p-2 rounded bg-zinc-800/50"><span>{t.target_type}: {t.value}</span><button onClick={async()=>{ await api.delete(`/api/v1/engagements/${id}/scope/targets/${t.id}`); load()}} className="text-red-400 text-xs">Remove</button></div>)}{targets.length===0 && <div className="text-xs text-zinc-500">No targets — add at least one before assessment</div>}</div>
          </CardContent>
        </Card>
        <Card><CardHeader><CardTitle>Exclusions (Deny List)</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <select value={newExcl.exclusion_type} onChange={e=>setNewExcl({...newExcl,exclusion_type:e.target.value})} className="h-9 rounded-md border border-zinc-800 bg-zinc-900 px-2 text-sm"><option value="system">System</option><option value="port">Port</option><option value="technique">Technique</option></select>
              <Input placeholder="10.0.0.5 or 22 or T1110" value={newExcl.value} onChange={e=>setNewExcl({...newExcl,value:e.target.value})} className="flex-1"/>
              <Button size="sm" onClick={async()=>{ if(!newExcl.value) return; await api.post(`/api/v1/engagements/${id}/scope/exclusions`, newExcl); setNewExcl({...newExcl,value:""}); load()}}>Add</Button>
            </div>
            <div className="space-y-1">{excls.map((e:any)=><div key={e.id} className="text-sm p-2 rounded bg-red-950/20 border border-red-900/30">{e.exclusion_type}: {e.value}</div>)}</div>
          </CardContent>
        </Card>
      </div>
      <Card><CardContent className="p-4 flex gap-2"><Button onClick={()=>{localStorage.setItem("active_engagement", id); location.href="/mission-control"}}>→ Open Mission Control</Button><Button variant="outline" onClick={load}>Refresh</Button></CardContent></Card>
    </div>
  )
}

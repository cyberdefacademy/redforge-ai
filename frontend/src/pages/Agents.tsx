import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"

type Provider = { id: string; label: string; kind: string; description: string; models: string[]; configured: boolean; default_model: string; base_url_set?: boolean }

export function Agents(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [agents,setAgents]=useState<any[]>([])
  const [ollama,setOllama]=useState<any>(null)
  const [providers,setProviders]=useState<Provider[]>([])
  const [provDefault,setProvDefault]=useState("ollama-local")
  const [extEnabled,setExtEnabled]=useState(false)
  const [provider,setProvider]=useState(()=>localStorage.getItem("rf_provider")||"ollama-local")
  const [model,setModel]=useState(()=>localStorage.getItem("rf_model")||"")
  const [allowExternal,setAllowExternal]=useState(false)
  const [prompt,setPrompt]=useState("Propose next 2 recon steps within scope")
  const [out,setOut]=useState<any>(null)
  const [loading,setLoading]=useState(false)

  async function load(){
    const r=await api.get("/api/v1/agents"); setAgents(r.data.agents||[]); setOllama(r.data)
    try{
      const p=await api.get("/api/v1/agents/providers")
      setProviders(p.data.providers||[]); setProvDefault(p.data.default||"ollama-local"); setExtEnabled(!!p.data.external_enabled)
      if(!localStorage.getItem("rf_provider") && p.data.default) setProvider(p.data.default)
    }catch{ /* providers endpoint optional for older backends */ }
  }
  useEffect(()=>{ load() },[])

  const sel = providers.find(p=>p.id===provider)
  const isCloud = sel?.kind==="cloud"
  const modelPlaceholder = sel?.default_model || "model name"
  const effectiveModel = model.trim() || sel?.default_model || ""

  async function run(id:string){
    setLoading(true); setOut(null)
    localStorage.setItem("rf_provider",provider); localStorage.setItem("rf_model",model.trim())
    try{
      const r=await api.post(`/api/v1/agents/${id}/run`,{engagement_id:engId, prompt, provider, model: effectiveModel||undefined, enable_external: isCloud ? allowExternal : undefined})
      setOut(r.data)
    }catch(e:any){ setOut({error:e.response?.data?.detail||e.message}) }
    finally{ setLoading(false)}
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AI Agents — Model Providers</h1>
      <Card><CardContent className="p-4 flex justify-between text-sm"><span>Ollama: {ollama?.ollama_url}</span><Badge variant={ollama?.ollama_health?.includes("connected")?"success":"warning"}>{ollama?.ollama_health}</Badge></CardContent></Card>
      <Card>
        <CardHeader><CardTitle>Model Provider</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <div className="flex flex-wrap gap-2 items-center text-sm">
            <label className="text-zinc-500">Provider</label>
            <select className="bg-zinc-900 border border-zinc-700 rounded px-2 py-1" value={provider} onChange={e=>{setProvider(e.target.value); setModel("")}}>
              {providers.map(p=><option key={p.id} value={p.id}>{p.label}{p.kind==="cloud"?(p.configured?" ●":" ○"):""}</option>)}
            </select>
            <label className="text-zinc-500">Model</label>
            <input className="bg-zinc-900 border border-zinc-700 rounded px-2 py-1 w-64" list="rf-models" placeholder={modelPlaceholder} value={model} onChange={e=>setModel(e.target.value)}/>
            <datalist id="rf-models">{(sel?.models||[]).map(m=><option key={m} value={m}/>)}</datalist>
            {isCloud && (
              <label className="flex items-center gap-1 text-xs text-amber-400">
                <input type="checkbox" checked={allowExternal} onChange={e=>setAllowExternal(e.target.checked)}/>
                Allow external call {extEnabled?"(server-enabled)":"(per-run opt-in)"}
              </label>
            )}
          </div>
          <div className="text-xs text-zinc-500">
            {sel?.description||""}
            {isCloud && !sel?.configured && <span className="text-amber-400"> — API key not configured on server. Prompts stay local until a key is set.</span>}
            {isCloud && sel?.configured && !extEnabled && !allowExternal && <span className="text-amber-400"> — external calls need per-run opt-in (checkbox) or server ENABLE_EXTERNAL_LLM.</span>}
          </div>
        </CardContent>
      </Card>
      <div className="grid grid-cols-2 gap-4">{agents.map((a:any)=><Card key={a.id}><CardHeader><CardTitle className="text-sm flex justify-between">{a.name}<Badge>{a.category}</Badge></CardTitle></CardHeader><CardContent className="space-y-2"><div className="text-xs text-zinc-500">Tools: {a.tools.join(", ")}</div><Button size="sm" disabled={loading} onClick={()=>run(a.id)}>{loading?"Running...":"Run"}</Button></CardContent></Card>)}</div>
      <Card><CardHeader><CardTitle>Planner Prompt</CardTitle></CardHeader><CardContent className="space-y-2"><Input value={prompt} onChange={e=>setPrompt(e.target.value)}/><div className="text-xs text-zinc-500">Structured JSON next_actions with risk/scope gating. Provider: {provider}{effectiveModel?` / ${effectiveModel}`:""}</div></CardContent></Card>
      {out && <Card><CardHeader><CardTitle>Agent Output</CardTitle></CardHeader><CardContent><pre className="text-xs whitespace-pre-wrap bg-zinc-900 p-3 rounded">{JSON.stringify(out,null,2).slice(0,4000)}</pre></CardContent></Card>}
    </div>
  )
}

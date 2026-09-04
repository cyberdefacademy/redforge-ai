import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
export function Agents(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [agents,setAgents]=useState<any[]>([])
  const [ollama,setOllama]=useState<any>(null)
  const [prompt,setPrompt]=useState("Propose next 2 recon steps within scope")
  const [out,setOut]=useState<any>(null)
  const [loading,setLoading]=useState(false)
  async function load(){ const r=await api.get("/api/v1/agents"); setAgents(r.data.agents||[]); setOllama(r.data)}
  useEffect(()=>{ load() },[])
  async function run(id:string){
    setLoading(true); setOut(null)
    try{ const r=await api.post(`/api/v1/agents/${id}/run`,{engagement_id:engId, prompt}); setOut(r.data)}catch(e:any){ setOut({error:e.response?.data?.detail||e.message})}
    finally{ setLoading(false)}
  }
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">AI Agents — Ollama Wired</h1>
      <Card><CardContent className="p-4 flex justify-between text-sm"><span>Ollama: {ollama?.ollama_url}</span><Badge variant={ollama?.ollama_health?.includes("connected")?"success":"warning"}>{ollama?.ollama_health}</Badge></CardContent></Card>
      <div className="grid grid-cols-2 gap-4">{agents.map((a:any)=><Card key={a.id}><CardHeader><CardTitle className="text-sm flex justify-between">{a.name}<Badge>{a.category}</Badge></CardTitle></CardHeader><CardContent className="space-y-2"><div className="text-xs text-zinc-500">Tools: {a.tools.join(", ")}</div><Button size="sm" disabled={loading} onClick={()=>run(a.id)}>{loading?"Running...":"Run"}</Button></CardContent></Card>)}</div>
      <Card><CardHeader><CardTitle>Planner Prompt</CardTitle></CardHeader><CardContent className="space-y-2"><Input value={prompt} onChange={e=>setPrompt(e.target.value)}/><div className="text-xs text-zinc-500">Wired to OllamaProvider (Ollama) with OpenAI fallback — structured JSON next_actions with risk/scope gating</div></CardContent></Card>
      {out && <Card><CardHeader><CardTitle>Agent Output</CardTitle></CardHeader><CardContent><pre className="text-xs whitespace-pre-wrap bg-zinc-900 p-3 rounded">{JSON.stringify(out,null,2).slice(0,4000)}</pre></CardContent></Card>}
    </div>
  )
}

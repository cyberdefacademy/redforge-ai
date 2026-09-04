import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import ReactFlow, { Background, Controls, MiniMap } from "reactflow"
import "reactflow/dist/style.css"

export function AttackGraph(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [graph,setGraph]=useState<any>({nodes:[], edges:[]})
  const [paths,setPaths]=useState<any[]>([])
  async function load(){
    if(!engId) return
    const g=await api.get(`/api/v1/engagements/${engId}/attack-graph`)
    setGraph(g.data)
    const p=await api.get(`/api/v1/engagements/${engId}/attack-paths`)
    setPaths(p.data.paths||[])
  }
  useEffect(()=>{ load() },[engId])
  if(!engId) return <div className="text-center py-16 text-zinc-500">No active engagement</div>
  const rfNodes = graph.nodes.map((n:any)=>({id:n.id, data:{label: n.data.label}, position: n.position, style:{background: n.type==="host"?"#0ea5e9":n.type==="finding"?"#ef4444":"#22c55e", color:"#fff", borderRadius:8, padding:8, fontSize:12}}))
  const rfEdges = graph.edges.map((e:any)=>({id:e.id, source:e.source, target:e.target, label:e.label, animated:true}))
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Attack Graph & Paths</h1>
      <p className="text-xs text-zinc-500">Environment graph — auto-built from hosts → ports → findings → MITRE</p>
      <Card><CardHeader><CardTitle>Environment Graph (React Flow)</CardTitle></CardHeader>
        <CardContent><div className="h-[420px] rounded-lg border border-zinc-800 bg-white"><ReactFlow nodes={rfNodes} edges={rfEdges} fitView><Background/><Controls/><MiniMap/></ReactFlow></div></CardContent>
      </Card>
      <Card><CardHeader><CardTitle>Prioritized Attack Paths</CardTitle></CardHeader>
        <CardContent className="space-y-2">{paths.map((p:any)=><div key={p.id} className="p-3 rounded bg-zinc-800/50 text-sm"><div>Steps: {p.steps.join(" → ")}</div><div className="text-xs text-zinc-500">Risk {p.risk_score} • MITRE {p.mitre.join(", ")}</div></div>)}{paths.length===0 && <div className="text-xs text-zinc-500">No paths yet — need hosts/findings</div>}</CardContent>
      </Card>
    </div>
  )
}

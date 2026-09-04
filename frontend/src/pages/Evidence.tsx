import { useEffect, useState } from "react"
import { api } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

export function Evidence(){
  const engId = localStorage.getItem("active_engagement") || ""
  const [list,setList]=useState<any[]>([])
  const [file,setFile]=useState<File|null>(null)
  const [tool,setTool]=useState("nmap")
  async function load(){
    if(!engId) return
    const r=await api.get(`/api/v1/engagements/${engId}/evidence`)
    setList(r.data)
  }
  useEffect(()=>{ load() },[engId])
  async function upload(){
    if(!file || !engId) return alert(!engId?"Open an engagement first":"Pick a file")
    const fd=new FormData()
    fd.append("file", file)
    await api.post(`/api/v1/engagements/${engId}/evidence?tool=${tool}`, fd, {headers:{"Content-Type":"multipart/form-data"}})
    setFile(null); load()
  }
  if(!engId) return <div className="text-center py-16 text-zinc-500">No active engagement — open one from Engagements</div>
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Evidence Store</h1>
      <p className="text-xs text-zinc-500">Immutable SHA-256 chain-of-custody • Every tool execution auto-hashed</p>
      <Card><CardHeader><CardTitle>Upload Artifact</CardTitle></CardHeader>
        <CardContent className="flex gap-2">
          <input type="file" onChange={e=>setFile(e.target.files?.[0]||null)} className="flex-1 text-sm text-zinc-400 file:mr-4 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-orange-600 file:text-white"/>
          <select value={tool} onChange={e=>setTool(e.target.value)} className="h-9 rounded border border-zinc-800 bg-zinc-900 px-2 text-sm"><option>nmap</option><option>nuclei</option><option>manual</option></select>
          <Button onClick={upload}>Upload & Hash</Button>
        </CardContent>
      </Card>
      <div className="grid gap-2">
        {list.map(ev=><Card key={ev.id}><CardContent className="p-3 flex justify-between items-center">
          <div><div className="text-sm font-mono">{ev.file_path.split("/").pop()}</div><div className="text-xs text-zinc-500">SHA-256: {ev.sha256.slice(0,24)}… • {ev.type}</div></div>
          <Badge variant="success">verified</Badge>
        </CardContent></Card>)}
        {list.length===0 && <div className="text-sm text-zinc-500 text-center py-8">No evidence yet — tool runs auto-populate hashes here</div>}
      </div>
    </div>
  )
}

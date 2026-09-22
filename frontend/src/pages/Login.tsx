import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { api } from "@/lib/api"
import { useAuth } from "@/store/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Zap, Shield } from "lucide-react"

export function Login() {
  const [email,setEmail]=useState("")
  const [password,setPassword]=useState("")
  const [err,setErr]=useState("")
  const [loading,setLoading]=useState(false)
  const nav=useNavigate()
  const {setAuth}=useAuth()
  async function submit(e:React.FormEvent){ e.preventDefault(); setErr(""); setLoading(true)
    try{
      const r=await api.post("/api/v1/auth/login",{email,password})
      const token=r.data.access_token
      localStorage.setItem("redforge_token",token)
      const me=await api.get("/api/v1/auth/me",{headers:{Authorization:`Bearer ${token}`}})
      setAuth(token, me.data)
      nav("/dashboard")
    }catch(e:any){ setErr(e.response?.data?.detail||"Login failed") } finally{ setLoading(false) }
  }
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0a0e1a] p-6">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center mx-auto mb-4"><Zap className="w-7 h-7 text-white"/></div>
          <h1 className="text-2xl font-black tracking-wider">REDFORGE AI</h1>
          <p className="text-xs tracking-[0.3em] text-zinc-500">AUTONOMOUS RED TEAM MISSION CONTROL</p>
          <p className="text-xs text-zinc-600 mt-2 flex items-center justify-center gap-1"><Shield className="w-3 h-3"/> Authorized Use Only</p>
        </div>
        <Card>
          <CardHeader><CardTitle>Operator Login</CardTitle><p className="text-xs text-zinc-500">Use your provisioned operator credentials</p></CardHeader>
          <CardContent>
            <form onSubmit={submit} className="space-y-4">
              <div><label className="text-xs text-zinc-400">Email</label><Input value={email} onChange={e=>setEmail(e.target.value)} placeholder="operator@redforge.local" autoComplete="username"/></div>
              <div><label className="text-xs text-zinc-400">Password</label><Input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password"/></div>
              {err && <div className="text-sm text-red-400 bg-red-950/30 border border-red-900 p-2 rounded">{err}</div>}
              <Button type="submit" disabled={loading} className="w-full">{loading?"Authenticating...":"Enter Mission Control"}</Button>
            </form>
          </CardContent>
        </Card>
        <p className="text-[11px] text-zinc-600 text-center mt-6">Scope-enforced • Evidence-hashed • Human-in-the-loop • MITRE-mapped</p>
      </div>
    </div>
  )
}

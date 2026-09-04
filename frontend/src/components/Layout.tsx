import { Link, useLocation, useNavigate } from "react-router-dom"
import { useAuth } from "@/store/auth"
import { Button } from "@/components/ui/button"
import { Shield, LayoutDashboard, Target, Crosshair, Bug, Network, FileText, Settings, Terminal, Wrench, AlertTriangle, LogOut, Zap, Cloud, Users, Beaker } from "lucide-react"

const nav = [
  {to:"/dashboard", label:"Dashboard", icon: LayoutDashboard},
  {to:"/engagements", label:"Engagements", icon: Target},
  {to:"/mission-control", label:"Mission Control", icon: Crosshair},
  {to:"/assets", label:"Assets", icon: Network},
  {to:"/vulnerabilities", label:"Findings", icon: Bug},
  {to:"/attack-paths", label:"Attack Paths", icon: Network},
  {to:"/mitre", label:"MITRE", icon: Shield},
  {to:"/tools", label:"Tool Center", icon: Wrench},
  {to:"/agents", label:"Agents", icon: Beaker},
  {to:"/advanced", label:"AD / Cloud / Purple", icon: Cloud},
  {to:"/terminal", label:"Terminal", icon: Terminal},
  {to:"/approvals", label:"Approvals", icon: AlertTriangle},
  {to:"/evidence", label:"Evidence", icon: FileText},
  {to:"/reports", label:"Reports", icon: FileText},
  {to:"/audit", label:"Audit", icon: FileText},
  {to:"/settings", label:"Settings", icon: Settings},
]

export function Layout({children}:{children:React.ReactNode}) {
  const loc = useLocation()
  const nav2 = useNavigate()
  const {user, logout} = useAuth()
  return (
    <div className="min-h-screen flex bg-[#0a0e1a]">
      <aside className="w-64 border-r border-zinc-800 bg-[#0f1423] flex flex-col">
        <div className="p-6 border-b border-zinc-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-orange-600 to-red-600 flex items-center justify-center"><Zap className="w-5 h-5 text-white"/></div>
            <div><div className="font-black tracking-wider text-sm">REDFORGE AI</div><div className="text-[10px] text-zinc-500 tracking-widest">MISSION CONTROL</div></div>
          </div>
          <div className="mt-4 flex items-center gap-2 text-xs"><span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"/><span className="text-zinc-400">OPERATIONAL</span><span className="ml-auto text-zinc-600">{user?.role||"operator"}</span></div>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto scrollbar-thin">
          {nav.map(n=>{
            const active = loc.pathname===n.to || loc.pathname.startsWith(n.to+"/")
            return <Link key={n.to} to={n.to} className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${active?"bg-orange-600/20 text-orange-400 border border-orange-600/30":"text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"}`}><n.icon className="w-4 h-4"/>{n.label}</Link>
          })}
        </nav>
        <div className="p-4 border-t border-zinc-800">
          <div className="text-xs text-zinc-500 truncate">{user?.email}</div>
          <Button variant="ghost" size="sm" className="w-full mt-2 justify-start text-zinc-400" onClick={()=>{logout(); nav2("/login")}}><LogOut className="w-4 h-4 mr-2"/>Logout</Button>
        </div>
      </aside>
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 border-b border-zinc-800 bg-[#0f1423]/80 backdrop-blur flex items-center px-6 gap-4">
          <div className="text-sm text-zinc-400">Authorized Use Only — Scope-Enforced Assessment Platform</div>
          <div className="ml-auto flex items-center gap-2">
            <Button variant="destructive" size="sm" onClick={async()=>{
              if(!confirm("EMERGENCY STOP — terminate all operations?")) return
              const engId = localStorage.getItem("active_engagement")
              if(!engId) return alert("No active engagement")
              const t = localStorage.getItem("redforge_token")
              await fetch(`/api/v1/engagements/${engId}/kill`, {method:"POST", headers:{Authorization: `Bearer ${t}`}})
              alert("Kill switch activated")
            }}>⏹ EMERGENCY STOP</Button>
          </div>
        </header>
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  )
}

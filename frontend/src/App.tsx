import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useAuth } from "@/store/auth"
import { Layout } from "@/components/Layout"
import { Login } from "@/pages/Login"
import { Dashboard } from "@/pages/Dashboard"
import { Engagements, EngagementDetail } from "@/pages/Engagements"
import { MissionControl } from "@/pages/MissionControl"
import { Tools, Mitre } from "@/pages/GenericPages"
import { Evidence } from "@/pages/Evidence"
import { Assets } from "@/pages/Assets"
import { AttackGraph } from "@/pages/AttackGraph"
import { Findings } from "@/pages/Findings"
import { Reports } from "@/pages/Reports"
import { Agents } from "@/pages/Agents"
import { Approvals } from "@/pages/Approvals"
import { Audit } from "@/pages/Audit"
import { WebPurple } from "@/pages/WebPurple"

const qc = new QueryClient()
function Protected({children}:{children:React.ReactNode}){
  const {token}=useAuth()
  if(!token) return <Navigate to="/login" replace />
  return <Layout>{children}</Layout>
}
export default function App(){
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login/>}/>
          <Route path="/dashboard" element={<Protected><Dashboard/></Protected>}/>
          <Route path="/engagements" element={<Protected><Engagements/></Protected>}/>
          <Route path="/engagements/:id" element={<Protected><EngagementDetail/></Protected>}/>
          <Route path="/mission-control" element={<Protected><MissionControl/></Protected>}/>
          <Route path="/assets" element={<Protected><Assets/></Protected>}/>
          <Route path="/vulnerabilities" element={<Protected><Findings/></Protected>}/>
          <Route path="/findings" element={<Protected><Findings/></Protected>}/>
          <Route path="/attack-paths" element={<Protected><AttackGraph/></Protected>}/>
          <Route path="/attack-graph" element={<Protected><AttackGraph/></Protected>}/>
          <Route path="/mitre" element={<Protected><Mitre/></Protected>}/>
          <Route path="/tools" element={<Protected><Tools/></Protected>}/>
          <Route path="/terminal" element={<Protected><MissionControl/></Protected>}/>
          <Route path="/approvals" element={<Protected><Approvals/></Protected>}/>
          <Route path="/evidence" element={<Protected><Evidence/></Protected>}/>
          <Route path="/reports" element={<Protected><Reports/></Protected>}/>
          <Route path="/audit" element={<Protected><Audit/></Protected>}/>
          <Route path="/agents" element={<Protected><Agents/></Protected>}/>
          <Route path="/settings" element={<Protected><Agents/></Protected>}/>
          <Route path="/advanced" element={<Protected><WebPurple/></Protected>}/>
          <Route path="/ad" element={<Protected><WebPurple/></Protected>}/>
          <Route path="/cloud" element={<Protected><WebPurple/></Protected>}/>
          <Route path="/" element={<Navigate to="/dashboard" replace/>}/>
          <Route path="*" element={<Navigate to="/dashboard" replace/>}/>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

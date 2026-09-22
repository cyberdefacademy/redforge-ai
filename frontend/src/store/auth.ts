import { create } from 'zustand'
type AuthState = { token: string | null, user: any | null, setAuth: (t:string, u:any)=>void, logout: ()=>void }
function safeParseUser(): any | null {
  try {
    const raw = localStorage.getItem("redforge_user")
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    localStorage.removeItem("redforge_user")
    localStorage.removeItem("redforge_token")
    return null
  }
}
export const useAuth = create<AuthState>((set)=>({
  token: localStorage.getItem("redforge_token"),
  user: safeParseUser(),
  setAuth: (token, user)=> { try { localStorage.setItem("redforge_token", token); localStorage.setItem("redforge_user", JSON.stringify(user)); } catch {} set({token, user}) },
  logout: ()=> { localStorage.removeItem("redforge_token"); localStorage.removeItem("redforge_user"); set({token:null, user:null}) }
}))

import { create } from 'zustand'
type AuthState = { token: string | null, user: any | null, setAuth: (t:string, u:any)=>void, logout: ()=>void }
export const useAuth = create<AuthState>((set)=>({
  token: localStorage.getItem("redforge_token"),
  user: JSON.parse(localStorage.getItem("redforge_user")||"null"),
  setAuth: (token, user)=> { localStorage.setItem("redforge_token", token); localStorage.setItem("redforge_user", JSON.stringify(user)); set({token, user}) },
  logout: ()=> { localStorage.removeItem("redforge_token"); localStorage.removeItem("redforge_user"); set({token:null, user:null}) }
}))

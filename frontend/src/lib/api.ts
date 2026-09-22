import axios from "axios"
// VITE_API_URL is baked at build time (Docker ARG). Empty string = same-origin via nginx proxy.
const baseURL = (import.meta as any).env?.VITE_API_URL || ""
export const api = axios.create({ baseURL, timeout: 30000 })
api.interceptors.request.use(cfg => {
  const t = localStorage.getItem("redforge_token")
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})
api.interceptors.response.use(r=>r, err=>{
  if (err.response?.status===401) {
    localStorage.removeItem("redforge_token")
    localStorage.removeItem("redforge_user")
    if (!location.pathname.startsWith("/login")) location.href="/login"
  }
  return Promise.reject(err)
})

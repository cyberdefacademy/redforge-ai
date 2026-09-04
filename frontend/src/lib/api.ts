import axios from "axios"
export const api = axios.create({ baseURL: "" })
api.interceptors.request.use(cfg => {
  const t = localStorage.getItem("redforge_token")
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})
api.interceptors.response.use(r=>r, err=>{
  if (err.response?.status===401) { localStorage.removeItem("redforge_token"); location.href="/login" }
  return Promise.reject(err)
})

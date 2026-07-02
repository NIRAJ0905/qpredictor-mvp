import axios from 'axios'

// In local dev (npm run dev), Vite proxies /api → localhost:8000
// In production (Vercel), requests go directly to the Render backend URL
// VITE_API_URL is set in Vercel's environment variables dashboard
const BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
})

// Attach JWT token to every request
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if (token) cfg.headers['Authorization'] = `Bearer ${token}`
  return cfg
})

// Redirect to login on 401
api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      const path = window.location.pathname
      if (path !== '/login' && path !== '/signup' && path !== '/') {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
    }
    return Promise.reject(err)
  }
)

// ── Auth ────────────────────────────────────────────────────────────────────
export const signup = (data) =>
  api.post('/api/auth/signup', data, {
    headers: { 'Content-Type': 'application/json' }
  })

export const login = (email, password) => {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  return api.post('/api/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
}

export const getMe = () => api.get('/api/auth/me')

// ── Subjects ─────────────────────────────────────────────────────────────────
export const getSubjects   = ()     => api.get('/api/subjects')
export const getSubject    = (id)   => api.get(`/api/subjects/${id}`)
export const createSubject = (data) => api.post('/api/subjects', data, {
  headers: { 'Content-Type': 'application/json' }
})
export const deleteSubject = (id)   => api.delete(`/api/subjects/${id}`)

// ── Papers ───────────────────────────────────────────────────────────────────
export const getPapers       = (sid)      => api.get(`/api/subjects/${sid}/papers`)
export const uploadPapers    = (sid, formData, onProgress) =>
  api.post(`/api/subjects/${sid}/upload-papers`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => onProgress?.(Math.round(e.loaded / e.total * 100))
  })
export const reprocessPapers = (sid)      => api.post(`/api/subjects/${sid}/process`)
export const deletePaper     = (sid, pid) => api.delete(`/api/subjects/${sid}/papers/${pid}`)

// ── Analysis ─────────────────────────────────────────────────────────────────
export const getAnalysis  = (sid)                      => api.get(`/api/subjects/${sid}/analysis`)
export const getQuestions = (sid, limit=100, offset=0) =>
  api.get(`/api/subjects/${sid}/questions`, { params: { limit, offset } })

// ── Predictions ──────────────────────────────────────────────────────────────
export const runPredictions = (sid) => api.post(`/api/subjects/${sid}/predictions`)
export const getPredictions = (sid) => api.get(`/api/subjects/${sid}/predictions`)

// ── Chat ─────────────────────────────────────────────────────────────────────
export const chat = (subject_id, message) =>
  api.post('/api/chat', { subject_id, message }, {
    headers: { 'Content-Type': 'application/json' }
  })

export default api

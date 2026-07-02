import { useState, useEffect } from 'react'
import { getSubject, getSubjects } from '../lib/api'

// Active subject persisted across page reloads
export function useActiveSubject() {
  const [subjectId, setSubjectIdRaw] = useState(
    () => parseInt(localStorage.getItem('activeSubjectId') || '0') || null
  )
  const [subject, setSubject] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)

  function setSubjectId(id) {
    setSubjectIdRaw(id)
    if (id) localStorage.setItem('activeSubjectId', id)
    else     localStorage.removeItem('activeSubjectId')
  }

  useEffect(() => {
    if (!subjectId) { setSubject(null); return }
    setLoading(true)
    getSubject(subjectId)
      .then(r => { setSubject(r.data); setError(null) })
      .catch(e => {
        setError(e.response?.data?.detail || 'Failed to load subject')
        setSubject(null)
        setSubjectId(null)
      })
      .finally(() => setLoading(false))
  }, [subjectId])

  return { subjectId, setSubjectId, subject, loading, error }
}

// All subjects list
export function useSubjects() {
  const [subjects, setSubjects] = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState(null)

  async function reload() {
    setLoading(true)
    try {
      const r = await getSubjects()
      setSubjects(r.data)
      setError(null)
    } catch(e) {
      setError(e.response?.data?.detail || 'Failed to load subjects')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, [])
  return { subjects, loading, error, reload }
}

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, BookOpen, FileText, TrendingUp, CheckCircle, AlertCircle, X } from 'lucide-react'
import { createSubject, deleteSubject } from '../lib/api'
import { useSubjects, useActiveSubject } from '../hooks/useSubject'
import { AppShell, PageHeader } from '../components/layout'
import { Card, CardContent, CardHeader, CardTitle, Button, Badge, Input, Alert, StatCard, Spinner, Empty } from '../components/ui'
import { fmtDate } from '../lib/utils'
import useAuthStore from '../store/authStore'

function CreateSubjectModal({ onClose, onCreated }) {
  const [form, setForm]   = useState({ name:'', code:'', department:'', university:'', semester:'' })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function set(k, v) { setForm(f => ({ ...f, [k]: v })) }

  async function submit(e) {
    e.preventDefault()
    if (!form.name.trim()) { setError('Subject name is required.'); return }
    setLoading(true); setError('')
    try {
      const r = await createSubject({
        name:       form.name.trim(),
        code:       form.code.trim()       || null,
        department: form.department.trim() || null,
        university: form.university.trim() || null,
        semester:   form.semester.trim()   || null,
      })
      onCreated(r.data)
    } catch(err) {
      setError(err.response?.data?.detail || 'Failed to create subject.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="font-semibold text-gray-900">New Subject</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><X size={20}/></button>
        </div>
        <form onSubmit={submit} className="px-6 py-5 space-y-3">
          {error && <Alert variant="error">{error}</Alert>}
          <Input label="Subject name *" value={form.name} onChange={e=>set('name',e.target.value)} placeholder="Applied Physics" />
          <div className="grid grid-cols-2 gap-3">
            <Input label="Code" value={form.code} onChange={e=>set('code',e.target.value)} placeholder="PHY101" />
            <Input label="Semester" value={form.semester} onChange={e=>set('semester',e.target.value)} placeholder="Sem 2" />
          </div>
          <Input label="Department" value={form.department} onChange={e=>set('department',e.target.value)} placeholder="Engineering" />
          <Input label="University" value={form.university} onChange={e=>set('university',e.target.value)} placeholder="Mumbai University" />
          <div className="flex gap-3 pt-2">
            <Button type="button" variant="secondary" className="flex-1" onClick={onClose}>Cancel</Button>
            <Button type="submit" className="flex-1" disabled={loading}>{loading ? 'Creating…' : 'Create Subject'}</Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { user }                          = useAuthStore()
  const { subjects, loading, reload }     = useSubjects()
  const { setSubjectId }                  = useActiveSubject()
  const [showCreate, setShowCreate]       = useState(false)
  const navigate                          = useNavigate()

  function handleCreated(subject) {
    setShowCreate(false)
    reload()
    setSubjectId(subject.id)
    navigate('/upload')
  }

  async function handleDelete(e, id) {
    e.stopPropagation()
    if (!confirm('Delete this subject and all its papers?')) return
    await deleteSubject(id)
    reload()
  }

  function selectSubject(id) {
    setSubjectId(id)
    navigate('/analysis')
  }

  const totalPapers    = subjects.reduce((a, s) => a + s.paper_count, 0)
  const totalQuestions = subjects.reduce((a, s) => a + s.question_count, 0)
  const readySubjects  = subjects.filter(s => s.is_ready).length

  return (
    <AppShell>
      <PageHeader
        title={`Welcome back, ${user?.name?.split(' ')[0] || 'Student'} 👋`}
        description="Manage your subjects and get AI-powered exam predictions"
        action={
          <Button onClick={() => setShowCreate(true)}>
            <Plus size={16} /> New Subject
          </Button>
        }
      />

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Subjects"  value={subjects.length}  icon={BookOpen}   color="text-brand-500" />
        <StatCard label="Papers"    value={totalPapers}      icon={FileText}   color="text-purple-500" />
        <StatCard label="Questions" value={totalQuestions}   icon={FileText}   color="text-blue-500" />
        <StatCard label="Ready"     value={readySubjects}    sub="≥10 papers"  icon={CheckCircle} color="text-green-500" />
      </div>

      {/* Subject cards */}
      <Card>
        <CardHeader>
          <CardTitle>Your Subjects</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex justify-center py-12"><Spinner /></div>
          ) : subjects.length === 0 ? (
            <Empty
              icon={BookOpen}
              title="No subjects yet"
              description="Create a subject to start uploading question papers"
              action={<Button onClick={() => setShowCreate(true)}><Plus size={16}/>Create your first subject</Button>}
            />
          ) : (
            <div className="divide-y divide-gray-100">
              {subjects.map(s => (
                <div
                  key={s.id}
                  onClick={() => selectSubject(s.id)}
                  className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 cursor-pointer group transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center">
                      <BookOpen size={18} className="text-brand-500" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{s.name}</p>
                      <p className="text-sm text-gray-400">
                        {[s.code, s.semester, s.university].filter(Boolean).join(' · ')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right text-sm text-gray-500">
                      <p>{s.paper_count} papers</p>
                      <p>{s.question_count} questions</p>
                    </div>
                    {s.is_ready
                      ? <Badge variant="green">Ready</Badge>
                      : <Badge variant="yellow">Need {10 - s.paper_count} more</Badge>
                    }
                    <button
                      onClick={e => handleDelete(e, s.id)}
                      className="opacity-0 group-hover:opacity-100 text-gray-300 hover:text-red-500 transition-all p-1"
                    >
                      <X size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {showCreate && <CreateSubjectModal onClose={() => setShowCreate(false)} onCreated={handleCreated} />}
    </AppShell>
  )
}

import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Upload, FileText, X, CheckCircle, AlertCircle, RefreshCw } from 'lucide-react'
import { uploadPapers, reprocessPapers } from '../lib/api'
import { useActiveSubject, useSubjects } from '../hooks/useSubject'
import { AppShell, PageHeader, SubjectBreadcrumb } from '../components/layout'
import { Card, CardContent, Button, Alert, Badge, ProgressBar, Spinner, Empty } from '../components/ui'
import { fmtDate, statusColor } from '../lib/utils'

function SubjectPicker({ subjects, activeId, onPick }) {
  return (
    <Card className="mb-6">
      <CardContent>
        <p className="text-sm font-medium text-gray-700 mb-3">Select a subject to upload papers to:</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {subjects.map(s => (
            <button
              key={s.id}
              onClick={() => onPick(s.id)}
              className={`text-left px-4 py-3 rounded-xl border-2 transition-all ${
                activeId === s.id
                  ? 'border-brand-500 bg-brand-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <p className="font-medium text-sm text-gray-900">{s.name}</p>
              <p className="text-xs text-gray-400">{s.paper_count} papers uploaded</p>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default function UploadPage() {
  const { subjectId, setSubjectId, subject }   = useActiveSubject()
  const { subjects }                           = useSubjects()
  const [files, setFiles]                      = useState([])
  const [year, setYear]                        = useState('')
  const [semester, setSemester]                = useState('')
  const [dragging, setDragging]                = useState(false)
  const [uploading, setUploading]              = useState(false)
  const [progress, setProgress]                = useState(0)
  const [result, setResult]                    = useState(null)
  const [error, setError]                      = useState('')
  const [reprocessing, setReprocessing]        = useState(false)
  const inputRef                               = useRef()
  const navigate                               = useNavigate()

  function addFiles(fl) {
    const pdfs = Array.from(fl).filter(f => f.name.toLowerCase().endsWith('.pdf'))
    const news  = pdfs.filter(f => !files.some(x => x.name === f.name && x.size === f.size))
    setFiles(prev => [...prev, ...news])
    if (pdfs.length < fl.length)
      setError(`${fl.length - pdfs.length} non-PDF file(s) skipped.`)
  }

  function removeFile(i) { setFiles(f => f.filter((_, j) => j !== i)) }

  function onDrop(e) {
    e.preventDefault(); setDragging(false)
    addFiles(e.dataTransfer.files)
  }

  async function handleUpload() {
    if (!subjectId || !files.length) return
    setUploading(true); setError(''); setResult(null); setProgress(0)
    try {
      const fd = new FormData()
      files.forEach(f => fd.append('files', f))
      if (year)     fd.append('year', year)
      if (semester) fd.append('semester', semester)
      const r = await uploadPapers(subjectId, fd, setProgress)
      setResult(r.data)
      setFiles([])
    } catch(err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.')
    } finally {
      setUploading(false); setProgress(0)
    }
  }

  async function handleReprocess() {
    if (!subjectId) return
    setReprocessing(true)
    try { await reprocessPapers(subjectId); setResult(null) }
    catch(e) { setError('Reprocess failed.') }
    finally { setReprocessing(false) }
  }

  const fmtSize = b => b < 1048576 ? `${(b/1024).toFixed(0)} KB` : `${(b/1048576).toFixed(1)} MB`

  return (
    <AppShell>
      <PageHeader
        title="Upload Papers"
        description="Upload previous year question papers for AI analysis"
      />

      {!subjectId && subjects.length > 0 && (
        <SubjectPicker subjects={subjects} activeId={subjectId} onPick={setSubjectId} />
      )}

      {!subjectId && subjects.length === 0 && (
        <Alert variant="warning" className="mb-6">
          No subjects found. <button onClick={() => navigate('/dashboard')} className="font-medium underline">Create a subject first →</button>
        </Alert>
      )}

      {subjectId && (
        <>
          <SubjectBreadcrumb subject={subject} />

          {result && (
            <Alert variant={result.ready_for_analysis ? 'success' : 'info'} className="mb-6">
              <p className="font-medium">{result.message}</p>
              {result.ready_for_analysis && (
                <button onClick={() => navigate('/predictions')} className="mt-2 text-sm font-medium underline">
                  Run predictions now →
                </button>
              )}
            </Alert>
          )}

          {error && <Alert variant="error" className="mb-4">{error}</Alert>}

          {/* Drop zone */}
          <Card className="mb-6">
            <CardContent>
              <div
                onDragOver={e => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={onDrop}
                onClick={() => inputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                  dragging ? 'border-brand-500 bg-brand-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                }`}
              >
                <Upload size={32} className="mx-auto text-gray-400 mb-3" />
                <p className="font-medium text-gray-700">Drop PDFs here or click to browse</p>
                <p className="text-sm text-gray-400 mt-1">PDF files only · max 30 MB each</p>
                <input ref={inputRef} type="file" multiple accept=".pdf" className="hidden" onChange={e => addFiles(e.target.files)} />
              </div>

              {files.length > 0 && (
                <div className="mt-4 space-y-2">
                  {files.map((f, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                      <FileText size={16} className="text-gray-400 flex-shrink-0" />
                      <span className="text-sm text-gray-700 flex-1 truncate">{f.name}</span>
                      <span className="text-xs text-gray-400">{fmtSize(f.size)}</span>
                      <button onClick={() => removeFile(i)} className="text-gray-300 hover:text-red-400">
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 mt-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 block mb-1">Year (optional)</label>
                  <input type="number" value={year} onChange={e=>setYear(e.target.value)} placeholder="e.g. 2023"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-700 block mb-1">Semester (optional)</label>
                  <input type="text" value={semester} onChange={e=>setSemester(e.target.value)} placeholder="e.g. Sem 2"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500" />
                </div>
              </div>

              {uploading && (
                <div className="mt-4">
                  <div className="flex justify-between text-sm text-gray-500 mb-1">
                    <span>Uploading and processing…</span>
                    <span>{progress}%</span>
                  </div>
                  <ProgressBar value={progress} />
                </div>
              )}

              <div className="flex gap-3 mt-4">
                <Button
                  className="flex-1"
                  onClick={handleUpload}
                  disabled={!files.length || uploading}
                >
                  {uploading ? <><Spinner className="w-4 h-4" /> Processing…</> : `Upload ${files.length || ''} Paper${files.length !== 1 ? 's' : ''}`}
                </Button>
                <Button variant="secondary" onClick={handleReprocess} disabled={reprocessing} title="Re-extract questions from failed papers">
                  {reprocessing ? <Spinner className="w-4 h-4" /> : <RefreshCw size={16} />}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Status summary */}
          {subject && (
            <div className="text-sm text-gray-500 text-center">
              {subject.paper_count} paper{subject.paper_count !== 1 ? 's' : ''} uploaded for this subject
              {subject.paper_count < 10 && <span className="text-yellow-600 ml-2">— upload {10 - subject.paper_count} more for full predictions</span>}
              {subject.paper_count >= 10 && <span className="text-green-600 ml-2">✓ Ready for predictions</span>}
            </div>
          )}
        </>
      )}
    </AppShell>
  )
}

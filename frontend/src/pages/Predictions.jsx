import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { TrendingUp, Zap, RefreshCw, Calendar, BookOpen, Star } from 'lucide-react'
import { runPredictions, getPredictions } from '../lib/api'
import { useActiveSubject, useSubjects } from '../hooks/useSubject'
import { AppShell, PageHeader, SubjectBreadcrumb } from '../components/layout'
import { Card, CardContent, CardHeader, CardTitle, Button, Alert, Badge, Spinner, Empty, ProgressBar } from '../components/ui'
import { confidenceColor, confidenceBadge } from '../lib/utils'

function PredictionCard({ pred, index }) {
  const confClass = confidenceColor(pred.confidence_score)
  const confLabel = confidenceBadge(pred.confidence_score)

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="py-4">
        <div className="flex items-start gap-4">
          {/* Rank */}
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-bold text-sm ${
            index === 0 ? 'bg-yellow-100 text-yellow-700' :
            index === 1 ? 'bg-gray-100 text-gray-600' :
            index === 2 ? 'bg-orange-100 text-orange-600' :
            'bg-brand-50 text-brand-600'
          }`}>
            {index < 3 ? ['🥇','🥈','🥉'][index] : pred.rank}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-3 mb-2">
              <p className="text-sm font-medium text-gray-800 leading-snug">{pred.question_text}</p>
              <span className={`flex-shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full ${confClass}`}>
                {confLabel}
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-400 mb-3 flex-wrap">
              {pred.topic && (
                <span className="flex items-center gap-1"><BookOpen size={11} />{pred.topic}</span>
              )}
              {pred.unit && pred.unit !== 'Unknown' && (
                <span className="flex items-center gap-1"><Star size={11} />{pred.unit}</span>
              )}
              {pred.source_years && (
                <span className="flex items-center gap-1"><Calendar size={11} />Years: {pred.source_years}</span>
              )}
              <span className="flex items-center gap-1">
                Appeared in {pred.frequency} paper{pred.frequency !== 1 ? 's' : ''}
              </span>
            </div>

            {/* Confidence bar */}
            <div className="flex items-center gap-3">
              <ProgressBar value={pred.confidence_score} className="flex-1" />
              <span className="text-sm font-bold text-brand-600 flex-shrink-0 w-12 text-right">
                {pred.confidence_score.toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function SubjectPicker({ subjects, onPick }) {
  return (
    <Card className="mb-6">
      <CardContent>
        <p className="text-sm font-medium text-gray-700 mb-3">Select subject:</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {subjects.map(s => (
            <button key={s.id} onClick={() => onPick(s.id)}
              className="text-left px-4 py-3 rounded-xl border-2 border-gray-200 hover:border-brand-500 transition-all">
              <p className="font-medium text-sm">{s.name}</p>
              <p className="text-xs text-gray-400">{s.paper_count} papers</p>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default function PredictionsPage() {
  const { subjectId, setSubjectId, subject } = useActiveSubject()
  const { subjects }                         = useSubjects()
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError]     = useState('')
  const navigate              = useNavigate()

  useEffect(() => {
    if (!subjectId) return
    setLoading(true)
    getPredictions(subjectId)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load predictions'))
      .finally(() => setLoading(false))
  }, [subjectId])

  async function handleRun() {
    setRunning(true); setError('')
    try {
      const r = await runPredictions(subjectId)
      setData(r.data)
    } catch(e) {
      setError(e.response?.data?.detail || 'Failed to run predictions')
    } finally {
      setRunning(false)
    }
  }

  const preds = data?.predictions || []

  return (
    <AppShell>
      <PageHeader
        title="Predictions"
        description="AI-ranked questions most likely to appear in your exam"
        action={
          subjectId && (
            <Button onClick={handleRun} disabled={running}>
              {running ? <><Spinner className="w-4 h-4" /> Running…</> : <><Zap size={14} /> Generate Predictions</>}
            </Button>
          )
        }
      />

      {!subjectId && subjects.length > 0 && (
        <SubjectPicker subjects={subjects} onPick={setSubjectId} />
      )}
      {!subjectId && subjects.length === 0 && (
        <Alert variant="warning">
          No subjects. <button onClick={()=>navigate('/dashboard')} className="underline font-medium">Create one →</button>
        </Alert>
      )}

      {subjectId && (
        <>
          <SubjectBreadcrumb subject={subject} />
          {error && <Alert variant="error" className="mb-4">{error}</Alert>}

          {data?.message && (
            <Alert variant={preds.length > 0 ? 'success' : 'warning'} className="mb-6">
              {data.message}
            </Alert>
          )}

          {loading && <div className="flex justify-center py-20"><Spinner /></div>}

          {!loading && preds.length === 0 && (
            <Empty
              icon={TrendingUp}
              title="No predictions yet"
              description="Click 'Generate Predictions' to run the AI engine on your uploaded papers"
              action={
                <Button onClick={handleRun} disabled={running}>
                  <Zap size={16} /> Generate Now
                </Button>
              }
            />
          )}

          {preds.length > 0 && !loading && (
            <>
              {/* Summary stats */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <Card><CardContent className="text-center py-3">
                  <p className="text-2xl font-bold text-gray-900">{preds.length}</p>
                  <p className="text-xs text-gray-500">Predicted Questions</p>
                </CardContent></Card>
                <Card><CardContent className="text-center py-3">
                  <p className="text-2xl font-bold text-green-600">{preds.filter(p=>p.confidence_score>=75).length}</p>
                  <p className="text-xs text-gray-500">High Confidence</p>
                </CardContent></Card>
                <Card><CardContent className="text-center py-3">
                  <p className="text-2xl font-bold text-brand-600">{preds[0]?.confidence_score.toFixed(0)}%</p>
                  <p className="text-xs text-gray-500">Top Confidence</p>
                </CardContent></Card>
              </div>

              {/* Scoring legend */}
              <Card className="mb-6">
                <CardContent className="py-3">
                  <p className="text-xs text-gray-500 font-medium mb-2">Confidence Score Formula:</p>
                  <div className="flex flex-wrap gap-3 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-brand-500 inline-block"></span>40% Frequency</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-purple-500 inline-block"></span>20% Recency</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-blue-500 inline-block"></span>20% Marks Weight</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500 inline-block"></span>10% Topic Spread</span>
                    <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-500 inline-block"></span>10% Year Variety</span>
                  </div>
                </CardContent>
              </Card>

              {/* Prediction cards */}
              <div className="space-y-3">
                {preds.map((p, i) => (
                  <PredictionCard key={p.id} pred={p} index={i} />
                ))}
              </div>
            </>
          )}
        </>
      )}
    </AppShell>
  )
}

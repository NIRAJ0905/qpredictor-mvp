import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import { BarChart2, BookOpen, Hash, TrendingUp, RefreshCw } from 'lucide-react'
import { getAnalysis } from '../lib/api'
import { useActiveSubject, useSubjects } from '../hooks/useSubject'
import { AppShell, PageHeader, SubjectBreadcrumb } from '../components/layout'
import { Card, CardHeader, CardTitle, CardContent, Button, Alert, StatCard, Spinner, Empty, Badge } from '../components/ui'
import { fmtPct } from '../lib/utils'

const PIE_COLORS = ['#4f6ef7','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ef4444','#ec4899','#6366f1']

function SubjectPicker({ subjects, onPick }) {
  return (
    <Card className="mb-6">
      <CardContent>
        <p className="text-sm font-medium text-gray-700 mb-3">Select a subject to analyse:</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {subjects.map(s => (
            <button key={s.id} onClick={() => onPick(s.id)}
              className="text-left px-4 py-3 rounded-xl border-2 border-gray-200 hover:border-brand-500 hover:bg-brand-50 transition-all">
              <p className="font-medium text-sm">{s.name}</p>
              <p className="text-xs text-gray-400">{s.paper_count} papers · {s.question_count} questions</p>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default function AnalysisPage() {
  const { subjectId, setSubjectId, subject } = useActiveSubject()
  const { subjects }                         = useSubjects()
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')
  const navigate            = useNavigate()

  useEffect(() => {
    if (!subjectId) return
    setLoading(true); setError('')
    getAnalysis(subjectId)
      .then(r => setData(r.data))
      .catch(e => setError(e.response?.data?.detail || 'Failed to load analysis'))
      .finally(() => setLoading(false))
  }, [subjectId])

  return (
    <AppShell>
      <PageHeader
        title="Analysis"
        description="Topic frequency, unit breakdown, and repeated questions"
        action={
          subjectId && (
            <Button onClick={() => navigate('/predictions')} size="sm">
              <TrendingUp size={14} /> Run Predictions
            </Button>
          )
        }
      />

      {!subjectId && subjects.length > 0 && (
        <SubjectPicker subjects={subjects} onPick={setSubjectId} />
      )}
      {!subjectId && subjects.length === 0 && (
        <Alert variant="warning">No subjects found. <button onClick={()=>navigate('/dashboard')} className="underline font-medium">Create one first →</button></Alert>
      )}

      {subjectId && (
        <>
          <SubjectBreadcrumb subject={subject} />

          {loading && <div className="flex justify-center py-20"><Spinner /></div>}
          {error   && <Alert variant="error">{error}</Alert>}

          {data && !loading && (
            <>
              {/* Stats row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <StatCard label="Papers Analysed"  value={data.papers_analysed}  icon={BookOpen} />
                <StatCard label="Questions Found"  value={data.total_questions}  icon={Hash} />
                <StatCard label="Unique Topics"    value={data.unique_topics}    icon={BarChart2} />
                <StatCard label="Top Topic"        value={data.most_repeated_topic || '—'} icon={TrendingUp} />
              </div>

              {!data.analysis_ready && (
                <Alert variant="warning" className="mb-6">
                  Only {data.papers_analysed} paper(s) processed. Upload {10 - data.papers_analysed} more for full prediction accuracy.
                </Alert>
              )}

              {data.total_questions === 0 ? (
                <Alert variant="warning">
                  No questions were extracted from your papers. This usually means your PDFs are scanned images.
                  Try <button onClick={() => navigate('/upload')} className="underline font-medium">re-processing</button> them.
                </Alert>
              ) : (
                <div className="space-y-6">
                  {/* Topic frequency bar chart */}
                  {data.topic_frequency?.length > 0 && (
                    <Card>
                      <CardHeader><CardTitle>Topic Frequency</CardTitle></CardHeader>
                      <CardContent>
                        <ResponsiveContainer width="100%" height={280}>
                          <BarChart data={data.topic_frequency.slice(0, 12)} margin={{ top: 5, right: 20, bottom: 60, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                            <XAxis dataKey="topic" tick={{ fontSize: 11 }} angle={-35} textAnchor="end" interval={0} />
                            <YAxis tick={{ fontSize: 11 }} />
                            <Tooltip formatter={(v, n) => [v, 'Appearances']} />
                            <Bar dataKey="count" fill="#4f6ef7" radius={[4,4,0,0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </CardContent>
                    </Card>
                  )}

                  <div className="grid md:grid-cols-2 gap-6">
                    {/* Unit pie chart */}
                    {data.unit_analysis?.length > 0 && (
                      <Card>
                        <CardHeader><CardTitle>Unit Weightage</CardTitle></CardHeader>
                        <CardContent>
                          <ResponsiveContainer width="100%" height={240}>
                            <PieChart>
                              <Pie data={data.unit_analysis} dataKey="question_count" nameKey="unit"
                                cx="50%" cy="50%" outerRadius={80} label={({ unit, percentage }) => `${unit} ${percentage}%`}
                                labelLine={false}>
                                {data.unit_analysis.map((_, i) => (
                                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                                ))}
                              </Pie>
                              <Tooltip formatter={(v, n, p) => [v + ' questions', p.payload.unit]} />
                            </PieChart>
                          </ResponsiveContainer>
                        </CardContent>
                      </Card>
                    )}

                    {/* Most repeated questions */}
                    {data.question_frequency?.length > 0 && (
                      <Card>
                        <CardHeader><CardTitle>Most Repeated Questions</CardTitle></CardHeader>
                        <CardContent className="p-0">
                          <div className="divide-y divide-gray-100 max-h-64 overflow-y-auto">
                            {data.question_frequency.slice(0, 8).map((q, i) => (
                              <div key={i} className="px-4 py-3">
                                <div className="flex items-start justify-between gap-2 mb-1">
                                  <p className="text-sm text-gray-700 flex-1 line-clamp-2">{q.question_text}</p>
                                  <Badge variant={q.frequency >= 3 ? 'green' : 'blue'} className="flex-shrink-0">
                                    {q.frequency}×
                                  </Badge>
                                </div>
                                <p className="text-xs text-gray-400">Years: {q.years.join(', ')} · {q.percentage}%</p>
                              </div>
                            ))}
                          </div>
                        </CardContent>
                      </Card>
                    )}
                  </div>

                  {/* Unit breakdown table */}
                  {data.unit_analysis?.length > 0 && (
                    <Card>
                      <CardHeader><CardTitle>Unit-wise Breakdown</CardTitle></CardHeader>
                      <CardContent className="p-0">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
                            <tr>
                              <th className="px-4 py-3 text-left">Unit</th>
                              <th className="px-4 py-3 text-right">Questions</th>
                              <th className="px-4 py-3 text-right">Avg Marks</th>
                              <th className="px-4 py-3 text-right">Weight</th>
                              <th className="px-4 py-3 text-left">Top Topics</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {data.unit_analysis.map((u, i) => (
                              <tr key={i} className="hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-800">{u.unit}</td>
                                <td className="px-4 py-3 text-right text-gray-600">{u.question_count}</td>
                                <td className="px-4 py-3 text-right text-gray-600">{u.avg_marks || '—'}</td>
                                <td className="px-4 py-3 text-right">
                                  <span className="font-medium text-brand-600">{u.percentage}%</span>
                                </td>
                                <td className="px-4 py-3 text-gray-500 text-xs">{u.top_topics.slice(0,3).join(', ')}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </CardContent>
                    </Card>
                  )}
                </div>
              )}
            </>
          )}
        </>
      )}
    </AppShell>
  )
}

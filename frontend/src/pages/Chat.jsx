import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Send, MessageSquare, Bot, User } from 'lucide-react'
import { chat } from '../lib/api'
import { useActiveSubject, useSubjects } from '../hooks/useSubject'
import { AppShell, PageHeader, SubjectBreadcrumb } from '../components/layout'
import { Card, CardContent, Button, Alert, Spinner } from '../components/ui'

const QUICK_PROMPTS = [
  'What should I study first?',
  'What are the most repeated topics?',
  'Give me a revision plan',
  'What are the top predicted questions?',
  'What questions are likely in Unit 1?',
  'What type of questions appear most?',
]

function Message({ msg }) {
  const isBot = msg.role === 'bot'
  return (
    <div className={`flex gap-3 ${isBot ? '' : 'flex-row-reverse'}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isBot ? 'bg-brand-100 text-brand-600' : 'bg-gray-200 text-gray-600'
      }`}>
        {isBot ? <Bot size={16} /> : <User size={16} />}
      </div>
      <div className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
        isBot
          ? 'bg-white border border-gray-200 text-gray-700 rounded-tl-sm'
          : 'bg-brand-500 text-white rounded-tr-sm'
      }`}>
        {msg.text}
      </div>
    </div>
  )
}

function SubjectPicker({ subjects, onPick }) {
  return (
    <Card className="mb-6">
      <CardContent>
        <p className="text-sm font-medium text-gray-700 mb-3">Select subject to chat about:</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {subjects.map(s => (
            <button key={s.id} onClick={() => onPick(s.id)}
              className="text-left px-4 py-3 rounded-xl border-2 border-gray-200 hover:border-brand-500 transition-all">
              <p className="font-medium text-sm">{s.name}</p>
              <p className="text-xs text-gray-400">{s.paper_count} papers · {s.question_count} questions</p>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default function ChatPage() {
  const { subjectId, setSubjectId, subject } = useActiveSubject()
  const { subjects }                         = useSubjects()
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hi! I\'m your AI study assistant. Select a subject and ask me anything about your uploaded papers — I\'ll help you prepare smarter.' }
  ])
  const [input, setInput]   = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef             = useRef()
  const navigate              = useNavigate()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function sendMessage(text) {
    const msg = (text || input).trim()
    if (!msg || !subjectId) return
    setInput('')
    setMessages(m => [...m, { role: 'user', text: msg }])
    setLoading(true)
    try {
      const r = await chat(subjectId, msg)
      setMessages(m => [...m, { role: 'bot', text: r.data.reply }])
    } catch(e) {
      setMessages(m => [...m, { role: 'bot', text: '⚠️ ' + (e.response?.data?.detail || 'Something went wrong. Please try again.') }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <AppShell>
      <PageHeader
        title="AI Study Chat"
        description="Ask anything about your uploaded papers"
      />

      {!subjectId && subjects.length > 0 && (
        <SubjectPicker subjects={subjects} onPick={id => {
          setSubjectId(id)
          setMessages([{ role:'bot', text:'Great! I have access to your papers for this subject. What would you like to know?' }])
        }} />
      )}
      {!subjectId && subjects.length === 0 && (
        <Alert variant="warning">
          No subjects. <button onClick={()=>navigate('/dashboard')} className="underline font-medium">Create one first →</button>
        </Alert>
      )}

      {subjectId && (
        <>
          <SubjectBreadcrumb subject={subject} />

          {/* Quick prompts */}
          <div className="flex flex-wrap gap-2 mb-4">
            {QUICK_PROMPTS.map(p => (
              <button
                key={p}
                onClick={() => sendMessage(p)}
                disabled={loading}
                className="text-xs px-3 py-1.5 bg-white border border-gray-200 rounded-full text-gray-600 hover:border-brand-400 hover:text-brand-600 transition-colors disabled:opacity-50"
              >
                {p}
              </button>
            ))}
          </div>

          {/* Chat window */}
          <Card>
            <CardContent className="p-0">
              <div className="h-[420px] overflow-y-auto p-5 space-y-4 bg-gray-50 rounded-t-xl">
                {messages.map((m, i) => <Message key={i} msg={m} />)}
                {loading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-600 flex items-center justify-center">
                      <Bot size={16} />
                    </div>
                    <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl rounded-tl-sm">
                      <div className="flex gap-1 items-center h-4">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={bottomRef} />
              </div>

              {/* Input */}
              <div className="flex gap-3 p-4 border-t border-gray-100">
                <textarea
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKey}
                  rows={1}
                  placeholder="Ask about topics, predictions, revision plan… (Enter to send)"
                  className="flex-1 resize-none px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
                <Button onClick={() => sendMessage()} disabled={!input.trim() || loading} className="flex-shrink-0">
                  <Send size={16} />
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </AppShell>
  )
}

import { useNavigate } from 'react-router-dom'
import { Zap, BarChart2, TrendingUp, MessageSquare, Upload, CheckCircle } from 'lucide-react'
import { Button } from '../components/ui'
import useAuthStore from '../store/authStore'

const FEATURES = [
  { icon: Upload,        title: 'Upload Papers',      desc: 'Upload 10+ previous year PDFs in any format' },
  { icon: BarChart2,     title: 'Deep Analysis',      desc: 'Topic frequency, unit weightage, repeated questions' },
  { icon: TrendingUp,    title: 'AI Predictions',     desc: 'Ranked questions with confidence scores up to 99%' },
  { icon: MessageSquare, title: 'AI Chat',             desc: 'Ask anything about your papers — get instant answers' },
]

const STEPS = [
  'Create an account and login',
  'Create a subject (e.g. Applied Physics)',
  'Upload 10+ previous year PDFs',
  'Get predictions instantly',
]

export default function Landing() {
  const navigate  = useNavigate()
  const { token } = useAuthStore()

  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-white to-purple-50">
      {/* Navbar */}
      <nav className="flex items-center justify-between px-6 py-4 max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
            <Zap size={16} className="text-white" />
          </div>
          <span className="font-bold text-gray-900">Q-Predictor</span>
        </div>
        <div className="flex items-center gap-3">
          {token ? (
            <Button onClick={() => navigate('/dashboard')}>Go to Dashboard</Button>
          ) : (
            <>
              <Button variant="secondary" onClick={() => navigate('/login')}>Login</Button>
              <Button onClick={() => navigate('/signup')}>Get Started Free</Button>
            </>
          )}
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-brand-100 text-brand-700 px-4 py-1.5 rounded-full text-sm font-medium mb-6">
          <Zap size={14} />
          AI-Powered Exam Preparation
        </div>
        <h1 className="text-5xl font-bold text-gray-900 mb-4 leading-tight">
          Predict Your Exam Questions<br />
          <span className="text-brand-500">Before the Exam</span>
        </h1>
        <p className="text-lg text-gray-500 mb-8 max-w-2xl mx-auto">
          Upload previous year question papers and let AI analyze patterns,
          find repeated topics, and predict questions likely to appear — with confidence scores.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Button size="lg" onClick={() => navigate(token ? '/dashboard' : '/signup')}>
            Start Predicting Free
          </Button>
          <Button size="lg" variant="secondary" onClick={() => navigate('/login')}>
            I have an account
          </Button>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {FEATURES.map(f => (
            <div key={f.title} className="bg-white rounded-xl border border-gray-200 p-5 text-center shadow-sm">
              <div className="w-10 h-10 bg-brand-50 rounded-xl flex items-center justify-center mx-auto mb-3">
                <f.icon size={20} className="text-brand-500" />
              </div>
              <p className="font-semibold text-gray-800 text-sm mb-1">{f.title}</p>
              <p className="text-xs text-gray-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-3xl mx-auto px-6 pb-20 text-center">
        <h2 className="text-2xl font-bold text-gray-900 mb-8">How it works</h2>
        <div className="flex flex-col gap-3 text-left">
          {STEPS.map((step, i) => (
            <div key={i} className="flex items-center gap-4 bg-white rounded-xl border border-gray-100 px-5 py-4 shadow-sm">
              <div className="w-8 h-8 rounded-full bg-brand-500 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
                {i + 1}
              </div>
              <span className="text-gray-700 font-medium">{step}</span>
              <CheckCircle size={18} className="text-green-400 ml-auto" />
            </div>
          ))}
        </div>
        <Button size="lg" className="mt-8" onClick={() => navigate(token ? '/dashboard' : '/signup')}>
          Get Started Now →
        </Button>
      </section>
    </div>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Zap } from 'lucide-react'
import { login, signup, getMe } from '../lib/api'
import useAuthStore from '../store/authStore'
import { Button, Input, Alert } from '../components/ui'

function AuthCard({ title, sub, children }) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-3">
            <Zap size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          <p className="text-gray-500 text-sm mt-1">{sub}</p>
        </div>
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          {children}
        </div>
      </div>
    </div>
  )
}

export function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const { setAuth }             = useAuthStore()
  const navigate                = useNavigate()

  async function handleLogin(e) {
    e.preventDefault()
    if (!email || !password) {
      setError('Please enter your email and password.')
      return
    }
    setLoading(true)
    setError('')
    try {
      // Step 1: get token
      const tokenRes = await login(email, password)
      const token = tokenRes.data.access_token
      if (!token) {
        setError('No token received from server.')
        return
      }

      // Step 2: save token immediately so getMe() can use it
      localStorage.setItem('token', token)

      // Step 3: get user info
      const userRes = await getMe()
      const user = userRes.data

      // Step 4: save to store (also saves to localStorage)
      setAuth(token, user)

      // Step 5: redirect
      navigate('/dashboard')
    } catch (err) {
      console.error('Login error:', err)
      const msg = err.response?.data?.detail
      if (typeof msg === 'string') {
        setError(msg)
      } else if (Array.isArray(msg)) {
        setError(msg.map(m => m.msg).join(', '))
      } else {
        setError('Login failed. Please check your email and password.')
      }
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Welcome back" sub="Login to your Q-Predictor account">
      <form onSubmit={handleLogin} className="space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
          autoComplete="email"
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="••••••••"
          required
          autoComplete="current-password"
        />
        <Button type="submit" className="w-full" size="lg" disabled={loading}>
          {loading ? 'Logging in…' : 'Login'}
        </Button>
        <p className="text-center text-sm text-gray-500">
          Don't have an account?{' '}
          <Link to="/signup" className="text-blue-600 font-medium hover:underline">
            Sign up free
          </Link>
        </p>
      </form>
    </AuthCard>
  )
}

export function SignupPage() {
  const [name, setName]         = useState('')
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const [error, setError]       = useState('')
  const [loading, setLoading]   = useState(false)
  const { setAuth }             = useAuthStore()
  const navigate                = useNavigate()

  async function handleSignup(e) {
    e.preventDefault()
    if (!name || !email || !password) {
      setError('Please fill in all fields.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    setLoading(true)
    setError('')
    try {
      // Step 1: create account
      await signup({ name, email, password })

      // Step 2: login immediately
      const tokenRes = await login(email, password)
      const token = tokenRes.data.access_token
      localStorage.setItem('token', token)

      // Step 3: get user
      const userRes = await getMe()
      setAuth(token, userRes.data)

      navigate('/dashboard')
    } catch (err) {
      console.error('Signup error:', err)
      const msg = err.response?.data?.detail
      if (typeof msg === 'string') {
        setError(msg)
      } else {
        setError('Signup failed. That email may already be registered.')
      }
      localStorage.removeItem('token')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthCard title="Create your account" sub="Start predicting exam questions in minutes">
      <form onSubmit={handleSignup} className="space-y-4">
        {error && <Alert variant="error">{error}</Alert>}
        <Input
          label="Full name"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="Asha Sharma"
          required
        />
        <Input
          label="Email"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="you@example.com"
          required
          autoComplete="email"
        />
        <Input
          label="Password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Min. 8 characters"
          required
          autoComplete="new-password"
        />
        <Button type="submit" className="w-full" size="lg" disabled={loading}>
          {loading ? 'Creating account…' : 'Create Account'}
        </Button>
        <p className="text-center text-sm text-gray-500">
          Already have an account?{' '}
          <Link to="/login" className="text-blue-600 font-medium hover:underline">
            Login
          </Link>
        </p>
      </form>
    </AuthCard>
  )
}

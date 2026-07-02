import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Upload, BarChart2, TrendingUp,
  MessageSquare, BookOpen, LogOut, ChevronRight, Zap
} from 'lucide-react'
import useAuthStore from '../../store/authStore'
import { cn } from '../../lib/utils'

const NAV = [
  { to: '/dashboard',   label: 'Dashboard',   icon: LayoutDashboard },
  { to: '/upload',      label: 'Upload Papers', icon: Upload },
  { to: '/analysis',    label: 'Analysis',    icon: BarChart2 },
  { to: '/predictions', label: 'Predictions', icon: TrendingUp },
  { to: '/chat',        label: 'AI Chat',     icon: MessageSquare },
]

function NavItem({ to, label, icon: Icon }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => cn(
        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
        isActive
          ? 'bg-brand-500 text-white shadow-sm'
          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
      )}
    >
      <Icon size={18} />
      {label}
    </NavLink>
  )
}

export function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-60 flex-shrink-0 h-screen bg-white border-r border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-500 rounded-lg flex items-center justify-center">
            <Zap size={16} className="text-white" />
          </div>
          <div>
            <p className="font-bold text-gray-900 text-sm leading-none">Q-Predictor</p>
            <p className="text-xs text-gray-400 mt-0.5">AI Exam Assistant</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(n => <NavItem key={n.to} {...n} />)}
      </nav>

      {/* User + logout */}
      <div className="px-3 py-4 border-t border-gray-100">
        <div className="flex items-center gap-3 px-2 py-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-brand-100 flex items-center justify-center text-brand-600 font-semibold text-sm">
            {user?.name?.[0]?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-800 truncate">{user?.name || 'User'}</p>
            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
        >
          <LogOut size={16} />
          Sign out
        </button>
      </div>
    </aside>
  )
}

export function AppShell({ children }) {
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto px-6 py-8">
          {children}
        </div>
      </main>
    </div>
  )
}

// ---- Page header ----
export function PageHeader({ title, description, action }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
        {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

// ---- Subject selector ----
export function SubjectBreadcrumb({ subject }) {
  return subject ? (
    <div className="flex items-center gap-1 text-sm text-gray-500 mb-4">
      <BookOpen size={14} />
      <span className="font-medium text-gray-700">{subject.name}</span>
      {subject.code && <><ChevronRight size={14} /><span>{subject.code}</span></>}
      {subject.semester && <><ChevronRight size={14} /><span>{subject.semester}</span></>}
    </div>
  ) : null
}

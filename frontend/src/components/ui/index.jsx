import { cn } from '../../lib/utils'

// ---- Card ----
export function Card({ className, children, ...props }) {
  return (
    <div className={cn('bg-white rounded-xl border border-gray-200 shadow-sm', className)} {...props}>
      {children}
    </div>
  )
}
export function CardHeader({ className, children }) {
  return <div className={cn('px-6 py-4 border-b border-gray-100', className)}>{children}</div>
}
export function CardTitle({ className, children }) {
  return <h3 className={cn('font-semibold text-gray-800 text-base', className)}>{children}</h3>
}
export function CardContent({ className, children }) {
  return <div className={cn('px-6 py-4', className)}>{children}</div>
}

// ---- Button ----
const btnVariants = {
  primary:   'bg-brand-500 hover:bg-brand-600 text-white shadow-sm',
  secondary: 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300',
  danger:    'bg-red-500 hover:bg-red-600 text-white',
  ghost:     'hover:bg-gray-100 text-gray-600',
}
const btnSizes = {
  sm: 'px-3 py-1.5 text-sm rounded-lg',
  md: 'px-4 py-2 text-sm rounded-lg',
  lg: 'px-6 py-3 text-base rounded-xl',
}
export function Button({ variant='primary', size='md', className, disabled, children, ...props }) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center gap-2 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-1 disabled:opacity-50 disabled:cursor-not-allowed',
        btnVariants[variant], btnSizes[size], className
      )}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  )
}

// ---- Badge ----
const badgeVariants = {
  default: 'bg-gray-100 text-gray-600',
  green:   'bg-green-100 text-green-700',
  yellow:  'bg-yellow-100 text-yellow-700',
  red:     'bg-red-100 text-red-700',
  blue:    'bg-blue-100 text-blue-700',
  purple:  'bg-purple-100 text-purple-700',
}
export function Badge({ variant='default', className, children }) {
  return (
    <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', badgeVariants[variant], className)}>
      {children}
    </span>
  )
}

// ---- Spinner ----
export function Spinner({ className }) {
  return (
    <svg className={cn('animate-spin h-5 w-5 text-brand-500', className)} fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
    </svg>
  )
}

// ---- Alert ----
const alertVariants = {
  info:    'bg-blue-50 border-blue-200 text-blue-800',
  success: 'bg-green-50 border-green-200 text-green-800',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  error:   'bg-red-50 border-red-200 text-red-800',
}
export function Alert({ variant='info', className, children }) {
  return (
    <div className={cn('rounded-lg border px-4 py-3 text-sm', alertVariants[variant], className)}>
      {children}
    </div>
  )
}

// ---- Input ----
export function Input({ className, label, error, ...props }) {
  return (
    <div className="w-full">
      {label && <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>}
      <input
        className={cn(
          'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition',
          error && 'border-red-400 focus:ring-red-400',
          className
        )}
        {...props}
      />
      {error && <p className="mt-1 text-xs text-red-500">{error}</p>}
    </div>
  )
}

// ---- StatCard ----
export function StatCard({ label, value, sub, icon: Icon, color='text-brand-500' }) {
  return (
    <Card>
      <CardContent className="flex items-start gap-4">
        {Icon && (
          <div className={cn('p-2 rounded-lg bg-gray-50', color)}>
            <Icon size={22} />
          </div>
        )}
        <div>
          <p className="text-2xl font-bold text-gray-900">{value ?? '—'}</p>
          <p className="text-sm font-medium text-gray-600">{label}</p>
          {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
        </div>
      </CardContent>
    </Card>
  )
}

// ---- Empty state ----
export function Empty({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && <Icon size={40} className="text-gray-300 mb-3" />}
      <p className="font-medium text-gray-600 mb-1">{title}</p>
      {description && <p className="text-sm text-gray-400 mb-4">{description}</p>}
      {action}
    </div>
  )
}

// ---- Progress bar ----
export function ProgressBar({ value, className }) {
  return (
    <div className={cn('w-full bg-gray-200 rounded-full h-2', className)}>
      <div
        className="bg-brand-500 h-2 rounded-full transition-all duration-300"
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  )
}

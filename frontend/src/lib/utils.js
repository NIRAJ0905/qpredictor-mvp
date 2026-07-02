import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

export function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  })
}

export function fmtPct(n) {
  return `${Number(n).toFixed(1)}%`
}

export function confidenceColor(score) {
  if (score >= 75) return 'text-green-600 bg-green-50'
  if (score >= 50) return 'text-yellow-600 bg-yellow-50'
  return 'text-red-500 bg-red-50'
}

export function confidenceBadge(score) {
  if (score >= 75) return 'HIGH'
  if (score >= 50) return 'MEDIUM'
  return 'LOW'
}

export function statusColor(status) {
  const map = {
    processed:  'bg-green-100 text-green-700',
    processing: 'bg-blue-100 text-blue-700',
    uploaded:   'bg-yellow-100 text-yellow-700',
    failed:     'bg-red-100 text-red-700',
  }
  return map[status] || 'bg-gray-100 text-gray-600'
}

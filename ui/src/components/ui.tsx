/** Small shared presentational components. */
import type { ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import { AlertTriangle, CheckCircle2, Clock3, FileEdit, XCircle } from 'lucide-react'
import type { Priority, WorkOrderStatus } from '../api'
import { initials, PRIORITY_LABEL, STATUS_LABEL } from '../lib/format'

const PRIORITY_STYLE: Record<Priority, string> = {
  high: 'bg-red-50 text-red-700 ring-red-600/20',
  medium: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  low: 'bg-slate-100 text-slate-600 ring-slate-500/20',
}

const STATUS_STYLE: Record<WorkOrderStatus, string> = {
  draft: 'bg-violet-50 text-violet-700 ring-violet-600/20',
  pending: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  approved: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  rejected: 'bg-red-50 text-red-700 ring-red-600/20',
}

const STATUS_ICON: Record<WorkOrderStatus, ReactNode> = {
  draft: <FileEdit className="size-3.5" />,
  pending: <Clock3 className="size-3.5" />,
  approved: <CheckCircle2 className="size-3.5" />,
  rejected: <XCircle className="size-3.5" />,
}

const PILL = 'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset'

/** Coloured pill for a work-order priority. */
export function PriorityBadge({ priority }: { priority: Priority }) {
  return (
    <span className={`${PILL} ${PRIORITY_STYLE[priority]}`}>
      {priority === 'high' && <AlertTriangle className="size-3.5" />}
      {PRIORITY_LABEL[priority]}
    </span>
  )
}

/** Coloured pill with icon for a work-order status. */
export function StatusBadge({ status }: { status: WorkOrderStatus }) {
  return (
    <span className={`${PILL} ${STATUS_STYLE[status]}`}>
      {STATUS_ICON[status]}
      {STATUS_LABEL[status]}
    </span>
  )
}

/** Monospace chip for a machine code like "PRES-3". */
export function MachineChip({ code }: { code: string }) {
  return (
    <span className="rounded-md bg-slate-900 px-1.5 py-0.5 font-mono text-[11px] font-semibold tracking-wide text-white">
      {code}
    </span>
  )
}

/** Round avatar with initials. */
export function Avatar({ userId, className = '' }: { userId: string; className?: string }) {
  return (
    <span
      className={`inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-slate-200 text-[11px] font-semibold text-slate-700 ${className}`}
    >
      {initials(userId)}
    </span>
  )
}

/** Renders assistant markdown (bold, lists, headings) with readable typography. */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="prose prose-sm prose-slate max-w-none prose-p:my-1.5 prose-ul:my-1.5 prose-ol:my-1.5 prose-li:my-0.5 prose-headings:mb-1.5 prose-headings:mt-3 prose-strong:text-slate-900">
      <ReactMarkdown>{children}</ReactMarkdown>
    </div>
  )
}

/** Centered illustration + text for empty lists. */
export function EmptyState({ icon, title, hint }: { icon: ReactNode; title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 px-6 py-10 text-center">
      <div className="text-slate-400">{icon}</div>
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
    </div>
  )
}

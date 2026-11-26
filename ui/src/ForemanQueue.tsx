import { useCallback, useEffect, useState, type ReactNode } from 'react'
import { AlertTriangle, Check, CheckCircle2, Clock3, History, Inbox, Loader2, RefreshCw, X } from 'lucide-react'
import { api, type User, type WorkOrder } from './api'
import type { Notify } from './hooks/useToasts'
import { PRIORITY_RANK, relativeTime } from './lib/format'
import { Avatar, EmptyState, MachineChip, Markdown, PriorityBadge, StatusBadge } from './components/ui'

/** Minimum reason length; mirrors RejectRequest.reason (min_length=3) on the API. */
const MIN_REASON_LENGTH = 3

/** How many recent decisions to show under the queue. */
const RECENT_DECISIONS_LIMIT = 6

/** Left-edge colour per priority, so urgent cards stand out while scanning. */
const PRIORITY_STRIPE = { high: 'bg-red-500', medium: 'bg-amber-400', low: 'bg-slate-300' } as const

interface Props {
  user: User
  notify: Notify
}

/** Foreman screen: review PENDING work orders (urgent first) and approve or reject them. */
export function ForemanQueue({ user, notify }: Props) {
  const [orders, setOrders] = useState<WorkOrder[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [busyId, setBusyId] = useState<number | null>(null) // order currently being decided

  const load = useCallback(async () => {
    setIsLoading(true)
    try {
      setOrders(await api.listWorkOrders(user))
    } catch (err) {
      notify('error', `Liste yüklenemedi: ${(err as Error).message}`)
    } finally {
      setIsLoading(false)
    }
  }, [user, notify])

  useEffect(() => {
    void load()
  }, [load])

  // Queue order: highest priority first, then oldest first (first come, first served).
  const pending = orders
    .filter((order) => order.status === 'pending')
    .sort(
      (a, b) =>
        PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority] || a.created_at.localeCompare(b.created_at),
    )
  const recent = orders
    .filter((order) => order.reviewed_at !== null)
    .sort((a, b) => (b.reviewed_at ?? '').localeCompare(a.reviewed_at ?? ''))
    .slice(0, RECENT_DECISIONS_LIMIT)
  const today = new Date().toDateString()
  const decidedToday = orders.filter(
    (order) => order.reviewed_at && new Date(order.reviewed_at).toDateString() === today,
  ).length

  /** Run approve/reject, then refresh (also after 409: someone else may have decided). */
  async function decide(order: WorkOrder, action: () => Promise<WorkOrder>, successText: string) {
    setBusyId(order.id)
    try {
      await action()
      notify('success', successText)
    } catch (err) {
      notify('error', (err as Error).message)
    } finally {
      setBusyId(null)
      await load()
    }
  }

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-5xl space-y-8 px-4 py-8 sm:px-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Onay kuyruğu</h1>
            <p className="mt-1 text-sm text-slate-500">
              Asistanın hazırladığı ve teknisyenlerin gönderdiği iş emirleri. Onayın olmadan hiçbiri işleme alınmaz.
            </p>
          </div>
          <button
            onClick={() => void load()}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:bg-slate-50"
          >
            <RefreshCw className={`size-4 ${isLoading ? 'animate-spin' : ''}`} /> Yenile
          </button>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <StatCard icon={<Clock3 className="size-5" />} label="Onay bekleyen" value={pending.length} tone="amber" />
          <StatCard
            icon={<AlertTriangle className="size-5" />}
            label="Yüksek öncelikli"
            value={pending.filter((order) => order.priority === 'high').length}
            tone="red"
          />
          <StatCard icon={<CheckCircle2 className="size-5" />} label="Bugün karara bağlanan" value={decidedToday} tone="emerald" />
        </div>

        <section className="space-y-3">
          {!isLoading && pending.length === 0 ? (
            <EmptyState
              icon={<Inbox className="size-8" />}
              title="Kuyruk boş"
              hint="Onay bekleyen iş emri yok. Yeni gönderimler burada görünecek."
            />
          ) : (
            pending.map((order) => (
              <PendingCard
                key={order.id}
                order={order}
                isBusy={busyId === order.id}
                onApprove={() =>
                  void decide(order, () => api.approve(user, order.id), `İş emri #${order.id} onaylandı.`)
                }
                onReject={(reason) =>
                  void decide(order, () => api.reject(user, order.id, reason), `İş emri #${order.id} reddedildi.`)
                }
              />
            ))
          )}
        </section>

        {recent.length > 0 && (
          <section>
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-700">
              <History className="size-4 text-slate-400" /> Son kararlar
            </h2>
            <div className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white">
              {recent.map((order) => (
                <div key={order.id} className="flex flex-wrap items-center gap-3 px-4 py-3 text-sm">
                  <MachineChip code={order.machine_code} />
                  <span className="min-w-0 flex-1 truncate font-medium">{order.title}</span>
                  <StatusBadge status={order.status} />
                  <span className="text-xs text-slate-500">
                    {order.reviewed_by} · {order.reviewed_at && relativeTime(order.reviewed_at)}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

const STAT_TONE = {
  amber: 'bg-amber-50 text-amber-600',
  red: 'bg-red-50 text-red-600',
  emerald: 'bg-emerald-50 text-emerald-600',
} as const

/** Small KPI tile. */
function StatCard({
  icon,
  label,
  value,
  tone,
}: {
  icon: ReactNode
  label: string
  value: number
  tone: keyof typeof STAT_TONE
}) {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className={`flex size-10 items-center justify-center rounded-xl ${STAT_TONE[tone]}`}>{icon}</div>
      <div>
        <p className="text-2xl font-semibold tabular-nums">{value}</p>
        <p className="text-xs text-slate-500">{label}</p>
      </div>
    </div>
  )
}

interface PendingCardProps {
  order: WorkOrder
  isBusy: boolean
  onApprove: () => void
  onReject: (reason: string) => void
}

/** One pending work order with approve / reject (reason required) actions. */
function PendingCard({ order, isBusy, onApprove, onReject }: PendingCardProps) {
  const [isRejecting, setIsRejecting] = useState(false)
  const [reason, setReason] = useState('')
  const canReject = reason.trim().length >= MIN_REASON_LENGTH

  return (
    <article className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className={`absolute inset-y-0 left-0 w-1 ${PRIORITY_STRIPE[order.priority]}`} />
      <div className="space-y-3 p-5 pl-6">
        <div className="flex flex-wrap items-center gap-2">
          <MachineChip code={order.machine_code} />
          <PriorityBadge priority={order.priority} />
          <span className="text-xs text-slate-400">#{order.id}</span>
          <span className="ml-auto flex items-center gap-2 text-xs text-slate-500">
            <Avatar userId={order.created_by} className="size-6 text-[10px]" />
            {order.created_by} · {relativeTime(order.created_at)}
          </span>
        </div>

        <div>
          <h3 className="text-base font-semibold leading-snug">{order.title}</h3>
          <p className="mt-1 text-sm text-slate-600">{order.description}</p>
        </div>

        <details className="rounded-xl bg-slate-50 px-4 py-2.5">
          <summary className="cursor-pointer text-xs font-medium text-slate-600 select-none">Önerilen adımlar</summary>
          <div className="pt-2">
            <Markdown>{order.proposed_actions}</Markdown>
          </div>
        </details>

        {isRejecting ? (
          <div className="space-y-2 rounded-xl border border-red-200 bg-red-50/50 p-3">
            <label className="text-xs font-medium text-red-800" htmlFor={`reason-${order.id}`}>
              Ret gerekçesi (teknisyen görecek)
            </label>
            <textarea
              id={`reason-${order.id}`}
              autoFocus
              rows={2}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="Örn: Önce yağ seviyesini ölç, sonuçla tekrar gönder."
              className="w-full resize-none rounded-lg border border-red-200 bg-white px-3 py-2 text-sm outline-none focus:border-red-400 focus:ring-4 focus:ring-red-500/10"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => {
                  setIsRejecting(false)
                  setReason('')
                }}
                className="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
              >
                Vazgeç
              </button>
              <button
                onClick={() => onReject(reason.trim())}
                disabled={!canReject || isBusy}
                className="inline-flex items-center gap-1.5 rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm transition hover:bg-red-500 disabled:opacity-50"
              >
                {isBusy ? <Loader2 className="size-4 animate-spin" /> : <X className="size-4" />} Reddet
              </button>
            </div>
          </div>
        ) : (
          <div className="flex justify-end gap-2 pt-1">
            <button
              onClick={() => setIsRejecting(true)}
              disabled={isBusy}
              className="inline-flex items-center gap-1.5 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-red-200 hover:bg-red-50 hover:text-red-700 disabled:opacity-50"
            >
              <X className="size-4" /> Reddet
            </button>
            <button
              onClick={onApprove}
              disabled={isBusy}
              className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-emerald-500 disabled:opacity-50"
            >
              {isBusy ? <Loader2 className="size-4 animate-spin" /> : <Check className="size-4" />} Onayla
            </button>
          </div>
        )}
      </div>
    </article>
  )
}

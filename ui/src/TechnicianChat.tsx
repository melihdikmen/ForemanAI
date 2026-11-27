import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react'
import {
  AlertCircle,
  ArrowUp,
  Bot,
  CheckCircle2,
  ClipboardList,
  FileEdit,
  Loader2,
  RefreshCw,
  RotateCcw,
  Send,
  Sparkles,
} from 'lucide-react'
import { api, type User, type WorkOrder, type WorkOrderDraft, type WorkOrderStatus } from './api'
import type { Notify } from './hooks/useToasts'
import { relativeTime, summarizeTools } from './lib/format'
import { Avatar, EmptyState, MachineChip, Markdown, PriorityBadge, StatusBadge } from './components/ui'

/** One chat turn. Assistant turns carry the tools used and any work-order drafts. */
interface ChatMessage {
  id: number
  author: 'technician' | 'assistant'
  text: string
  toolCalls: string[]
  drafts: WorkOrderDraft[]
  guardFlags: string[] // output-guard hits; non-empty shows a safety banner
  failed?: boolean // technician turn whose answer never arrived (server down, crash...)
}

/** Starter questions shown on an empty chat (real machine and alarm codes from the seed). */
const SUGGESTIONS = [
  "PRES-1'de E-102 alarmı var, ne kontrol etmeliyim?",
  'Son 6 ayda en çok arıza veren makine hangisi?',
  'KOMP-1 için C-302 alarmı nasıl giderilir?',
  "PRES-3'te silindir altında yağ sızıntısı var, iş emri açar mısın?",
]

/** Filter tabs for the technician's own work orders. */
const ORDER_FILTERS: { key: WorkOrderStatus | 'all'; label: string }[] = [
  { key: 'all', label: 'Tümü' },
  { key: 'pending', label: 'Bekleyen' },
  { key: 'approved', label: 'Onaylı' },
  { key: 'rejected', label: 'Reddedilen' },
]

/** Maximum composer height before it starts scrolling (px). */
const COMPOSER_MAX_HEIGHT = 160

interface Props {
  user: User
  notify: Notify
}

/** Technician screen: chat with the assistant, send drafts for approval, track own orders. */
export function TechnicianChat({ user, notify }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState('')
  const [isAsking, setIsAsking] = useState(false)
  // Draft key ("messageId-index") -> id of the work order created from it.
  const [submittedDrafts, setSubmittedDrafts] = useState<Record<string, number>>({})
  const [submittingKey, setSubmittingKey] = useState<string | null>(null)
  const [myOrders, setMyOrders] = useState<WorkOrder[]>([])
  const [isLoadingOrders, setIsLoadingOrders] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)
  const composerRef = useRef<HTMLTextAreaElement>(null)

  const loadMyOrders = useCallback(async () => {
    setIsLoadingOrders(true)
    try {
      const all = await api.listWorkOrders(user)
      setMyOrders(all.filter((order) => order.created_by === user.id))
    } catch (err) {
      notify('error', `İş emirleri yüklenemedi: ${(err as Error).message}`)
    } finally {
      setIsLoadingOrders(false)
    }
  }, [user, notify])

  useEffect(() => {
    void loadMyOrders()
  }, [loadMyOrders])

  // Keep the newest message in view.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isAsking])

  // Grow the composer with its content, up to a limit.
  useEffect(() => {
    const textarea = composerRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(textarea.scrollHeight, COMPOSER_MAX_HEIGHT)}px`
  }, [question])

  /**
   * Send a question. With `retryMessageId`, re-sends an earlier failed question instead
   * of adding a new bubble. Safe to retry: /ask is read-only, so nothing happens twice.
   */
  async function ask(text: string, retryMessageId?: number) {
    const trimmed = text.trim()
    if (!trimmed || isAsking) return
    setIsAsking(true)
    setQuestion('')
    const questionId = retryMessageId ?? Date.now()
    setMessages((prev) =>
      retryMessageId === undefined
        ? [...prev, { id: questionId, author: 'technician', text: trimmed, toolCalls: [], drafts: [], guardFlags: [] }]
        : prev.map((message) => (message.id === questionId ? { ...message, failed: false } : message)),
    )
    try {
      const response = await api.ask(user, trimmed)
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          author: 'assistant',
          text: response.answer,
          toolCalls: response.tool_calls,
          drafts: response.drafts,
          guardFlags: response.guard_flags,
        },
      ])
    } catch (err) {
      // Keep the question on screen and mark it failed so it can be retried in one click.
      setMessages((prev) =>
        prev.map((message) => (message.id === questionId ? { ...message, failed: true } : message)),
      )
      notify('error', `Asistan cevap veremedi: ${(err as Error).message}`)
    } finally {
      setIsAsking(false)
      composerRef.current?.focus()
    }
  }

  function handleComposerKey(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter inserts a newline.
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void ask(question)
    }
  }

  async function submitDraft(draftKey: string, draft: WorkOrderDraft) {
    setSubmittingKey(draftKey)
    try {
      const created = await api.submitDraft(user, draft)
      setSubmittedDrafts((prev) => ({ ...prev, [draftKey]: created.id }))
      notify('success', `İş emri #${created.id} ustabaşı onayına gönderildi.`)
      await loadMyOrders()
    } catch (err) {
      notify('error', `Gönderilemedi: ${(err as Error).message}`)
    } finally {
      setSubmittingKey(null)
    }
  }

  return (
    <div className="grid h-full lg:grid-cols-[minmax(0,1fr)_380px]">
      {/* Chat column */}
      <section className="flex min-h-0 flex-col">
        <div ref={scrollRef} className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-3xl space-y-6 px-4 py-8 sm:px-6">
            {messages.length === 0 && <ChatWelcome name={user.displayName} onPick={(text) => void ask(text)} />}

            {messages.map((message) =>
              message.author === 'technician' ? (
                <div key={message.id} className="flex flex-col items-end gap-1.5">
                  <div
                    className={`max-w-[85%] rounded-2xl rounded-br-md px-4 py-2.5 text-sm whitespace-pre-wrap text-white ${
                      message.failed ? 'bg-slate-400' : 'bg-slate-900'
                    }`}
                  >
                    {message.text}
                  </div>
                  {message.failed && (
                    <div className="flex items-center gap-2 text-xs text-red-600">
                      <AlertCircle className="size-3.5" /> Cevap alınamadı
                      <button
                        onClick={() => void ask(message.text, message.id)}
                        disabled={isAsking}
                        className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-white px-2 py-1 font-medium text-red-700 transition hover:bg-red-50 disabled:opacity-50"
                      >
                        <RotateCcw className="size-3.5" /> Tekrar dene
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div key={message.id} className="flex gap-3">
                  <AssistantAvatar />
                  <div className="min-w-0 flex-1 space-y-3">
                    {message.toolCalls.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {summarizeTools(message.toolCalls).map((label) => (
                          <span
                            key={label}
                            className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-600"
                          >
                            <Sparkles className="size-3" /> {label}
                          </span>
                        ))}
                      </div>
                    )}
                    {message.guardFlags.length > 0 && (
                      <div className="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                        Güvenlik denetimi bu cevabı işaretledi ({message.guardFlags.join(', ')}). Cevabın
                        sonundaki uyarıyı okuyun; güvenlik adımlarını atlamayın.
                      </div>
                    )}
                    <div className="rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
                      <Markdown>{message.text}</Markdown>
                    </div>
                    {message.drafts.map((draft, index) => {
                      const draftKey = `${message.id}-${index}`
                      return (
                        <DraftCard
                          key={draftKey}
                          draft={draft}
                          createdId={submittedDrafts[draftKey]}
                          isSubmitting={submittingKey === draftKey}
                          onSubmit={() => void submitDraft(draftKey, draft)}
                        />
                      )
                    })}
                  </div>
                </div>
              ),
            )}

            {isAsking && (
              <div className="flex gap-3">
                <AssistantAvatar />
                <div className="flex items-center gap-3 rounded-2xl rounded-tl-md border border-slate-200 bg-white px-4 py-3 shadow-sm">
                  <span className="flex gap-1">
                    {[0, 150, 300].map((delay) => (
                      <span
                        key={delay}
                        className="size-1.5 animate-bounce rounded-full bg-slate-400"
                        style={{ animationDelay: `${delay}ms` }}
                      />
                    ))}
                  </span>
                  <span className="text-xs text-slate-500">Kılavuzlar ve arıza kayıtları inceleniyor…</span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Composer */}
        <div className="border-t border-slate-200 bg-white/80 px-4 py-4 backdrop-blur sm:px-6">
          <div className="mx-auto max-w-3xl">
            <div className="flex items-end gap-2 rounded-2xl border border-slate-300 bg-white p-2 shadow-sm transition focus-within:border-slate-400 focus-within:ring-4 focus-within:ring-slate-900/5">
              <textarea
                ref={composerRef}
                rows={1}
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={handleComposerKey}
                placeholder="Arızayı, alarm kodunu veya sorunu yaz…"
                disabled={isAsking}
                className="max-h-40 flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-slate-400 disabled:opacity-60"
              />
              <button
                onClick={() => void ask(question)}
                disabled={isAsking || !question.trim()}
                aria-label="Gönder"
                className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-slate-900 text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
              >
                {isAsking ? <Loader2 className="size-4 animate-spin" /> : <ArrowUp className="size-4" />}
              </button>
            </div>
            <p className="mt-2 text-center text-[11px] text-slate-400">
              Asistan hata yapabilir. Enerji kesme / LOTO adımlarını her zaman uygula.
            </p>
          </div>
        </div>
      </section>

      {/* My work orders */}
      <MyOrdersPanel orders={myOrders} isLoading={isLoadingOrders} onRefresh={() => void loadMyOrders()} />
    </div>
  )
}

/** Round bot avatar for assistant messages. */
function AssistantAvatar() {
  return (
    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-orange-500 to-amber-500 text-white shadow-sm">
      <Bot className="size-4" />
    </div>
  )
}

/** Empty-chat greeting with clickable example questions. */
function ChatWelcome({ name, onPick }: { name: string; onPick: (text: string) => void }) {
  return (
    <div className="pt-6 text-center sm:pt-16">
      <div className="mx-auto mb-4 flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-500 to-amber-500 text-white shadow-md">
        <Bot className="size-6" />
      </div>
      <h2 className="text-xl font-semibold tracking-tight">Merhaba {name.split(' ')[0]}, hangi makinede sorun var?</h2>
      <p className="mt-1 text-sm text-slate-500">
        Kılavuzlarda arar, arıza geçmişine bakar, gerekirse iş emri taslağı hazırlarım.
      </p>
      <div className="mt-8 grid gap-2 text-left sm:grid-cols-2">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            onClick={() => onPick(suggestion)}
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-700 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  )
}

interface DraftCardProps {
  draft: WorkOrderDraft
  createdId: number | undefined // set once the draft was submitted
  isSubmitting: boolean
  onSubmit: () => void
}

/** An unsaved work-order draft proposed by the assistant, with a submit button. */
function DraftCard({ draft, createdId, isSubmitting, onSubmit }: DraftCardProps) {
  const isSubmitted = createdId !== undefined
  return (
    <div className="overflow-hidden rounded-2xl border border-violet-200 bg-white shadow-sm">
      <div className="flex items-center gap-2 border-b border-violet-100 bg-violet-50/60 px-4 py-2 text-xs font-medium text-violet-800">
        <FileEdit className="size-3.5" />
        İş emri taslağı
        <span className="font-normal text-violet-600">· henüz kaydedilmedi</span>
      </div>
      <div className="space-y-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <MachineChip code={draft.machine_code} />
          <PriorityBadge priority={draft.priority} />
        </div>
        <h3 className="font-semibold leading-snug">{draft.title}</h3>
        <p className="text-sm text-slate-600">{draft.description}</p>
        <details className="group rounded-lg bg-slate-50 px-3 py-2">
          <summary className="cursor-pointer text-xs font-medium text-slate-600 select-none">Önerilen adımlar</summary>
          <div className="pt-2">
            <Markdown>{draft.proposed_actions}</Markdown>
          </div>
        </details>
        <div className="flex items-center justify-end pt-1">
          {isSubmitted ? (
            <span className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-700">
              <CheckCircle2 className="size-4" /> Onaya gönderildi · #{createdId}
            </span>
          ) : (
            <button
              onClick={onSubmit}
              disabled={isSubmitting}
              className="inline-flex items-center gap-2 rounded-xl bg-violet-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-violet-500 disabled:opacity-60"
            >
              {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              Onaya gönder
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

interface MyOrdersPanelProps {
  orders: WorkOrder[]
  isLoading: boolean
  onRefresh: () => void
}

/** Side panel listing the technician's submitted work orders with status filters. */
function MyOrdersPanel({ orders, isLoading, onRefresh }: MyOrdersPanelProps) {
  const [filter, setFilter] = useState<WorkOrderStatus | 'all'>('all')
  const visible = filter === 'all' ? orders : orders.filter((order) => order.status === filter)
  const countFor = (key: WorkOrderStatus | 'all') =>
    key === 'all' ? orders.length : orders.filter((order) => order.status === key).length

  return (
    <aside className="hidden min-h-0 flex-col border-l border-slate-200 bg-white lg:flex">
      <div className="flex items-center justify-between px-5 pt-5">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <ClipboardList className="size-4 text-slate-500" /> İş emirlerim
        </h2>
        <button
          onClick={onRefresh}
          aria-label="Yenile"
          className="rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-800"
        >
          <RefreshCw className={`size-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <div className="flex gap-1 px-5 pt-3 pb-3">
        {ORDER_FILTERS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setFilter(key)}
            className={`rounded-lg px-2 py-1 text-xs font-medium transition ${
              filter === key ? 'bg-slate-900 text-white' : 'text-slate-500 hover:bg-slate-100'
            }`}
          >
            {label} <span className="opacity-60">{countFor(key)}</span>
          </button>
        ))}
      </div>

      <div className="flex-1 space-y-2 overflow-y-auto px-5 pb-5">
        {visible.length === 0 ? (
          <EmptyState
            icon={<ClipboardList className="size-6" />}
            title="Burada henüz iş emri yok"
            hint="Asistandan iş emri iste, taslağı onaya gönder."
          />
        ) : (
          visible.map((order) => (
            <div key={order.id} className="rounded-xl border border-slate-200 p-3 transition hover:border-slate-300">
              <div className="flex items-center gap-2">
                <MachineChip code={order.machine_code} />
                <span className="text-xs text-slate-400">#{order.id}</span>
                <span className="ml-auto">
                  <StatusBadge status={order.status} />
                </span>
              </div>
              <p className="mt-2 text-sm leading-snug font-medium">{order.title}</p>
              <p className="mt-1 text-xs text-slate-500">{relativeTime(order.created_at)} gönderildi</p>
              {order.status === 'rejected' && order.rejection_reason && (
                <div className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-800">
                  <span className="font-semibold">{order.reviewed_by}:</span> {order.rejection_reason}
                </div>
              )}
              {order.status === 'approved' && order.reviewed_by && (
                <p className="mt-2 flex items-center gap-1.5 text-xs text-emerald-700">
                  <Avatar userId={order.reviewed_by} className="size-5 text-[9px]" />
                  {order.reviewed_by} onayladı
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </aside>
  )
}

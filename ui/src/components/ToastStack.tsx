import { CheckCircle2, X, XCircle } from 'lucide-react'
import type { Toast } from '../hooks/useToasts'

/** Bottom-right stack of transient notifications. */
export function ToastStack({ toasts, onDismiss }: { toasts: Toast[]; onDismiss: (id: number) => void }) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className="pointer-events-auto flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-lg shadow-slate-900/5"
        >
          {toast.kind === 'success' ? (
            <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600" />
          ) : (
            <XCircle className="mt-0.5 size-5 shrink-0 text-red-600" />
          )}
          <p className="flex-1 text-sm text-slate-700">{toast.message}</p>
          <button
            onClick={() => onDismiss(toast.id)}
            className="rounded p-0.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            aria-label="Kapat"
          >
            <X className="size-4" />
          </button>
        </div>
      ))}
    </div>
  )
}

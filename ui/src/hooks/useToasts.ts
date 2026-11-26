import { useCallback, useState } from 'react'

export type ToastKind = 'success' | 'error'

export interface Toast {
  id: number
  kind: ToastKind
  message: string
}

/** How long a toast stays on screen before it disappears by itself. */
const TOAST_DURATION_MS = 4000

/** Minimal toast queue: `notify` adds a message that auto-dismisses. */
export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const notify = useCallback(
    (kind: ToastKind, message: string) => {
      const id = Date.now() + Math.random()
      setToasts((prev) => [...prev, { id, kind, message }])
      window.setTimeout(() => dismiss(id), TOAST_DURATION_MS)
    },
    [dismiss],
  )

  return { toasts, notify, dismiss }
}

export type Notify = (kind: ToastKind, message: string) => void

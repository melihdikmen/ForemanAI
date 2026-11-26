/**
 * Typed client for the FastAPI backend.
 *
 * Types are hand-mirrored from the Pydantic models (app/tools/work_orders.py,
 * app/api/work_orders.py, app/api/main.py). A larger project would generate them
 * from FastAPI's /openapi.json (e.g. with openapi-typescript) to avoid drift.
 */

export type Role = 'technician' | 'foreman'
export type Priority = 'low' | 'medium' | 'high'
export type WorkOrderStatus = 'draft' | 'pending' | 'approved' | 'rejected'

/** The signed-in user. v1 identity is fake: it is sent as plain headers. */
export interface User {
  id: string // ASCII user id sent in X-User (headers cannot carry "ı", "ş"...)
  displayName: string // shown in the UI only
  role: Role
}

/** A work-order proposal from the agent; also the POST /work-orders body. */
export interface WorkOrderDraft {
  machine_code: string
  title: string
  description: string
  proposed_actions: string
  priority: Priority
}

/** A work order as stored in the database. */
export interface WorkOrder extends WorkOrderDraft {
  id: number
  status: WorkOrderStatus
  created_by: string
  created_at: string
  reviewed_by: string | null
  reviewed_at: string | null
  rejection_reason: string | null
}

/** Response of POST /ask. */
export interface AskResponse {
  answer: string
  total_tokens: number
  cost_usd: number | null
  tool_calls: string[]
  drafts: WorkOrderDraft[]
}

/** Fetch JSON from the API as `user`; throws an Error carrying FastAPI's `detail`. */
async function request<T>(user: User, path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-User': user.id,
      'X-Role': user.role,
      ...init.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : response.statusText
    throw new Error(`${response.status}: ${detail}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  ask: (user: User, question: string) =>
    request<AskResponse>(user, '/ask', { method: 'POST', body: JSON.stringify({ question }) }),

  submitDraft: (user: User, draft: WorkOrderDraft) =>
    request<WorkOrder>(user, '/work-orders', { method: 'POST', body: JSON.stringify(draft) }),

  listWorkOrders: (user: User, status?: WorkOrderStatus) =>
    request<WorkOrder[]>(user, `/work-orders${status ? `?status=${status}` : ''}`),

  approve: (user: User, id: number) =>
    request<WorkOrder>(user, `/work-orders/${id}/approve`, { method: 'POST' }),

  reject: (user: User, id: number, reason: string) =>
    request<WorkOrder>(user, `/work-orders/${id}/reject`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    }),
}

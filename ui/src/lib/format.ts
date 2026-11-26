/** Turkish labels and formatting helpers shared by the screens. */
import type { Priority, WorkOrderStatus } from '../api'

export const PRIORITY_LABEL: Record<Priority, string> = {
  low: 'Düşük',
  medium: 'Orta',
  high: 'Yüksek',
}

export const STATUS_LABEL: Record<WorkOrderStatus, string> = {
  draft: 'Taslak',
  pending: 'Onay bekliyor',
  approved: 'Onaylandı',
  rejected: 'Reddedildi',
}

/** Sort weight so high-priority orders come first. */
export const PRIORITY_RANK: Record<Priority, number> = { high: 0, medium: 1, low: 2 }

/** Turkish names for the agent's tools, shown as "what the assistant did" chips. */
export const TOOL_LABEL: Record<string, string> = {
  search_manuals: 'Kılavuz araması',
  get_fault_history: 'Arıza geçmişi',
  draft_work_order: 'İş emri taslağı',
}

const relativeFormatter = new Intl.RelativeTimeFormat('tr', { numeric: 'auto' })

/** "3 dakika önce" style text for an ISO timestamp (API times are local, naive). */
export function relativeTime(isoTimestamp: string): string {
  const seconds = Math.round((new Date(isoTimestamp).getTime() - Date.now()) / 1000)
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ['day', 86400],
    ['hour', 3600],
    ['minute', 60],
  ]
  for (const [unit, unitSeconds] of units) {
    if (Math.abs(seconds) >= unitSeconds) {
      return relativeFormatter.format(Math.round(seconds / unitSeconds), unit)
    }
  }
  return 'az önce'
}

/** Two-letter initials for an avatar, e.g. "ahmet.yilmaz" -> "AY". */
export function initials(userId: string): string {
  return userId
    .split(/[.\s_-]+/)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')
    .slice(0, 2)
}

/** Group tool calls into "label ×count" chips, keeping first-seen order. */
export function summarizeTools(toolCalls: string[]): string[] {
  const counts = new Map<string, number>()
  for (const tool of toolCalls) counts.set(tool, (counts.get(tool) ?? 0) + 1)
  return [...counts].map(([tool, count]) => {
    const label = TOOL_LABEL[tool] ?? tool
    return count > 1 ? `${label} ×${count}` : label
  })
}

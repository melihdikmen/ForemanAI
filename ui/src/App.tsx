import { useState } from 'react'
import { ShieldAlert, Wrench } from 'lucide-react'
import type { User } from './api'
import { Avatar } from './components/ui'
import { ToastStack } from './components/ToastStack'
import { useToasts } from './hooks/useToasts'
import { ForemanQueue } from './ForemanQueue'
import { TechnicianChat } from './TechnicianChat'

/** Demo users for the fake (v1) identity. Real deployments would use SSO. */
const DEMO_USERS: User[] = [
  { id: 'ahmet.yilmaz', displayName: 'Ahmet Yılmaz', role: 'technician' },
  { id: 'mehmet.kaya', displayName: 'Mehmet Kaya', role: 'foreman' },
]

const ROLE_LABEL: Record<User['role'], string> = { technician: 'Teknisyen', foreman: 'Ustabaşı' }

/** Root: app shell with a demo-user switcher; shows the screen for the user's role. */
export default function App() {
  const [user, setUser] = useState<User>(DEMO_USERS[0])
  const { toasts, notify, dismiss } = useToasts()

  return (
    <div className="flex h-full flex-col">
      <header className="flex h-16 shrink-0 items-center gap-4 border-b border-slate-200 bg-white px-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex size-9 items-center justify-center rounded-xl bg-gradient-to-br from-orange-500 to-amber-500 text-white shadow-sm">
            <Wrench className="size-5" />
          </div>
          <div className="leading-tight">
            <p className="text-sm font-semibold">Bakım Asistanı</p>
            <p className="hidden text-xs text-slate-500 sm:block">Metal işleme · Bakım ekibi</p>
          </div>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <span
            title="Kimlik sahte (X-User / X-Role başlıkları). Gerçek kurulumda SSO kullanılır."
            className="hidden items-center gap-1 rounded-full bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800 ring-1 ring-amber-600/20 ring-inset md:inline-flex"
          >
            <ShieldAlert className="size-3.5" /> Demo kimlik
          </span>
          <div className="flex rounded-xl bg-slate-100 p-1" role="tablist" aria-label="Kullanıcı seç">
            {DEMO_USERS.map((demo) => {
              const isActive = demo.id === user.id
              return (
                <button
                  key={demo.id}
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setUser(demo)}
                  className={`flex items-center gap-2 rounded-lg px-2.5 py-1.5 text-left transition ${
                    isActive ? 'bg-white shadow-sm' : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  <Avatar userId={demo.id} className="size-6 text-[10px]" />
                  <span className="hidden leading-tight sm:block">
                    <span className="block text-xs font-semibold">{demo.displayName}</span>
                    <span className="block text-[11px] text-slate-500">{ROLE_LABEL[demo.role]}</span>
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </header>

      <main className="min-h-0 flex-1">
        {/* key={user.id} remounts the screen so state never leaks between users. */}
        {user.role === 'technician' ? (
          <TechnicianChat key={user.id} user={user} notify={notify} />
        ) : (
          <ForemanQueue key={user.id} user={user} notify={notify} />
        )}
      </main>

      <ToastStack toasts={toasts} onDismiss={dismiss} />
    </div>
  )
}

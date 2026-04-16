import { Outlet, NavLink } from 'react-router-dom'

const navItems = [
  { to: '/dashboard', label: 'Home',    icon: '🏠' },
  { to: '/journal',   label: 'Journal', icon: '✍️' },
  { to: '/history',   label: 'History', icon: '📖' },
  { to: '/chat',      label: 'Chat',    icon: '💬' },
]

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-gradient-to-br from-primary-50 via-lavender-50 to-calm-50">
      {/* Sidebar */}
      <aside className="w-full md:w-60 md:min-h-screen bg-white/80 backdrop-blur border-b md:border-b-0 md:border-r border-primary-100 flex md:flex-col items-center md:items-stretch px-4 md:px-0 py-3 md:py-8 gap-2 md:gap-1 shadow-soft shrink-0">
        {/* Logo */}
        <div className="hidden md:flex flex-col items-center mb-8 px-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary-400 to-lavender-300 flex items-center justify-center text-2xl shadow-card mb-2">
            🧠
          </div>
          <span className="font-bold text-primary-600 text-lg tracking-tight">MindMitra</span>
          <span className="text-xs text-slate-400 font-medium">AI Journaling</span>
        </div>

        {/* Mobile logo */}
        <span className="md:hidden font-bold text-primary-600 text-base mr-auto">🧠 MindMitra</span>

        {/* Nav */}
        <nav className="flex md:flex-col gap-1 md:px-3 w-full md:w-auto">
          {navItems.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-2xl text-sm font-medium transition-all duration-200
                ${isActive
                  ? 'bg-primary-100 text-primary-600 shadow-soft'
                  : 'text-slate-500 hover:bg-lavender-50 hover:text-primary-500'}`
              }
            >
              <span className="text-base">{icon}</span>
              <span className="hidden sm:inline">{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* Footer */}
        <div className="hidden md:flex mt-auto px-6 pb-2 text-xs text-slate-300 text-center">
          Built with care 💜
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 md:px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
import { NavLink, useNavigate } from 'react-router-dom'

const links = [
  { to: '/',         icon: '▦', label: 'Dashboard' },
  { to: '/scan',     icon: '⊕', label: 'New Scan'  },
  { to: '/patients', icon: '◉', label: 'Patients'  },
  { to: '/reports',  icon: '≡', label: 'Reports'   },
  { to: '/billing',  icon: '◈', label: 'Billing'   },
]

export default function Layout({ children }) {
  const navigate = useNavigate()
  const name     = localStorage.getItem('name') || 'Doctor'

  const logout = () => { localStorage.clear(); navigate('/login') }

  return (
    <div className="flex min-h-screen bg-slate-950">

      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 flex flex-col bg-slate-900 border-r border-slate-800">
        {/* Logo */}
        <div className="px-6 py-6 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-cyan-500 rounded-xl flex items-center justify-center text-white font-bold text-lg">O</div>
            <div>
              <p className="text-white font-bold text-sm leading-tight">OralScan AI</p>
              <p className="text-slate-500 text-xs">Medical Platform</p>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {links.map(l => (
            <NavLink key={l.to} to={l.to} end={l.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                  isActive
                    ? 'bg-cyan-500/15 text-cyan-400 border border-cyan-500/25'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }>
              <span className="text-base w-5 text-center">{l.icon}</span>
              {l.label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-3 py-4 border-t border-slate-800">
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-800">
            <div className="w-8 h-8 bg-cyan-500 rounded-full flex items-center justify-center text-white text-sm font-bold">
              {name.charAt(0).toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate">{name}</p>
              <p className="text-slate-500 text-xs">Doctor</p>
            </div>
            <button onClick={logout} title="Logout"
              className="text-slate-500 hover:text-red-400 transition-colors text-lg">⏻</button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto bg-slate-50">
        {children}
      </main>
    </div>
  )
}
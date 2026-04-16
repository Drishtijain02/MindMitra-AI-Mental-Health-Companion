import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getEntries } from '../api/client'
import EmotionBadge from '../components/EmotionBadge'
import Spinner from '../components/Spinner'

export default function Dashboard() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState(null)

  useEffect(() => {
    getEntries()
      .then(res => setEntries(res.data.data || res.data))
      .catch(() => setError('Could not connect to backend.'))
      .finally(() => setLoading(false))
  }, [])

  const hour = new Date().getHours()
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening'

  return (
    <div className="animate-fade-in space-y-8">
      {/* Hero */}
      <div className="rounded-4xl bg-gradient-to-br from-primary-500 to-lavender-300 p-8 text-white shadow-card">
        <p className="text-primary-100 text-sm font-medium mb-1">{new Date().toLocaleDateString('en-US', { weekday:'long', month:'long', day:'numeric' })}</p>
        <h1 className="text-3xl font-bold mb-2">{greeting} 👋</h1>
        <p className="text-primary-100 text-sm leading-relaxed max-w-md">
          Your mind matters. Take a moment to reflect, express, and grow.
        </p>
        <Link
          to="/journal"
          className="inline-flex items-center gap-2 mt-5 bg-white text-primary-600 font-semibold text-sm px-5 py-2.5 rounded-2xl shadow hover:shadow-md transition-all duration-200 hover:scale-105"
        >
          ✍️ Write today's entry
        </Link>
      </div>

      {/* Quick stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Total Entries', value: entries.length, icon: '📓' },
          { label: 'This Week',     value: entries.filter(e => {
              const d = new Date(e.date); const now = new Date()
              return (now - d) / 86400000 <= 7
            }).length, icon: '📅' },
          { label: 'Emotions Logged', value: [...new Set(entries.map(e => e.emotion).filter(Boolean))].length, icon: '🎭' },
        ].map(({ label, value, icon }) => (
          <div key={label} className="bg-white rounded-3xl p-4 shadow-soft text-center">
            <div className="text-2xl mb-1">{icon}</div>
            <div className="text-2xl font-bold text-primary-600">{loading ? '—' : value}</div>
            <div className="text-xs text-slate-400 mt-0.5 font-medium">{label}</div>
          </div>
        ))}
      </div>

      {/* Recent entries */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-slate-700">Recent Entries</h2>
          <Link to="/history" className="text-xs text-primary-500 font-medium hover:underline">View all →</Link>
        </div>

        {loading && <div className="flex justify-center py-10"><Spinner /></div>}
        {error   && <p className="text-sm text-rose-500 bg-rose-50 rounded-2xl px-4 py-3">{error}</p>}

        {!loading && !error && entries.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <div className="text-4xl mb-3">📭</div>
            <p className="text-sm">No entries yet. Start your first journal!</p>
          </div>
        )}

        <div className="space-y-3">
          {entries.slice(0, 4).map((e, i) => (
            <div key={i} className="bg-white rounded-3xl p-4 shadow-soft border border-slate-50 hover:shadow-card transition-shadow duration-200">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm text-slate-600 line-clamp-2 flex-1">{e.text}</p>
                {e.emotion && <EmotionBadge emotion={e.emotion} />}
              </div>
              {e.date && (
                <p className="text-xs text-slate-300 mt-2">
                  {new Date(e.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
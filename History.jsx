import { useEffect, useState } from 'react'
import { getEntries } from '../api/client'
import EmotionBadge from '../components/EmotionBadge'
import AIResponseCard from '../components/AIResponseCard'
import Spinner from '../components/Spinner'

// Entry Card
function EntryCard({ entry }) {
  const [open, setOpen] = useState(false)

  return (
    <div className="bg-white rounded-3xl shadow-soft border border-slate-50 overflow-hidden">
      
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left p-5"
      >
        <p className="text-sm text-slate-700">{entry.text}</p>
        <p className="text-xs text-slate-400 mt-1">
          🕐 {entry.display_date} • {entry.time}
        </p>

        {entry.emotion && <EmotionBadge emotion={entry.emotion} />}
      </button>

      {open && entry.ai_response && (
        <div className="p-4 border-t">
          <AIResponseCard aiResponse={entry.ai_response} />
        </div>
      )}
    </div>
  )
}


// MAIN COMPONENT
export default function History() {

  // ✅ THIS WAS MISSING / BROKEN
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getEntries()
      .then(res => {
        console.log("API RESPONSE:", res.data)

        const data = res.data?.data || res.data || []
        setEntries(Array.isArray(data) ? data : [])
      })
      .catch(err => {
        console.error(err)
        setError('Could not load entries.')
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">

      <h1 className="text-2xl font-bold">Journal History</h1>

      {loading && <Spinner />}

      {error && <p className="text-red-500">{error}</p>}

      {!loading && entries.length === 0 && (
        <p>No entries yet</p>
      )}

      <div className="space-y-3">
        {entries.map((entry, i) => (
          <EntryCard key={i} entry={entry} />
        ))}
      </div>

    </div>
  )
}
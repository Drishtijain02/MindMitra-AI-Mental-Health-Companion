import { useState } from 'react'
import { saveEntry } from '../api/client'
import EmotionBadge from '../components/EmotionBadge'
import AIResponseCard from '../components/AIResponseCard'
import Spinner from '../components/Spinner'

export default function Journal() {
  const [text, setText]       = useState('')
  const [result, setResult]   = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const entry = result?.entry

  const handleSave = async () => {
    if (!text.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await saveEntry(text.trim())
      setResult({
        entry: res.data.entry,
        support: res.data.support,
        helplines: res.data.helplines
      })
    } catch {
      setError('Could not save your entry. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleNew = () => { setResult(null); setText('') }

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Today's Journal</h1>
        <p className="text-sm text-slate-400 mt-1">Write freely. MindMitra will listen.</p>
      </div>

      {!result ? (
        <div className="bg-white rounded-4xl shadow-card p-6 space-y-4 border border-slate-50">
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            rows={12}
            placeholder="Write your thoughts here..."
            className="w-full resize-none outline-none text-slate-700 text-base leading-relaxed placeholder-slate-300 font-light"
          />
          <div className="flex items-center justify-between border-t border-slate-50 pt-4">
            <span className="text-xs text-slate-300">{text.length} characters</span>
            <button
              onClick={handleSave}
              disabled={loading || !text.trim()}
              className="flex items-center gap-2 bg-primary-500 hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold text-sm px-6 py-2.5 rounded-2xl transition-all duration-200 shadow hover:shadow-md"
            >
              {loading ? <><Spinner size="sm" /> Saving…</> : '💾 Save Entry'}
            </button>
          </div>
        </div>
      ) : (
        <div className="animate-slide-up space-y-4">
          {/* Original text */}
          <div className="bg-white rounded-4xl shadow-soft p-5 border border-slate-50">
            <p className="text-xs font-semibold text-slate-400 mb-2">📝 Your entry</p>
            <p className="text-sm text-slate-700 leading-relaxed">{result.text}</p>
          </div>

          {/* Emotion + sentiment row */}
          <div className="flex flex-wrap gap-3">
            {result.emotion && (
              <div className="bg-white rounded-2xl shadow-soft px-4 py-3 flex items-center gap-2">
                <span className="text-xs text-slate-400 font-medium">Emotion</span>
                <EmotionBadge emotion={result.emotion} />
              </div>
            )}
            {result.sentiment && (
              <div className="bg-white rounded-2xl shadow-soft px-4 py-3 flex items-center gap-2">
                <span className="text-xs text-slate-400 font-medium">Sentiment</span>
                <span className="text-xs font-semibold text-primary-600 bg-primary-50 px-2.5 py-1 rounded-full capitalize">{result.sentiment}</span>
              </div>
            )}
          </div>

          {/* AI response card */}
          <AIResponseCard aiResponse={entry?.ai_response} />
          {/* SUPPORT SECTION */}
          {result?.support && (
            <div className="bg-white rounded-2xl shadow-soft p-4 space-y-2">
              <h3 className="text-sm font-semibold text-slate-500">💡 Suggested Support</h3>
              <p className="text-sm text-slate-700">🧠 {result.support.tip}</p>
              <p className="text-sm text-slate-700">🌱 {result.support.activity}</p>
              {result.support.video && (
                <iframe
                className="w-full rounded-xl mt-2"
                height="200"
                src={result.support.video.replace("watch?v=", "embed/")}
                title="Support Video"
              />
            )}
          </div>
        )}
        {result?.helplines && (
          <div className="bg-rose-50 border border-rose-200 rounded-2xl p-4">
            <h3 className="text-sm font-semibold text-rose-600">
              🚨 Need immediate help?
              </h3>
              {result.helplines.map((h, i) => (
                <p key={i} className="text-sm text-rose-700">
                  📞 {h.name}: {h.number}
                </p>
              ))}
          </div>
        )}

          <button
            onClick={handleNew}
            className="w-full py-3 rounded-2xl border-2 border-dashed border-primary-200 text-primary-500 text-sm font-medium hover:bg-primary-50 transition-colors duration-200"
          >
            ✨ Write another entry
          </button>
        </div>
      )}

      {error && (
        <p className="text-sm text-rose-500 bg-rose-50 rounded-2xl px-4 py-3">{error}</p>
      )}
    </div>
  )
  
}
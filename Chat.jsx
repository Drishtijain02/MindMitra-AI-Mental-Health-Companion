import { useState, useRef, useEffect } from 'react'
import { sendChat } from '../api/client'
import Spinner from '../components/Spinner'

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex gap-3 animate-slide-up ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-xl shrink-0 flex items-center justify-center text-sm font-bold
        ${isUser
          ? 'bg-primary-500 text-white'
          : 'bg-gradient-to-br from-primary-400 to-lavender-300 text-white shadow'}`}>
        {isUser ? '👤' : '🧠'}
      </div>
      {/* Bubble */}
      <div className={`max-w-[75%] px-4 py-3 rounded-3xl text-sm leading-relaxed shadow-soft
        ${isUser
          ? 'bg-primary-500 text-white rounded-tr-sm'
          : 'bg-white text-slate-700 rounded-tl-sm border border-slate-50'}`}>
        {msg.content}
      </div>
    </div>
  )
}

export default function Chat() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: "Hi 👋 I'm MindMitra, your emotional support companion. How are you feeling today?" }
  ])
  const [input, setInput]     = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState(null)
  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSend = async () => {
    const txt = input.trim()
    if (!txt || loading) return

    const userMsg = { role: 'user', content: txt }
    const next = [...messages, userMsg]
    setMessages(next)
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const res = await sendChat(next.map(m => ({ role: m.role, content: m.content })))
      const { role, content } = res.data
      setMessages(prev => [...prev, { role: role || 'assistant', content }])
    } catch {
      setError('Could not reach the assistant. Please try again.')
      setMessages(prev => prev.slice(0, -1))
    } finally {
      setLoading(false)
      setTimeout(() => inputRef.current?.focus(), 50)
    }
  }

  const handleKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  return (
    <div className="animate-fade-in flex flex-col h-[calc(100vh-9rem)] md:h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="mb-4">
        <h1 className="text-2xl font-bold text-slate-800">Chat with MindMitra</h1>
        <p className="text-sm text-slate-400 mt-1">Your safe space to talk it out.</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin space-y-4 pr-1 pb-2">
        {messages.map((m, i) => <Message key={i} msg={m} />)}

        {loading && (
          <div className="flex gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-400 to-lavender-300 flex items-center justify-center text-sm shadow">🧠</div>
            <div className="bg-white border border-slate-50 rounded-3xl rounded-tl-sm px-4 py-3 shadow-soft flex items-center gap-2">
              <Spinner size="sm" />
              <span className="text-xs text-slate-400">Thinking…</span>
            </div>
          </div>
        )}

        {error && <p className="text-xs text-rose-500 bg-rose-50 rounded-xl px-3 py-2 text-center">{error}</p>}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="mt-3 bg-white rounded-3xl shadow-card border border-slate-100 flex items-end gap-2 px-4 py-3">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          rows={1}
          placeholder="Type a message… (Enter to send)"
          className="flex-1 resize-none outline-none text-sm text-slate-700 placeholder-slate-300 leading-relaxed max-h-28 overflow-y-auto scrollbar-thin"
          style={{ height: 'auto' }}
          onInput={e => { e.target.style.height = 'auto'; e.target.style.height = e.target.scrollHeight + 'px' }}
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="shrink-0 w-9 h-9 rounded-2xl bg-primary-500 hover:bg-primary-600 disabled:opacity-40 disabled:cursor-not-allowed text-white flex items-center justify-center transition-all duration-200 shadow"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4 rotate-90">
            <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.897 28.897 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
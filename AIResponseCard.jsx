export default function AIResponseCard({ aiResponse }) {
  if (!aiResponse) return null
  const { reply, supportive_response, suggestion, motivation, insight } = aiResponse

  const sections = [
  { icon: '💬', label: 'Response',   value: reply               },
  { icon: '🤗', label: 'Support',    value: supportive_response },
  { icon: '🧠', label: 'Insight',    value: insight             },   
  { icon: '💡', label: 'Suggestion', value: suggestion          },
  { icon: '🌟', label: 'Motivation', value: motivation          },
].filter(s => s.value)

  return (
    <div className="mt-4 rounded-3xl bg-gradient-to-br from-lavender-50 to-primary-50 border border-primary-100 shadow-soft p-5 animate-slide-up">
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary-400 to-lavender-300 flex items-center justify-center text-sm shadow">
          🧠
        </div>
        <span className="font-semibold text-primary-600 text-sm">MindMitra says</span>
      </div>
      <div className="space-y-3">
        {sections.map(({ icon, label, value }) => (
          <div key={label} className="bg-white/70 rounded-2xl px-4 py-3">
            <p className="text-xs font-semibold text-slate-400 mb-1">{icon} {label}</p>
            <p className="text-sm text-slate-700 leading-relaxed">{value}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

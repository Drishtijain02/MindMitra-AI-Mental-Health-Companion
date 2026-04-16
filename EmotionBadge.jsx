const emotionConfig = {
  happy:    { emoji: '😊', bg: 'bg-yellow-100',  text: 'text-yellow-700'  },
  sad:      { emoji: '😢', bg: 'bg-blue-100',    text: 'text-blue-700'    },
  anxious:  { emoji: '😰', bg: 'bg-orange-100',  text: 'text-orange-700'  },
  angry:    { emoji: '😠', bg: 'bg-red-100',     text: 'text-red-700'     },
  neutral:  { emoji: '😐', bg: 'bg-slate-100',   text: 'text-slate-600'   },
  grateful: { emoji: '🙏', bg: 'bg-green-100',   text: 'text-green-700'   },
  excited:  { emoji: '🎉', bg: 'bg-purple-100',  text: 'text-purple-700'  },
  stressed: { emoji: '😤', bg: 'bg-rose-100',    text: 'text-rose-700'    },
}

export default function EmotionBadge({ emotion }) {
  const key = (emotion || '').toLowerCase()
  const cfg = emotionConfig[key] || { emoji: '💭', bg: 'bg-primary-100', text: 'text-primary-600' }
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${cfg.bg} ${cfg.text}`}>
      {cfg.emoji} {emotion || 'Unknown'}
    </span>
  )
}
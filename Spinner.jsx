export default function Spinner({ size = 'md' }) {
  const s = size === 'sm' ? 'w-4 h-4 border-2' : 'w-8 h-8 border-3'
  return (
    <div className={`${s} rounded-full border-primary-200 border-t-primary-500 animate-spin inline-block`} />
  )
}
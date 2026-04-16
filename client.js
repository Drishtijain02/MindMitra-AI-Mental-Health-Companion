import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' },
})

export const saveEntry  = (text)     => api.post('/save_entry', { text })
export const getEntries = ()         => api.get('/entries')
export const sendChat   = (messages) => api.post('/chat', { messages })

export default api
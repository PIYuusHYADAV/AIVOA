const BASE = '/api'

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export const api = {
  extractFromText: (text, currentFields) =>
    fetch(`${BASE}/extract/text`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text, current_fields: currentFields }),
    }).then(handle),

  extractFromFile: (file, currentFields) => {
    const form = new FormData()
    form.append('file', file)
    if (currentFields) form.append('current_fields', JSON.stringify(currentFields))
    return fetch(`${BASE}/extract/file`, { method: 'POST', body: form }).then(handle)
  },

  chat: (message, currentFields, history) =>
    fetch(`${BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, current_fields: currentFields, history }),
    }).then(handle),

  saveComplaint: (payload) =>
    fetch(`${BASE}/complaints`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).then(handle),

  listComplaints: () => fetch(`${BASE}/complaints`).then(handle),
}

export async function sendChat(query) {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const resp = await fetch(`${baseUrl}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  })
  let data = null
  try {
    data = await resp.json()
  } catch {
    data = null
  }
  if (!resp.ok) {
    throw new Error(data?.detail || 'Không thể kết nối backend. Kiểm tra FastAPI server rồi thử lại.')
  }
  return data
}

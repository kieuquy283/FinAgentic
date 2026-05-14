import { useEffect, useMemo, useRef, useState } from 'react'
import { sendChat } from './api'

const STORAGE_KEY = 'finance-agentic-rag-chat-history'
const FALLBACK_TITLE = 'Đoạn chat mới'

const sampleQueries = [
  'FPT niêm yết ở sàn nào?',
  'Giá FPT 3 tháng gần đây thế nào?',
  'Tính RSI14 và SMA20 của FPT.',
  'Tin tức gần đây về HPG là tích cực hay tiêu cực?',
  'FPT có đáng theo dõi không? Nêu lý do và rủi ro.'
]

function MetaBadge({ label, value }) {
  return (
    <div className="meta-item">
      <span className="muted">{label}</span>
      <span className="badge">{value || 'N/A'}</span>
    </div>
  )
}

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function nowIso() {
  return new Date().toISOString()
}

function toTitle(query) {
  const text = String(query || '').trim()
  if (!text) return FALLBACK_TITLE
  return text.length > 64 ? `${text.slice(0, 61)}...` : text
}

function newThread() {
  const now = nowIso()
  return {
    id: makeId(),
    title: FALLBACK_TITLE,
    createdAt: now,
    updatedAt: now,
    messages: []
  }
}

function readThreads() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return [newThread()]
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed) || parsed.length === 0) return [newThread()]
    return parsed.map((t) => ({
      id: String(t.id || makeId()),
      title: String(t.title || FALLBACK_TITLE),
      createdAt: String(t.createdAt || nowIso()),
      updatedAt: String(t.updatedAt || nowIso()),
      messages: Array.isArray(t.messages) ? t.messages : []
    }))
  } catch {
    return [newThread()]
  }
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' })
  } catch {
    return ''
  }
}

export default function App() {
  const [chatThreads, setChatThreads] = useState(() => readThreads())
  const [activeChatId, setActiveChatId] = useState('')
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const chatScrollRef = useRef(null)

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(chatThreads))
    } catch {
      // ignore storage failures
    }
  }, [chatThreads])

  useEffect(() => {
    if (!activeChatId && chatThreads.length > 0) {
      setActiveChatId(chatThreads[0].id)
    }
  }, [activeChatId, chatThreads])

  useEffect(() => {
    const el = chatScrollRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [activeThread?.messages, loading, error])

  const activeThread = useMemo(
    () => chatThreads.find((t) => t.id === activeChatId) || chatThreads[0],
    [chatThreads, activeChatId]
  )

  const latestResponse = useMemo(() => {
    if (!activeThread) return null
    const assistant = [...activeThread.messages].reverse().find((m) => m.role === 'assistant' && m.responseMeta)
    return assistant?.responseMeta || null
  }, [activeThread])

  const setThreadMessages = (threadId, updater) => {
    setChatThreads((prev) =>
      prev.map((t) => (t.id === threadId ? { ...t, ...updater(t), updatedAt: nowIso() } : t))
    )
  }

  const createNewChat = () => {
    const t = newThread()
    setChatThreads((prev) => [t, ...prev])
    setActiveChatId(t.id)
    setQuery('')
    setError('')
  }

  const submit = async (raw) => {
    const clean = String(raw || '').trim()
    if (!clean || !activeThread) {
      setError('Vui lòng nhập câu hỏi trước khi gửi.')
      return
    }

    setLoading(true)
    setError('')

    const threadId = activeThread.id
    const userMessage = { role: 'user', content: clean }
    setThreadMessages(threadId, (t) => ({
      title: t.messages.length === 0 ? toTitle(clean) : t.title,
      messages: [...t.messages, userMessage]
    }))

    try {
      const data = await sendChat(clean)
      const assistantMessage = {
        role: 'assistant',
        content: data?.answer || 'N/A',
        responseMeta: data || null
      }
      setThreadMessages(threadId, (t) => ({
        messages: [...t.messages, assistantMessage]
      }))
      setQuery('')
    } catch (e) {
      setError(String(e?.message || 'Không thể kết nối backend. Kiểm tra FastAPI server rồi thử lại.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar panel">
        <h1 className="brand">Finance Agentic RAG</h1>
        <button type="button" className="new-chat-btn" onClick={createNewChat}>+ Đoạn chat mới</button>

        <h2 className="section-title">Lịch sử chat</h2>
        <div className="history-list" role="list">
          {chatThreads.map((t) => (
            <button
              key={t.id}
              type="button"
              role="listitem"
              className={`history-item ${t.id === activeThread?.id ? 'history-item-active' : ''}`}
              aria-current={t.id === activeThread?.id ? 'page' : undefined}
              onClick={() => {
                setActiveChatId(t.id)
                setError('')
              }}
            >
              <div className="history-title">{t.title || FALLBACK_TITLE}</div>
              <div className="history-time muted">{formatTime(t.updatedAt)}</div>
            </button>
          ))}
        </div>
      </aside>

      <main className="main panel chat-panel">
        <header className="topbar">
          <h2>Chat Workspace</h2>
          <span className="muted">Deep analysis dashboard</span>
        </header>

        <section ref={chatScrollRef} className="workspace chat-scroll-area" aria-live="polite">
          {activeThread?.messages?.length === 0 && !loading && !error && (
            <div className="empty-state">
              <p>Hỏi thử một câu về cổ phiếu Việt Nam.</p>
              <div className="sample-row">
                {sampleQueries.map((q) => (
                  <button key={q} type="button" className="sample-chip" onClick={() => submit(q)}>
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {error && <div className="error-card">{error}</div>}
          {loading && <div className="loading-card">Đang phân tích...</div>}

          {(activeThread?.messages || []).map((m, i) => (
            <article key={`${m.role}-${i}`} className={`bubble ${m.role === 'user' ? 'user-bubble' : 'assistant-bubble'}`}>
              <div className="bubble-label">{m.role === 'user' ? 'Bạn' : 'Trợ lý'}</div>
              <p className="answer">{m.content || 'N/A'}</p>
            </article>
          ))}
        </section>

        <div className="sample-strip-wrap">
          <div className="sample-strip">
            {sampleQueries.map((q) => (
              <button key={`strip-${q}`} type="button" className="sample-chip" onClick={() => submit(q)} disabled={loading}>
                {q}
              </button>
            ))}
          </div>
        </div>

        <form
          className="composer chat-composer"
          onSubmit={(e) => {
            e.preventDefault()
            submit(query)
          }}
        >
          <label htmlFor="query-input" className="sr-only">Nhập câu hỏi</label>
          <input
            id="query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Nhập câu hỏi về cổ phiếu Việt Nam..."
            disabled={loading}
          />
          <button type="submit" className="send-btn" disabled={loading || !query.trim()}>
            {loading ? 'Đang phân tích...' : 'Gửi'}
          </button>
        </form>
      </main>

      <aside className="details panel">
        <h2 className="section-title">Phản hồi</h2>
        <div className="details-scroll-area">
          <div className="meta-grid">
            <MetaBadge label="Ý định" value={latestResponse?.intent} />
            <MetaBadge label="Tuyến xử lý" value={latestResponse?.route} />
            <MetaBadge label="Độ tin cậy" value={latestResponse?.confidence} />
            <MetaBadge label="Độ trễ" value={typeof latestResponse?.latency_ms === 'number' ? `${latestResponse.latency_ms} ms` : 'N/A'} />
          </div>

          <h3 className="section-title">Nguồn bằng chứng</h3>
          <div className="stack">
            {!latestResponse?.evidence?.length && <div className="empty-mini">Chưa có bằng chứng cho câu trả lời này.</div>}
            {(latestResponse?.evidence || []).map((e, i) => (
              <div className="evidence-item" key={`${e.source}-${i}`}>
                <div className="evidence-head">
                  <span className="badge">{e.source_type || 'N/A'}</span>
                  <span className="muted">{e.ticker || 'N/A'} • {e.date || 'N/A'}</span>
                </div>
                <div className="evidence-source">{e.source || 'N/A'}</div>
                <div>{e.content || 'N/A'}</div>
              </div>
            ))}
          </div>

          <h3 className="section-title">Guardrails</h3>
          <div className={`guardrail ${latestResponse?.guardrails?.passed === false ? 'guardrail-warn' : ''}`}>
            <MetaBadge label="Trạng thái" value={latestResponse?.guardrails?.passed === false ? 'warning' : 'passed'} />
            <div className="stack">
              {(latestResponse?.guardrails?.warnings || []).length === 0 && <div className="empty-mini">Không có cảnh báo.</div>}
              {(latestResponse?.guardrails?.warnings || []).map((w, i) => (
                <div key={i} className="warning-item">• {w}</div>
              ))}
            </div>
            <div className="disclaimer">{latestResponse?.guardrails?.disclaimer || 'N/A'}</div>
          </div>
        </div>
      </aside>
    </div>
  )
}


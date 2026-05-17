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

function statusLabel(status) {
  if (status === 'loading') return 'Đang xử lý'
  if (status === 'error') return 'Lỗi'
  return 'Thành công'
}

function newThread() {
  const now = nowIso()
  return {
    id: makeId(),
    title: FALLBACK_TITLE,
    createdAt: now,
    updatedAt: now,
    pairs: [],
    selectedPairId: null
  }
}

function pairFromMessages(messages) {
  const pairs = []
  let pendingQuestion = null
  for (const m of messages) {
    if (m?.role === 'user') {
      if (pendingQuestion) {
        pairs.push({
          id: makeId(),
          question: pendingQuestion,
          answer: '',
          status: 'success',
          errorMessage: '',
          response: null,
          createdAt: nowIso(),
          updatedAt: nowIso()
        })
      }
      pendingQuestion = String(m.content || '')
    } else if (m?.role === 'assistant') {
      if (!pendingQuestion) continue
      pairs.push({
        id: makeId(),
        question: pendingQuestion,
        answer: String(m.content || ''),
        status: 'success',
        errorMessage: '',
        response: m.responseMeta || null,
        createdAt: nowIso(),
        updatedAt: nowIso()
      })
      pendingQuestion = null
    }
  }
  if (pendingQuestion) {
    pairs.push({
      id: makeId(),
      question: pendingQuestion,
      answer: '',
      status: 'success',
      errorMessage: '',
      response: null,
      createdAt: nowIso(),
      updatedAt: nowIso()
    })
  }
  return pairs
}

function migrateThread(rawThread) {
  const now = nowIso()
  const id = String(rawThread?.id || makeId())
  let pairs = []

  if (Array.isArray(rawThread?.pairs)) {
    pairs = rawThread.pairs.map((p) => ({
      id: String(p?.id || makeId()),
      question: String(p?.question || ''),
      answer: String(p?.answer || ''),
      status: p?.status === 'loading' || p?.status === 'error' || p?.status === 'success' ? p.status : 'success',
      errorMessage: String(p?.errorMessage || ''),
      response: p?.response || null,
      createdAt: String(p?.createdAt || now),
      updatedAt: String(p?.updatedAt || now)
    }))
  } else if (Array.isArray(rawThread?.messages)) {
    pairs = pairFromMessages(rawThread.messages)
  }

  const selectedPairId = pairs.find((p) => p.id === rawThread?.selectedPairId)?.id || pairs[0]?.id || null

  return {
    id,
    title: String(rawThread?.title || FALLBACK_TITLE),
    createdAt: String(rawThread?.createdAt || now),
    updatedAt: String(rawThread?.updatedAt || now),
    pairs,
    selectedPairId
  }
}

function readThreads() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return [newThread()]
    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed) || parsed.length === 0) return [newThread()]
    const migrated = parsed.map(migrateThread)
    return migrated.length ? migrated : [newThread()]
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
  const [submitting, setSubmitting] = useState(false)
  const [inputError, setInputError] = useState('')
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

  const activeThread = useMemo(
    () => chatThreads.find((t) => t.id === activeChatId) || chatThreads[0],
    [chatThreads, activeChatId]
  )

  const selectedPair = useMemo(() => {
    if (!activeThread) return null
    return activeThread.pairs.find((p) => p.id === activeThread.selectedPairId) || activeThread.pairs[0] || null
  }, [activeThread])

  useEffect(() => {
    const el = chatScrollRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [activeThread, submitting, inputError])

  const updateThread = (threadId, updater) => {
    setChatThreads((prev) => prev.map((t) => (t.id === threadId ? { ...t, ...updater(t), updatedAt: nowIso() } : t)))
  }

  const selectPair = (pairId) => {
    if (!activeThread) return
    updateThread(activeThread.id, (t) => ({ selectedPairId: pairId }))
  }

  const createNewChat = () => {
    const t = newThread()
    setChatThreads((prev) => [t, ...prev])
    setActiveChatId(t.id)
    setQuery('')
    setInputError('')
  }

  const submit = async (raw) => {
    const clean = String(raw || '').trim()
    if (!clean || !activeThread) {
      setInputError('Vui lòng nhập câu hỏi trước khi gửi.')
      return
    }

    setSubmitting(true)
    setInputError('')

    const pairId = makeId()
    const startedAt = nowIso()

    updateThread(activeThread.id, (t) => ({
      title: t.pairs.length === 0 ? toTitle(clean) : t.title,
      selectedPairId: pairId,
      pairs: [
        ...t.pairs,
        {
          id: pairId,
          question: clean,
          answer: '',
          status: 'loading',
          errorMessage: '',
          response: null,
          createdAt: startedAt,
          updatedAt: startedAt
        }
      ]
    }))

    try {
      const data = await sendChat(clean)
      updateThread(activeThread.id, (t) => ({
        pairs: t.pairs.map((p) =>
          p.id === pairId
            ? {
                ...p,
                status: 'success',
                answer: String(data?.answer || ''),
                response: data || null,
                errorMessage: '',
                updatedAt: nowIso()
              }
            : p
        )
      }))
      setQuery('')
    } catch (e) {
      const msg = String(e?.message || 'Không thể kết nối backend. Kiểm tra FastAPI server rồi thử lại.')
      updateThread(activeThread.id, (t) => ({
        pairs: t.pairs.map((p) =>
          p.id === pairId
            ? {
                ...p,
                status: 'error',
                errorMessage: msg,
                updatedAt: nowIso()
              }
            : p
        )
      }))
    } finally {
      setSubmitting(false)
    }
  }

  const currentResponse = selectedPair?.response || null

  return (
    <div className="app-shell">
      <aside className="sidebar panel">
        <h1 className="brand">FinAgentic</h1>
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
                setInputError('')
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
          {activeThread?.pairs?.length === 0 && !submitting && !inputError && (
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

          {inputError && <div className="error-card">{inputError}</div>}

          {(activeThread?.pairs || []).map((pair) => {
            const isSelected = pair.id === activeThread?.selectedPairId
            return (
              <div key={pair.id} className={`pair-block ${isSelected ? 'pair-block-selected' : ''}`}>
                <button
                  type="button"
                  className={`bubble user-bubble qa-button ${isSelected ? 'qa-selected' : ''}`}
                  aria-selected={isSelected}
                  onClick={() => selectPair(pair.id)}
                >
                  <div className="bubble-label">Bạn</div>
                  <p className="answer">{pair.question || 'N/A'}</p>
                </button>

                <button
                  type="button"
                  className={`bubble assistant-bubble qa-button ${isSelected ? 'qa-selected' : ''}`}
                  aria-selected={isSelected}
                  onClick={() => selectPair(pair.id)}
                >
                  <div className="bubble-label">Trợ lý</div>
                  <div className="pair-head-row">
                    <span className={`pair-status pair-status-${pair.status}`}>{statusLabel(pair.status)}</span>
                  </div>
                  <p className="answer">{pair.answer || (pair.status === 'loading' ? 'Đang phân tích...' : pair.status === 'error' ? pair.errorMessage : 'N/A')}</p>
                </button>
              </div>
            )
          })}
        </section>

        <div className="sample-strip-wrap">
          <div className="sample-strip">
            {sampleQueries.map((q) => (
              <button key={`strip-${q}`} type="button" className="sample-chip" onClick={() => submit(q)} disabled={submitting}>
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
            disabled={submitting}
          />
          <button type="submit" className="send-btn" disabled={submitting || !query.trim()}>
            {submitting ? 'Đang phân tích...' : 'Gửi'}
          </button>
        </form>
      </main>

      <aside className="details panel">
        <h2 className="section-title">Phản hồi của câu hỏi đang chọn</h2>
        <div className="details-scroll-area">
          {!selectedPair && <div className="empty-mini">Chọn một câu hỏi hoặc câu trả lời để xem phản hồi.</div>}

          {selectedPair && (
            <>
              <div className="meta-grid">
                <MetaBadge label="Trạng thái" value={statusLabel(selectedPair.status)} />
                <MetaBadge label="Ý định" value={currentResponse?.intent} />
                <MetaBadge label="Tuyến xử lý" value={currentResponse?.route} />
                <MetaBadge label="Độ tin cậy" value={currentResponse?.confidence} />
                <MetaBadge label="Độ trễ" value={typeof currentResponse?.latency_ms === 'number' ? `${currentResponse.latency_ms} ms` : 'N/A'} />
              </div>

              {selectedPair.status === 'loading' && <div className="loading-card">Đang xử lý phản hồi cho câu hỏi này...</div>}
              {selectedPair.status === 'error' && <div className="error-card">{selectedPair.errorMessage || 'Lỗi không xác định.'}</div>}

              <h3 className="section-title">Nguồn bằng chứng</h3>
              <div className="stack">
                {!currentResponse?.evidence?.length && <div className="empty-mini">Chưa có bằng chứng cho câu trả lời này.</div>}
                {(currentResponse?.evidence || []).map((e, i) => (
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
              <div className={`guardrail ${currentResponse?.guardrails?.passed === false ? 'guardrail-warn' : ''}`}>
                <MetaBadge label="Trạng thái" value={currentResponse?.guardrails?.passed === false ? 'warning' : 'passed'} />
                <div className="stack">
                  {(currentResponse?.guardrails?.warnings || []).length === 0 && <div className="empty-mini">Không có cảnh báo.</div>}
                  {(currentResponse?.guardrails?.warnings || []).map((w, i) => (
                    <div key={i} className="warning-item">• {w}</div>
                  ))}
                </div>
                <div className="disclaimer">{currentResponse?.guardrails?.disclaimer || 'N/A'}</div>
              </div>
            </>
          )}
        </div>
      </aside>
    </div>
  )
}

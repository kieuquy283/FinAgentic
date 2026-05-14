import { useState } from 'react'
import { sendChat } from './api'

const samples = [
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

export default function App() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async (raw) => {
    const clean = String(raw || '').trim()
    if (!clean) {
      setError('Vui lòng nhập câu hỏi trước khi gửi.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const data = await sendChat(clean)
      setResult(data)
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
        <p className="subtitle">Vietnamese stock analysis assistant</p>
        <div className="status-row">
          <span className={`badge ${loading ? 'badge-info' : 'badge-ok'}`}>{loading ? 'Đang phân tích...' : 'Sẵn sàng'}</span>
        </div>
        <h2 className="section-title">Câu hỏi mẫu</h2>
        <div className="samples">
          {samples.map((q) => (
            <button key={q} className="demo-btn" onClick={() => submit(q)} disabled={loading}>
              {q}
            </button>
          ))}
        </div>
      </aside>

      <main className="main panel">
        <header className="topbar">
          <h2>Chat Workspace</h2>
          <span className="muted">Deep analysis dashboard</span>
        </header>

        <section className="workspace" aria-live="polite">
          {!result && !loading && !error && (
            <div className="empty-state">
              <p>Hỏi thử một câu về cổ phiếu Việt Nam.</p>
              <p className="muted">Ví dụ: Tính RSI14 và SMA20 của FPT.</p>
            </div>
          )}

          {error && <div className="error-card">{error}</div>}
          {loading && <div className="loading-card">Đang phân tích...</div>}

          {result && (
            <>
              <div className="bubble user-bubble">
                <div className="bubble-label">Bạn</div>
                <div>{result.query || query || 'N/A'}</div>
              </div>

              <article className="bubble assistant-bubble">
                <div className="bubble-label">Trợ lý</div>
                <p className="answer">{result.answer || 'N/A'}</p>
              </article>
            </>
          )}
        </section>

        <form
          className="composer"
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
        <div className="meta-grid">
          <MetaBadge label="Ý định" value={result?.intent} />
          <MetaBadge label="Tuyến xử lý" value={result?.route} />
          <MetaBadge label="Độ tin cậy" value={result?.confidence} />
          <MetaBadge label="Độ trễ" value={typeof result?.latency_ms === 'number' ? `${result.latency_ms} ms` : 'N/A'} />
        </div>

        <h3 className="section-title">Nguồn bằng chứng</h3>
        <div className="stack">
          {!result?.evidence?.length && <div className="empty-mini">Chưa có bằng chứng cho câu trả lời này.</div>}
          {(result?.evidence || []).map((e, i) => (
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
        <div className={`guardrail ${result?.guardrails?.passed === false ? 'guardrail-warn' : ''}`}>
          <MetaBadge label="Trạng thái" value={result?.guardrails?.passed === false ? 'warning' : 'passed'} />
          <div className="stack">
            {(result?.guardrails?.warnings || []).length === 0 && <div className="empty-mini">Không có cảnh báo.</div>}
            {(result?.guardrails?.warnings || []).map((w, i) => (
              <div key={i} className="warning-item">• {w}</div>
            ))}
          </div>
          <div className="disclaimer">{result?.guardrails?.disclaimer || 'N/A'}</div>
        </div>
      </aside>
    </div>
  )
}

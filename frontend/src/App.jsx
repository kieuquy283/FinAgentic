import { useState } from 'react'
import { sendChat } from './api'

const samples = [
  'FPT niem yet o san nao?',
  'Gia FPT 3 thang gan day the nao?',
  'Tinh RSI14 va SMA20 cua FPT.',
  'Tin tuc gan day ve HPG la tich cuc hay tieu cuc?',
  'FPT co dang theo doi khong? Neu ly do va rui ro.'
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
      setError('Vui long nhap cau hoi truoc khi gui.')
      return
    }

    setLoading(true)
    setError('')
    try {
      const data = await sendChat(clean)
      setResult(data)
    } catch (e) {
      setError(String(e?.message || 'Khong the ket noi backend. Kiem tra FastAPI server roi thu lai.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar panel">
        <h1 className="brand">FinAgentic</h1>
        <p className="subtitle">Vietnamese stock analysis assistant</p>
        <div className="status-row">
          <span className={`badge ${loading ? 'badge-info' : 'badge-ok'}`}>{loading ? 'Dang phan tich...' : 'San sang'}</span>
        </div>
        <h2 className="section-title">Cau hoi mau</h2>
        <div className="samples">
          {samples.map((q) => (
            <button key={q} className="demo-btn" onClick={() => submit(q)} disabled={loading}>
              {q}
            </button>
          ))}
        </div>
      </aside>

      <main className="main panel chat-panel">
        <header className="topbar">
          <h2>Chat Workspace</h2>
          <span className="muted">Deep analysis dashboard</span>
        </header>

        <section className="workspace chat-scroll-area" aria-live="polite">
          {!result && !loading && !error && (
            <div className="empty-state">
              <p>Hoi thu mot cau ve co phieu Viet Nam.</p>
              <p className="muted">Vi du: Tinh RSI14 va SMA20 cua FPT.</p>
            </div>
          )}

          {error && <div className="error-card">{error}</div>}
          {loading && <div className="loading-card">Dang phan tich...</div>}

          {result && (
            <>
              <div className="bubble user-bubble">
                <div className="bubble-label">Ban</div>
                <div>{result.query || query || 'N/A'}</div>
              </div>

              <article className="bubble assistant-bubble">
                <div className="bubble-label">Tro ly</div>
                <p className="answer">{result.answer || 'N/A'}</p>
              </article>
            </>
          )}
        </section>

        <form
          className="composer chat-composer"
          onSubmit={(e) => {
            e.preventDefault()
            submit(query)
          }}
        >
          <label htmlFor="query-input" className="sr-only">Nhap cau hoi</label>
          <input
            id="query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Nhap cau hoi ve co phieu Viet Nam..."
            disabled={loading}
          />
          <button type="submit" className="send-btn" disabled={loading || !query.trim()}>
            {loading ? 'Dang phan tich...' : 'Gui'}
          </button>
        </form>
      </main>

      <aside className="details panel">
        <h2 className="section-title">Phan hoi</h2>
        <div className="details-scroll-area">
          <div className="meta-grid">
            <MetaBadge label="Y dinh" value={result?.intent} />
            <MetaBadge label="Tuyen xu ly" value={result?.route} />
            <MetaBadge label="Do tin cay" value={result?.confidence} />
            <MetaBadge label="Do tre" value={typeof result?.latency_ms === 'number' ? `${result.latency_ms} ms` : 'N/A'} />
          </div>

          <h3 className="section-title">Nguon bang chung</h3>
          <div className="stack">
            {!result?.evidence?.length && <div className="empty-mini">Chua co bang chung cho cau tra loi nay.</div>}
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
            <MetaBadge label="Trang thai" value={result?.guardrails?.passed === false ? 'warning' : 'passed'} />
            <div className="stack">
              {(result?.guardrails?.warnings || []).length === 0 && <div className="empty-mini">Khong co canh bao.</div>}
              {(result?.guardrails?.warnings || []).map((w, i) => (
                <div key={i} className="warning-item">• {w}</div>
              ))}
            </div>
            <div className="disclaimer">{result?.guardrails?.disclaimer || 'N/A'}</div>
          </div>
        </div>
      </aside>
    </div>
  )
}

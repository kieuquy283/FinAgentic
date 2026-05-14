---
name: finance-agentic-rag-chat-ui
description: Creates and updates the frontend for a Vietnamese financial assistant chat app using a DeepSeek-like dark, structured, accessible dashboard style. Use when Codex implements or refactors the React/Vite frontend.
---

# Finance Agentic RAG Chat UI Skill

## Mission

Implement a polished DeepSeek-like chat interface for the Hybrid Agentic RAG Vietnamese stock investment assistant.

The interface must help users clearly see:

- the chat answer,
- the detected intent,
- the selected route,
- confidence,
- evidence,
- guardrail warnings,
- demo/mock-data disclaimer,
- the five required demo queries.

This is a frontend implementation skill for Codex. It must be read together with:

```txt
ARCHITECTURE.md
CODEX_TASKS.md
FRONTEND_DESIGN.md
README.md
```

## Product Context

- Product: Vietnamese stock investment assistant.
- User: authenticated or demo user exploring market/company questions.
- Surface: dashboard-style web app.
- Core workflow: user asks a Vietnamese stock question, app calls `/chat`, response is rendered with answer, metadata, evidence, and guardrails.
- Design reference: DeepSeek-like dark chat dashboard, but branded for the finance assistant.

The uploaded DeepSeek reference emphasizes tokenized UI guidance, accessibility, keyboard-first behavior, focus-visible rules, and consistent component states. This project should preserve those principles while adapting the interface to financial analysis.

## Frontend Stack

Use the existing MVP frontend stack:

```txt
React
Vite
Plain CSS or CSS modules
No heavy UI framework unless already installed
No Tailwind migration unless explicitly requested
```

Preferred files:

```txt
frontend/src/App.jsx
frontend/src/main.jsx
frontend/src/api.js
frontend/src/styles.css
frontend/src/components/
```

If components do not exist yet, Codex may create:

```txt
frontend/src/components/AppShell.jsx
frontend/src/components/ChatPanel.jsx
frontend/src/components/MessageBubble.jsx
frontend/src/components/DemoQueryBar.jsx
frontend/src/components/ResponseMeta.jsx
frontend/src/components/EvidencePanel.jsx
frontend/src/components/GuardrailPanel.jsx
frontend/src/components/StatusBadge.jsx
frontend/src/components/EmptyState.jsx
frontend/src/components/LoadingState.jsx
frontend/src/components/ErrorState.jsx
```

Keep the implementation simple and maintainable.

## Non-negotiable Architecture Rules

The frontend must not change backend architecture.

The frontend must not:

- calculate financial indicators,
- fabricate evidence,
- hide guardrail warnings,
- remove the financial disclaimer,
- call external financial APIs directly,
- bypass the backend `/chat` endpoint,
- hardcode fake answers when backend is available.

The frontend may:

- display fallback UI when backend fails,
- show loading/error states,
- improve layout and styling,
- add demo query buttons,
- render response metadata,
- render evidence and guardrails.

## Required User Experience

The app must provide:

1. A dark dashboard chat interface.
2. A centered chat workspace.
3. A left sidebar or top section with product identity and demo actions.
4. Five required demo query buttons.
5. A text input with send button.
6. Loading state while waiting for `/chat`.
7. Error state if backend request fails.
8. Rendered answer in Vietnamese.
9. Intent/route/confidence metadata.
10. Evidence panel.
11. Guardrail warning panel.
12. Disclaimer visible on advisory outputs.
13. Empty state explaining what the user can ask.
14. Responsive layout for desktop and mobile.

## Required Demo Query Buttons

The frontend must include clickable buttons for:

```txt
FPT niêm yết ở sàn nào?
Giá FPT 3 tháng gần đây thế nào?
Tính RSI14 và SMA20 của FPT.
Tin tức gần đây về HPG là tích cực hay tiêu cực?
FPT có đáng theo dõi không? Nêu lý do và rủi ro.
```

Clicking a button must submit the query to the backend.

## API Contract

The frontend must call:

```txt
POST /chat
```

Expected request:

```json
{
  "query": "string"
}
```

Expected response:

```json
{
  "query": "string",
  "intent": "string",
  "route": "direct | analytics | rag | advisory | unknown",
  "answer": "string",
  "evidence": [
    {
      "source": "string",
      "source_type": "db | analytics | rag | cache",
      "ticker": "string",
      "date": "string",
      "content": "string"
    }
  ],
  "confidence": "high | medium | low",
  "guardrails": {
    "passed": true,
    "warnings": ["string"],
    "disclaimer": "string"
  },
  "latency_ms": 0
}
```

The UI must handle missing optional fields gracefully.

## Visual Design Intent

Create a DeepSeek-like interface:

- black/dark base,
- low-contrast but readable slate text,
- compact density,
- rounded controls,
- blue primary action,
- structured panels,
- minimal visual noise,
- evidence and warnings clearly separated,
- responsive chat layout.

Do not copy brand names or external assets. Use this project’s product identity.

Suggested product title:

```txt
Finance Agentic RAG
```

Suggested subtitle:

```txt
Vietnamese stock analysis assistant
```

## Component Requirements

Every interactive component must define and implement these states:

```txt
default
hover
focus-visible
active
disabled
loading
error
```

At minimum, this applies to:

- send button,
- query buttons,
- input textarea,
- evidence expand/collapse if implemented,
- retry button if implemented.

## Accessibility Requirements

Target WCAG 2.2 AA.

The UI must:

- use semantic HTML where possible,
- support keyboard navigation,
- provide visible focus indicators,
- keep sufficient contrast,
- associate labels with inputs,
- avoid color-only meaning,
- provide loading text for screen readers,
- not trap focus,
- make buttons descriptive.

Testable acceptance criteria:

1. User can tab to every interactive element.
2. Focus state is visible on every interactive element.
3. Enter or button click can submit the query.
4. Loading state is announced visually and textually.
5. Error state contains readable recovery guidance.
6. Guardrail warnings are visible and not hidden behind hover-only UI.
7. Evidence content is readable at desktop and mobile widths.

## Content Tone

Tone must be:

```txt
concise
confident
implementation-focused
transparent about uncertainty
```

Use Vietnamese UI text by default.

Examples:

```txt
Đang phân tích...
Không thể kết nối backend. Kiểm tra FastAPI server rồi thử lại.
Dữ liệu demo/mock: chỉ dùng để kiểm thử kiến trúc.
Nguồn bằng chứng
Cảnh báo guardrails
Độ tin cậy
Tuyến xử lý
```

Avoid:

```txt
Chắc chắn mua
Cam kết lợi nhuận
Tín hiệu thắng 100%
Không có rủi ro
```

## Layout Guidance

Desktop:

```txt
App shell
  Left sidebar / header zone
    product name
    demo query buttons
    system status
  Main chat area
    message history / response area
    input composer
  Right or lower details area
    metadata
    evidence
    guardrails
```

Mobile:

```txt
Single-column layout
  product header
  demo buttons horizontally scrollable or stacked
  chat area
  metadata/evidence/guardrails below answer
  sticky input composer if practical
```

## Implementation Workflow for Codex

When applying this skill:

1. Read `FRONTEND_DESIGN.md`.
2. Inspect current frontend implementation.
3. Preserve API compatibility.
4. Refactor into small components if helpful.
5. Apply design tokens using CSS variables.
6. Add robust loading/error/empty states.
7. Ensure all five demo query buttons work.
8. Run frontend build.
9. If possible, run backend and manually test all five queries.
10. Update README or docs if startup behavior changes.

## Quality Gates

Codex must verify:

```txt
npm install
npm run build
```

If backend is available, Codex should also verify:

```txt
POST /chat for all 5 demo queries
```

Final UI must not be marked done unless:

- build passes,
- app renders without console-breaking errors,
- all demo buttons are wired,
- response metadata is visible,
- evidence is visible,
- guardrail warnings/disclaimer are visible,
- mobile layout is usable.

## Anti-patterns

Do not implement:

- light theme only,
- hidden evidence,
- hidden disclaimer,
- raw JSON dump as the main UI,
- inaccessible icon-only buttons,
- tiny unreadable text,
- one-off colors outside tokens,
- fake frontend-only answers,
- external API calls from frontend,
- excessive animation,
- overbuilt dashboard unrelated to the chat demo.

## Final Codex Prompt Snippet

Use this when instructing Codex:

```txt
Read FRONTEND_SKILL.md and FRONTEND_DESIGN.md.

Refactor the existing React/Vite frontend to match the DeepSeek-like dark chat dashboard design specified there.

Do not change backend behavior.
Do not add new product features.
Focus on UI implementation, accessibility, response rendering, demo query buttons, evidence display, guardrail display, loading/error states, and frontend build stability.

Run npm install and npm run build.
Fix all frontend issues before marking complete.
```

# FRONTEND_DESIGN.md

# Finance Agentic RAG Chat UI Design System

## 1. Context and Goals

This document defines the frontend design system for the Vietnamese stock investment assistant.

The target UI is a DeepSeek-like dark chat dashboard adapted for financial analysis. The interface should be structured, compact, accessible, and implementation-ready.

Reference design principles from the uploaded DeepSeek files include:

- token-driven UI guidance,
- Arial-based compact typography,
- dark surface palette,
- blue primary action color,
- explicit component states,
- keyboard-first interactions,
- visible focus indicators,
- testable accessibility criteria.

This project adapts those principles to the Finance Agentic RAG assistant.

## 2. Design Intent

Build a dark, focused financial assistant interface where the answer, route, confidence, evidence, and guardrails are immediately understandable.

The UI should feel:

```txt
dark
compact
technical
trustworthy
evidence-first
accessible
demo-ready
```

## 3. Brand

```txt
Product name: Finance Agentic RAG
Short label: Finance RAG
Surface: dashboard chat app
Audience: Vietnamese stock market users, students, builders, analysts
Tone: concise, transparent, evidence-driven
```

Do not use the DeepSeek brand name or logo in the app UI.

## 4. Design Tokens

Codex should implement these as CSS variables.

### 4.1 Font Tokens

```css
--font-family-primary: Arial, Helvetica, sans-serif;
--font-size-xs: 12px;
--font-size-sm: 13.33px;
--font-size-md: 14px;
--font-size-lg: 15px;
--font-size-xl: 18px;
--font-weight-base: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--line-height-base: 1.45;
--line-height-tight: 1.2;
```

### 4.2 Color Tokens

Dark base palette:

```css
--color-surface-base: #000000;
--color-surface-raised: #0f0f0f;
--color-surface-muted: #252525;
--color-surface-subtle: #171717;
--color-surface-hover: #1f1f1f;
--color-surface-active: #2a2a2a;

--color-border-muted: #2a2a2a;
--color-border-strong: #3a3a3a;

--color-text-primary: #f1f5f9;
--color-text-secondary: #cbd5e1;
--color-text-muted: #94a3b8;
--color-text-inverse: #ffffff;

--color-primary: #4d6bfe;
--color-primary-hover: #5c78ff;
--color-primary-active: #3f5bea;
--color-primary-soft: rgba(77, 107, 254, 0.14);

--color-success: #22c55e;
--color-warning: #f59e0b;
--color-danger: #ef4444;
--color-info: #38bdf8;
```

### 4.3 Spacing Tokens

```css
--space-1: 6px;
--space-2: 8px;
--space-3: 10px;
--space-4: 11px;
--space-5: 12px;
--space-6: 18px;
--space-7: 24px;
--space-8: 32px;
```

### 4.4 Radius Tokens

```css
--radius-xs: 8px;
--radius-sm: 12px;
--radius-md: 18px;
--radius-lg: 24px;
--radius-pill: 999px;
```

### 4.5 Shadow Tokens

```css
--shadow-primary: 0 2px 8px rgba(77, 107, 254, 0.3);
--shadow-soft: 0 12px 40px rgba(0, 0, 0, 0.35);
--shadow-panel: 0 0 0 1px rgba(255, 255, 255, 0.03);
```

### 4.6 Motion Tokens

```css
--motion-duration-instant: 150ms;
--motion-duration-fast: 200ms;
--motion-ease-standard: ease;
```

## 5. App Layout

### 5.1 Desktop Layout

The app should use a dashboard chat shell.

```txt
.app-shell
  .sidebar
    product identity
    demo query buttons
    status card
  .main
    top bar
    chat workspace
    composer
  .details-panel
    response metadata
    evidence
    guardrails
```

If a right-side details panel is too much for the MVP, render metadata/evidence/guardrails below the answer in the main area.

Recommended desktop dimensions:

```css
.app-shell {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
}
```

Optional details panel:

```css
@media (min-width: 1200px) {
  .chat-layout {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 360px;
  }
}
```

### 5.2 Mobile Layout

At widths below `768px`:

```txt
single column
top header
demo buttons in scroll row or stacked grid
chat response
details sections
composer
```

Rules:

- Sidebar must collapse above the main chat.
- Demo buttons must remain accessible.
- Composer must remain easy to reach.
- Evidence must not overflow horizontally.

## 6. Component Rules

## 6.1 App Shell

Purpose:
Provide a stable dashboard frame.

Anatomy:

```txt
AppShell
  Sidebar/Header
  Main Chat Area
  Details Sections
```

States:
- default: dark base background.
- loading: main area shows loading indicator after submit.
- error: error banner appears in chat area.
- empty: empty state appears before first query.

Rules:
- Must use `--color-surface-base` as global background.
- Must use `--font-family-primary`.
- Must keep content readable at 320px width.
- Must not hide evidence or guardrails on small screens.

## 6.2 Sidebar / Demo Query Panel

Purpose:
Expose product identity and required demo queries.

Required content:

```txt
Finance Agentic RAG
Vietnamese stock analysis assistant
5 demo query buttons
Backend status if implemented
```

Demo buttons:
- must be keyboard-focusable,
- must call the same submit handler as text input,
- must show hover/focus states,
- should wrap on small screens.

Button labels:

```txt
FPT niêm yết ở sàn nào?
Giá FPT 3 tháng gần đây thế nào?
Tính RSI14 và SMA20 của FPT.
Tin tức gần đây về HPG là tích cực hay tiêu cực?
FPT có đáng theo dõi không? Nêu lý do và rủi ro.
```

## 6.3 Chat Workspace

Purpose:
Show the latest query and response in a readable chat format.

Anatomy:

```txt
User message
Assistant answer card
Response meta row
Evidence section
Guardrail section
```

Rules:
- User query should be visually distinct from assistant answer.
- Assistant answer must support multiline Vietnamese text.
- Long text must wrap.
- Do not render the entire raw JSON as the primary answer.
- Raw response may be shown only in a developer/debug section if implemented.

## 6.4 Message Bubble

Variants:

```txt
user
assistant
system/error
```

User bubble:
- right or compact aligned,
- surface muted,
- text primary.

Assistant bubble:
- left or full-width card,
- raised surface,
- answer text first,
- metadata second.

Error bubble:
- danger border or warning color,
- clear recovery text.

States:
- default,
- loading,
- error.

## 6.5 Query Composer

Purpose:
Allow the user to type and submit a question.

Anatomy:

```txt
textarea/input
send button
optional keyboard hint
```

Behavior:
- Enter should submit when using single-line input.
- If textarea is multiline, Ctrl+Enter or button should submit.
- Empty or whitespace-only query must not submit.
- During loading, input can remain editable but send button should be disabled.
- Must show focus-visible state.

Recommended labels:

```txt
Nhập câu hỏi về cổ phiếu Việt Nam...
Gửi
Đang phân tích...
```

## 6.6 Primary Button

Use for send action.

States:
- default: `--color-primary`
- hover: `--color-primary-hover`
- active: `--color-primary-active`
- focus-visible: outline with primary color
- disabled: reduced opacity, no pointer action
- loading: disabled with loading label

Must be at least 40px high on touch devices.

## 6.7 Demo Query Button

Use for sample queries.

States:
- default: muted/raised surface
- hover: surface hover
- active: surface active
- focus-visible: visible primary outline
- disabled/loading: reduced opacity

Rules:
- Must support long Vietnamese text.
- Must wrap cleanly.
- Must not truncate essential ticker/question content.

## 6.8 Status Badge

Use for intent, route, confidence, guardrail status.

Variants:

```txt
intent
route
confidence-high
confidence-medium
confidence-low
guardrail-pass
guardrail-warning
source-type
```

Rules:
- Must not rely on color only.
- Must include text label.
- Should use compact pill radius.

Examples:

```txt
Intent: technical_analysis
Route: analytics
Confidence: high
Guardrails: passed
Source: analytics
```

## 6.9 Response Metadata Panel

Purpose:
Show response contract metadata.

Required fields:
- intent,
- route,
- confidence,
- latency if available.

Rules:
- Must be visible for every response.
- Unknown/missing values must show `N/A`, not crash.
- Should use compact badges.

## 6.10 Evidence Panel

Purpose:
Show why the answer was generated.

Anatomy:

```txt
section title: Nguồn bằng chứng
evidence item cards
source
source_type
ticker
date
content
```

Rules:
- Must render all evidence items returned by backend.
- If evidence is empty, show an empty state: `Chưa có bằng chứng cho câu trả lời này.`
- Evidence content must wrap.
- Source type should be shown as badge.
- Cache evidence should be visually marked but not overemphasized.
- Do not hide evidence by default in demo mode.

## 6.11 Guardrail Panel

Purpose:
Show warnings and disclaimer.

Anatomy:

```txt
section title: Guardrails
passed status
warnings
disclaimer
```

Rules:
- Must always render if guardrails object exists.
- Warnings must be visible.
- Disclaimer must be visible, especially for advisory output.
- If `passed=false`, show warning styling.

Required disclaimer text:

```txt
Thông tin này chỉ phục vụ mục đích tham khảo và demo hệ thống, không phải khuyến nghị đầu tư cá nhân hóa. Người dùng cần tự đánh giá rủi ro hoặc tham khảo chuyên gia tài chính trước khi ra quyết định.
```

## 6.12 Loading State

Purpose:
Make backend waiting time clear.

Rules:
- Must show text: `Đang phân tích...`
- Send button must be disabled or show loading state.
- Demo query buttons may be disabled during submit.
- Must not clear previous answer until new answer arrives unless intentionally showing a pending state.

## 6.13 Error State

Purpose:
Show backend/network failure clearly.

Example text:

```txt
Không thể kết nối backend. Hãy kiểm tra FastAPI server rồi thử lại.
```

Rules:
- Must not expose raw stack traces.
- Should include retry action if easy.
- Must not remove typed query.

## 6.14 Empty State

Purpose:
Guide first-time users.

Suggested copy:

```txt
Hỏi thử một câu về cổ phiếu Việt Nam.
Ví dụ: Tính RSI14 và SMA20 của FPT.
```

Rules:
- Must be visible before first response.
- Must point to demo buttons or composer.

## 7. Accessibility Requirements

Target: WCAG 2.2 AA.

### 7.1 Keyboard

- All buttons must be reachable with Tab.
- Focus order must be logical.
- Send action must be available from keyboard.
- No focus trap unless explicitly implemented and tested.

### 7.2 Focus

- Every interactive element must have a visible `:focus-visible` style.
- Focus outline must not be removed.
- Focus color should use `--color-primary`.

### 7.3 Contrast

- Text must be readable on dark surfaces.
- Muted text must not be used for essential information.
- Warning and error states must include text, not color only.

### 7.4 Screen Reader

- Input must have accessible label.
- Loading state should be readable text.
- Error messages should be text-based.
- Buttons must use descriptive labels.

### 7.5 Motion

- Use minimal motion.
- Transitions should use `--motion-duration-instant` or `--motion-duration-fast`.
- Do not use distracting animations.

## 8. Content Standards

Use Vietnamese labels by default.

Recommended UI labels:

```txt
Finance Agentic RAG
Trợ lý phân tích cổ phiếu Việt Nam
Câu hỏi mẫu
Câu trả lời
Tuyến xử lý
Ý định
Độ tin cậy
Độ trễ
Nguồn bằng chứng
Guardrails
Cảnh báo
Gửi
Đang phân tích...
```

Answer text should be:
- concise,
- evidence-aware,
- transparent about demo/mock data,
- free from guaranteed-return language.

## 9. Anti-patterns

Do not ship:

- raw JSON as the primary user interface,
- no evidence section,
- no guardrail section,
- missing disclaimer,
- hidden focus outlines,
- low-contrast text,
- hardcoded fake answers,
- direct frontend calls to third-party market APIs,
- UI that only works on desktop,
- buttons with ambiguous labels like `OK` or `Run`,
- financial advice copy that sounds personalized or guaranteed.

## 10. QA Checklist

Before marking frontend complete, verify:

```txt
[ ] npm install succeeds
[ ] npm run build succeeds
[ ] App loads without blank screen
[ ] All 5 demo query buttons are visible
[ ] Clicking each demo query sends request to /chat
[ ] Manual typed query can be submitted
[ ] Empty query is blocked
[ ] Loading state appears
[ ] Backend error state appears if server is down
[ ] Answer text is readable
[ ] Intent is visible
[ ] Route is visible
[ ] Confidence is visible
[ ] Latency is visible if returned
[ ] Evidence panel is visible
[ ] Guardrail panel is visible
[ ] Disclaimer is visible
[ ] Focus-visible styles are visible
[ ] Layout works at mobile width
[ ] No raw stack trace is shown to user
```

## 11. Codex Implementation Prompt

Use this prompt:

```txt
Read FRONTEND_SKILL.md and FRONTEND_DESIGN.md.

Refactor the existing React/Vite frontend to match this design system.

Do not change backend APIs.
Do not add new product features.
Do not calculate financial data in the frontend.
Do not hide evidence or guardrail warnings.

Implement:
- dark DeepSeek-like dashboard chat shell,
- demo query panel,
- chat response card,
- metadata badges,
- evidence panel,
- guardrail panel,
- loading state,
- error state,
- empty state,
- accessible focus-visible states,
- responsive mobile layout.

Use CSS variables from FRONTEND_DESIGN.md.
Run npm install and npm run build.
Fix all frontend issues before completion.
```

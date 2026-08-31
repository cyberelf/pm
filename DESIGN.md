---
version: alpha
name: reports-workspace-design-system
description: A two-surface local reporting workspace. The 周报工作台 (weekly report workspace) is the primary light surface — white canvas, black primary CTAs, compact Cal Sans display typography, persistent project sidebar, soft-rounded cards (~12px), no decorative page footer. The TODO 看板 (TODO board) is the one intentionally inverted dark surface — a navy three-column kanban with its own board-* accent token set. Both surfaces share one foundation: the same color tokens, type families, button/input/dialog/toast/badge recipes, and the page-corner fold navigation. The weekly report workspace is the source of truth for everything shared. Interface icons come from locally embedded Font Awesome Free SVG definitions.

colors:
  primary: "#111111"
  primary-active: "#242424"
  primary-disabled: "#e5e7eb"
  ink: "#111111"
  body: "#374151"
  muted: "#6b7280"
  muted-soft: "#898989"
  hairline: "#e5e7eb"
  hairline-soft: "#f3f4f6"
  canvas: "#ffffff"
  surface-soft: "#f8f9fa"
  surface-card: "#f5f5f5"
  surface-strong: "#e5e7eb"
  surface-dark: "#101010"
  surface-dark-elevated: "#1a1a1a"
  on-primary: "#ffffff"
  on-dark: "#ffffff"
  on-dark-soft: "#a1a1aa"
  brand-accent: "#3b82f6"
  success: "#10b981"
  warning: "#f59e0b"
  error: "#ef4444"
  badge-orange: "#fb923c"
  badge-pink: "#ec4899"
  badge-violet: "#8b5cf6"
  badge-emerald: "#34d399"
  board-canvas: "#172033"
  board-column-fill: "rgba(241, 245, 249, 0.12)"
  board-line: "rgba(255, 255, 255, 0.2)"
  board-line-soft: "rgba(255, 255, 255, 0.25)"
  board-line-strong: "rgba(255, 255, 255, 0.38)"
  board-count-fill: "rgba(255, 255, 255, 0.14)"
  board-draft-fill: "rgba(15, 23, 42, 0.25)"
  board-draft-fill-active: "rgba(37, 99, 235, 0.24)"
  board-todo-fill: "rgba(37, 99, 235, 0.34)"
  board-todo-line: "rgba(96, 165, 250, 0.75)"
  board-doing-fill: "rgba(5, 150, 105, 0.32)"
  board-doing-line: "rgba(52, 211, 153, 0.72)"
  board-closed-fill: "rgba(100, 116, 139, 0.38)"
  board-closed-line: "rgba(148, 163, 184, 0.68)"
  board-accent-blue: "#2563eb"
  board-accent-blue-line: "#60a5fa"
  board-accent-blue-soft: "#93c5fd"
  board-accent-green: "#059669"
  board-accent-slate: "#64748b"
  board-on-accent: "#dbeafe"
  board-muted-on-dark: "#bfdbfe"

typography:
  display-xl:
    fontFamily: "Cal Sans, Inter, sans-serif"
    fontSize: 64px
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: -2px
  display-lg:
    fontFamily: "Cal Sans, Inter, sans-serif"
    fontSize: 48px
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: -1.5px
  display-md:
    fontFamily: "Cal Sans, Inter, sans-serif"
    fontSize: 36px
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: -1px
  display-sm:
    fontFamily: "Cal Sans, Inter, sans-serif"
    fontSize: 28px
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: -0.5px
  title-lg:
    fontFamily: "Inter, sans-serif"
    fontSize: 22px
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: -0.3px
  title-md:
    fontFamily: "Inter, sans-serif"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: 0
  title-sm:
    fontFamily: "Inter, sans-serif"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: 0
  body-md:
    fontFamily: "Inter, sans-serif"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  body-sm:
    fontFamily: "Inter, sans-serif"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  caption:
    fontFamily: "Inter, sans-serif"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0
  code:
    fontFamily: "JetBrains Mono, ui-monospace, monospace"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0
  button:
    fontFamily: "Inter, sans-serif"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0
  nav-link:
    fontFamily: "Inter, sans-serif"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0

rounded:
  xs: 4px
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  pill: 9999px
  full: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  xxl: 48px
  section: 96px

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 12px 20px
    height: 40px
  button-primary-active:
    backgroundColor: "{colors.primary-active}"
    textColor: "{colors.on-primary}"
    rounded: "{rounded.md}"
  button-primary-disabled:
    backgroundColor: "{colors.primary-disabled}"
    textColor: "{colors.muted}"
    rounded: "{rounded.md}"
  button-secondary:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 12px 20px
    height: 40px
  button-icon-circular:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    size: 36px
  button-compact:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: 12px / 600
    rounded: "{rounded.md}"
    padding: 8px 11px
    height: 34px
  button-text-link:
    backgroundColor: transparent
    textColor: "{colors.ink}"
    typography: "{typography.button}"
  text-link:
    backgroundColor: transparent
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
  top-nav:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.nav-link}"
    height: 64px
  nav-pill-group:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink}"
    typography: "{typography.nav-link}"
    rounded: "{rounded.pill}"
    padding: 6px
  hero-band:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.display-xl}"
    padding: 96px
  hero-app-mockup-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
  feature-card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    typography: "{typography.title-md}"
    rounded: "{rounded.lg}"
    padding: 32px
  feature-icon-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.title-sm}"
    rounded: "{rounded.lg}"
    padding: 24px
  product-mockup-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: 24px
  testimonial-card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: 24px
  pricing-tier-card:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.title-lg}"
    rounded: "{rounded.lg}"
    padding: 32px
  pricing-tier-card-featured:
    backgroundColor: "{colors.surface-dark}"
    textColor: "{colors.on-dark}"
    typography: "{typography.title-lg}"
    rounded: "{rounded.lg}"
    padding: 32px
  text-input:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body-md}"
    rounded: "{rounded.md}"
    padding: 10px 14px
    height: 40px
  text-input-focused:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
  category-tab:
    backgroundColor: transparent
    textColor: "{colors.muted}"
    typography: "{typography.nav-link}"
    padding: 8px 14px
    rounded: "{rounded.md}"
  category-tab-active:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.nav-link}"
    rounded: "{rounded.md}"
  avatar-circle:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    size: 36px
  badge-pill:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: 4px 12px
  rating-stars:
    backgroundColor: transparent
    textColor: "{colors.badge-orange}"
    typography: "{typography.caption}"
  cta-band-light:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.ink}"
    typography: "{typography.display-sm}"
    rounded: "{rounded.lg}"
    padding: 48px
  page-corner:
    position: fixed top-right
    size: 188px x 162px
    foldSize: 36px (resting) / 104px (hover, focus, turning)
    typography: "{typography.caption}"
    textColor: "{colors.ink}" / inverted on the board
  todo-column:
    backgroundColor: "{colors.board-column-fill}"
    borderColor: "{colors.board-line}"
    textColor: "{colors.on-dark}"
    rounded: "{rounded.lg}"
    padding: 12px
  todo-column-todo:
    backgroundColor: "{colors.board-todo-fill}"
    borderColor: "{colors.board-todo-line}"
  todo-column-doing:
    backgroundColor: "{colors.board-doing-fill}"
    borderColor: "{colors.board-doing-line}"
  todo-column-closed:
    backgroundColor: "{colors.board-closed-fill}"
    borderColor: "{colors.board-closed-line}"
  todo-column-count:
    backgroundColor: column accent (board-accent-blue / board-accent-green / board-accent-slate)
    textColor: "{colors.on-dark}"
    typography: "{typography.caption}"
    rounded: "{rounded.pill}"
    padding: 4px 10px
  todo-card:
    backgroundColor: "{colors.canvas}"
    borderColor: "{colors.hairline}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: 14px
    shadow: subtle drop shadow
  todo-card-editable:
    backgroundColor: "{colors.canvas}"
    borderColor: "{colors.board-accent-blue-soft}" on hover
    cursor: text
  todo-draft:
    backgroundColor: "{colors.board-draft-fill}"
    borderColor: "{colors.board-line-strong}" dashed
    textColor: "{colors.board-on-accent}"
    rounded: "{rounded.lg}"
    minHeight: 92px
  todo-card-editor:
    backgroundColor: "{colors.canvas}"
    borderColor: "{colors.board-accent-blue-line}"
    ring: 2px "{colors.board-accent-blue-line}" at low alpha
---

## Overview

The token foundation of this system comes from a Cal.com design analysis: a white canvas (`{colors.canvas}` — #ffffff) with black primary CTAs (`{colors.primary}` — #111111), **Cal Sans** display typography over **Inter** body, soft-gray `{colors.surface-card}` cards, and pill-radius segmented navigation. It reads as confidently engineered without trying to impress — clear hierarchy, generous whitespace, a single primary action per zone.

The application built on that foundation is a **two-surface workspace**, and the surfaces deliberately differ in mood:

- **周报工作台 (Weekly Report Workspace)** — the primary, light surface. Persistent project sidebar (`{colors.surface-soft}`), white content canvas, gray `{component.panel}` cards, pill tab navigation. This surface **defines the shared system**: every token default, every shared component recipe, type scale, and interaction pattern is normed here.
- **TODO 看板 (TODO Board)** — the one intentionally inverted surface. A navy `{colors.board-canvas}` (#172033) floor with three translucent tinted columns (blue 待办 / green 进行中 / slate 已关闭) and white `{component.todo-card}` cards on top. It is a kanban, not a report editor — denser, darker, columnar.

**The consistency contract:** the two surfaces may differ in page floor, column composition, and accent mood, but everything shared — color tokens, font families and weights, button/input/dialog/toast/loading/badge/pill recipes, focus treatment, radius and spacing scales — is identical on both, and the weekly report workspace is the source of truth. The board gets its own `board-*` accent token set for column tints and dark-surface text; those tokens never appear on the light workspace, and shared controls are never restyled per-surface.

Both surfaces are joined by the `{component.page-corner}` page fold — a fixed top-right paper fold that flips between the two views. It is the only page-level ornament in the app.

The app is an operational shell, not a marketing page. Screens end with their working content area and never grow a decorative footer.

**Key Characteristics:**
- White canvas with black primary CTA (`{colors.primary}` — #111111). Buttons are `{rounded.md}` (8px) with confident weight-600 labels — the same button on both surfaces.
- Custom `Cal Sans` display typeface for headlines (substituted with Inter weight 600 here). Negative letter-spacing on display sizes — geometric, precise, slightly condensed.
- Light-gray card surfaces (`{colors.surface-card}` — #f5f5f5) for panels on the report workspace; white hairline-bordered cards (`{component.todo-card}`) everywhere on the board. Content cards are `{rounded.lg}` (12px) on both surfaces.
- Nav-pill-group (`{component.nav-pill-group}`) — a small pill-radius wrapper around grouped nav segments (the workspace tab bar and the source switcher). The pill wrapper is one of the system's signature interactive components.
- The persistent project sidebar is the main piece of application chrome on the report workspace; the board drops it entirely for full-width columns.
- The board uses a compact type scale (column head 16px, card title 15px, card body 13px, meta 11–12px) — same families and weights, smaller steps. See Typography.
- Spacing rhythm is `{spacing.section}` (96px) between major bands on editorial pages; the workspace topbar opens with 96px and the board runs dense at 8–16px gaps.
- Border radius is hierarchical and identical on both surfaces: `{rounded.md}` (8px) for buttons + inputs, `{rounded.lg}` (12px) for content cards and board columns, `{rounded.xl}` (16px) for dialogs and the hero container, `{rounded.pill}` for pill groups + badges.

## Surfaces

### 周报工作台 — light workspace (source of truth)
- Page floor `{colors.canvas}`; sidebar `{colors.surface-soft}`; content cards `{component.panel}` on `{colors.surface-card}`.
- Chromatically quiet: ink/body/muted text, black primary actions, semantic status colors only where state exists.
- Persistent project sidebar (260px desktop, horizontal switcher below 768px), sticky pill tab bar, no footer.

### TODO 看板 — dark board
- Page floor `{colors.board-canvas}` (#172033); sidebar hidden; board grid up to 1480px.
- Three columns carry translucent semantic tints: 待办 blue (`{colors.board-todo-fill}` / border `{colors.board-todo-line}`), 进行中 green (`{colors.board-doing-fill}` / `{colors.board-doing-line}`), 已关闭 slate (`{colors.board-closed-fill}` / `{colors.board-closed-line}`). Column heads are `{colors.on-dark}` with an accent count pill.
- Cards on the board are **exactly the light surface's card language** — `{colors.canvas}` background, `{colors.hairline}` border, `{rounded.lg}`, subtle drop shadow — so shared controls (buttons, inputs) render identically to the report workspace.
- Dark-surface text tones: `{colors.on-dark}` for headings, `{colors.board-muted-on-dark}` for secondary copy, `{colors.board-on-accent}` for text on translucent fills.
- The board accent blue (`{colors.board-accent-blue-soft}` / `{colors.board-accent-blue-line}`) drives edit affordances: editable-card hover, draft-button hover, editor ring, and the dark-surface focus outline.

### Shared on every surface
- Color tokens, font families, the type scale, radius + spacing scales.
- Buttons (`button-primary`, `button-secondary`, danger), inputs, `text-input` focus treatment, dialogs, toast, loading overlay, badges/status pills.
- Focus treatment: 2px `{colors.ink}` outline at 2px offset on the light surface; 2px `{colors.board-accent-blue-soft}` outline everywhere on the TODO board, where ink would disappear into the navy floor.
- The `{component.page-corner}` fold navigation, with labels inverting to `{colors.on-dark}` on the board.

### Rules
1. The weekly report workspace wins every disagreement about a shared component. If the board needs a different treatment, that treatment becomes a documented board token or component — never an inline override of a shared recipe.
2. `board-*` accents never leak onto the light workspace; `{colors.brand-accent}` and badge pastels never appear on the board.
3. No third surface. New pages adopt one of the two existing moods.

## Colors

### Brand & Accent
- **Primary** (`{colors.primary}` — #111111): The dominant action color. All primary CTAs, h1/h2 display type. Press state shifts to `{colors.primary-active}` (#242424).
- **Brand Accent** (`{colors.brand-accent}` — #3b82f6): Used sparely on inline links and on a small badge / "Customer story" highlight. Cal.com is a near-monochrome brand — the blue appears rarely.
- **Badge Pastels** — A small pastel set for category badges and avatar fills: `{colors.badge-orange}` (#fb923c), `{colors.badge-pink}` (#ec4899), `{colors.badge-violet}` (#8b5cf6), `{colors.badge-emerald}` (#34d399). These appear on tag pills and small accent moments inside product UI fragments — never on hero CTAs.

### Surface
- **Canvas** (`{colors.canvas}` — #ffffff): The default page floor.
- **Surface Soft** (`{colors.surface-soft}` — #f8f9fa): Nav-pill-group background, very-soft section dividers.
- **Surface Card** (`{colors.surface-card}` — #f5f5f5): Feature cards, testimonial cards, badge pills, default avatar fills.
- **Surface Strong** (`{colors.surface-strong}` — #e5e7eb): Hairline border alternative; disabled button background.
- **Surface Dark** (`{colors.surface-dark}` — #101010): Reserved for overlays and intentionally inverted special surfaces; it is not used as a persistent page footer.
- **Surface Dark Elevated** (`{colors.surface-dark-elevated}` — #1a1a1a): Used only for nested elements inside an intentionally inverted surface.
- **Hairline** (`{colors.hairline}` — #e5e7eb): The 1px border tone on light surfaces. Used on input borders, table dividers, content card outlines (sometimes).
- **Hairline Soft** (`{colors.hairline-soft}` — #f3f4f6): A barely-visible divider used between sections that share the white canvas.

### Text
- **Ink** (`{colors.ink}` — #111111): All headlines and primary text.
- **Body** (`{colors.body}` — #374151): Default running-text color.
- **Muted** (`{colors.muted}` — #6b7280): Secondary text — sub-headings, week labels, and breadcrumbs.
- **Muted Soft** (`{colors.muted-soft}` — #898989): Tertiary text — captions, fine-print, copyright lines.
- **On Primary / On Dark** (`{colors.on-primary}` / `{colors.on-dark}` — #ffffff): Text on primary buttons and intentionally inverted surfaces.
- **On Dark Soft** (`{colors.on-dark-soft}` — #a1a1aa): Secondary text on intentionally inverted surfaces.

### Semantic
- **Success** (`{colors.success}` — #10b981): Confirmation states, success badges in product UI, and the on-state fill of toggle switches (`{component.switch}`).
- **Warning** (`{colors.warning}` — #f59e0b): Warning callouts.
- **Error** (`{colors.error}` — #ef4444): Validation errors, plus the danger chrome of delete/remove buttons (`{component.button-danger}`).

### Board (TODO 看板 only)
The board carries its own closed accent set. These tokens are scoped to `#todo-view` and never appear on the light workspace:
- **Board Canvas** (`{colors.board-canvas}` — #172033): The dark navy page floor of the TODO board.
- **Column Tints** — translucent semantic fills + borders for the three columns: `{colors.board-todo-fill}`/`{colors.board-todo-line}` (blue, 待办), `{colors.board-doing-fill}`/`{colors.board-doing-line}` (green, 进行中), `{colors.board-closed-fill}`/`{colors.board-closed-line}` (slate, 已关闭). `{colors.board-column-fill}` is the neutral fallback; `{colors.board-line}` the neutral border.
- **Column Accent Solids** — `{colors.board-accent-blue}` (#2563eb), `{colors.board-accent-green}` (#059669), `{colors.board-accent-slate}` (#64748b): count-pill fills.
- **Edit Accents** — `{colors.board-accent-blue-line}` (#60a5fa) for the editor card ring and `{colors.board-accent-blue-soft}` (#93c5fd) for editable-card / draft hover borders and the dark-surface focus outline.
- **Translucent Whites** — `{colors.board-line-soft}` / `{colors.board-line-strong}` for dashed placeholder borders, `{colors.board-count-fill}` for the neutral count pill, `{colors.board-draft-fill}` / `{colors.board-draft-fill-active}` for the draft button's resting / active fills.
- **Text on Dark** — `{colors.on-dark}` for headings, `{colors.board-on-accent}` (#dbeafe) for text on translucent fills, `{colors.board-muted-on-dark}` (#bfdbfe) for secondary copy and empty states.

## Typography

### Font Family
The system runs **Cal Sans** for display + brand wordmark and **Inter** for everything else. Cal Sans is Cal.com's custom geometric display typeface — slightly condensed, weight 600, negative letter-spacing. Inter handles body, buttons, navigation, captions, and tabular code blocks. The fallback stack walks `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` for both families.

The split is functional:
- Cal Sans (display, 600 weight, -0.5 to -2px tracking) — h1, h2, h3
- Inter (body + UI, 400-600 weight, 0 letter-spacing) — paragraphs, labels, buttons, nav

### Hierarchy

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| `{typography.display-xl}` | 64px | 600 | 1.05 | -2px | Homepage h1 ("The better way to schedule your meetings") — Cal Sans |
| `{typography.display-lg}` | 48px | 600 | 1.1 | -1.5px | Section heads ("Your all-purpose scheduling app") — Cal Sans |
| `{typography.display-md}` | 36px | 600 | 1.15 | -1px | Sub-section heads, card titles — Cal Sans |
| `{typography.display-sm}` | 28px | 600 | 1.2 | -0.5px | CTA-band heads, pricing tier prices — Cal Sans |
| `{typography.title-lg}` | 22px | 600 | 1.3 | -0.3px | Pricing plan names — Inter |
| `{typography.title-md}` | 18px | 600 | 1.4 | 0 | Feature card titles, intro paragraphs |
| `{typography.title-sm}` | 16px | 600 | 1.4 | 0 | Small card titles, list labels |
| `{typography.body-md}` | 16px | 400 | 1.5 | 0 | Default running-text |
| `{typography.body-sm}` | 14px | 400 | 1.5 | 0 | Secondary application copy and fine-print |
| `{typography.caption}` | 13px | 500 | 1.4 | 0 | Badge labels, captions |
| `{typography.code}` | 14px | 400 | 1.5 | 0 | Code snippets, API examples — JetBrains Mono |
| `{typography.button}` | 14px | 600 | 1.0 | 0 | Standard button labels |
| `{typography.nav-link}` | 14px | 500 | 1.4 | 0 | Top-nav menu items |

### Principles
Cal Sans is the brand voice — every display headline uses it. Inter handles the supporting type. The boundary is strict: never put body copy in Cal Sans, never put a display headline in Inter. Cal Sans without negative letter-spacing reads as off-brand — the -0.5 to -2px tracking is part of the voice.

Display weight stays at 600 across all sizes — never 700, never 500. The middle weight is what makes Cal Sans feel modern and confident without becoming bombastic.

The reporting workspace uses a compact application-title treatment instead of the larger marketing display scale: project titles are 28px on desktop and 24px on mobile. The current project week sits on the same line to the right in muted 14px UI text; the pair may wrap together on narrow screens.

### Board Scale (TODO 看板)
The board keeps the same two families and the same weights but steps the scale down for kanban density — same fonts, smaller sizes:
- Column heads: 16px / 600 (Cal Sans role) in `{colors.on-dark}`
- Card titles: 15px / 600 in `{colors.ink}`
- Card body (markdown): 13px / 400, inline code 12px `{typography.code}`
- Card meta + hints: 11–12px / 500–600 in `{colors.muted-soft}`
- Count pills + project tags: 12px / 500 (`{typography.caption}` territory) — matching the light surface's badge metrics

The page h1 on the board follows the workspace title treatment (28px, `{colors.on-dark}`), so both surfaces share one title rhythm at the top of the page.

### Note on Font Substitutes
If Cal Sans is unavailable, **Inter** at weight 600 with -0.04em letter-spacing is a usable approximation. The geometric character of Cal Sans differs from Inter's humanist forms, but the substitution preserves the weight + tracking signature. **Manrope** at weight 700 is another close alternative.

## Layout

### Spacing System
- **Base unit:** 4px.
- **Tokens:** `{spacing.xxs}` 4px · `{spacing.xs}` 8px · `{spacing.sm}` 12px · `{spacing.md}` 16px · `{spacing.lg}` 24px · `{spacing.xl}` 32px · `{spacing.xxl}` 48px · `{spacing.section}` 96px.
- **Section padding:** `{spacing.section}` (96px) — the universal vertical rhythm between editorial bands.
- **Card internal padding:** `{spacing.xl}` (32px) for feature cards and pricing tier cards; `{spacing.lg}` (24px) for testimonial and product-mockup cards.
- **Gutters:** `{spacing.lg}` (24px) between cards in 3-up grids; `{spacing.md}` (16px) between compact controls.

### Grid & Container
- **Max content width:** ~1200px centered on marketing pages.
- **Editorial body:** Single 12-column grid; hero band often uses 7/5 split (h1 left, app mockup card right).
- **Feature card grids:** 3-up at desktop, 2-up at tablet, 1-up at mobile.
- **Pricing grid:** 4-up at desktop, 2-up at tablet, 1-up at mobile.
- **Application shell:** Persistent project sidebar on desktop, compact horizontal project switcher below 768px, and no page footer.
- **TODO board:** No sidebar — a single full-viewport floor. Three columns in a grid of `repeat(3, minmax(260px, 1fr))`, 16px gutters, board content capped at 1480px. Below 1024px the board scrolls horizontally instead of collapsing the columns; below 768px columns are `minmax(260px, 84vw)`.

### Whitespace Philosophy
Cal.com uses generous but not excessive whitespace — section padding sits at 96px (modern-SaaS standard), and card internal padding stays at 32px. The rhythm is calibrated for fast scanning: every band has a single h1 + h2 + supporting cards, never densely packed lists. The result reads as confident-not-shouting.

## Elevation & Depth

| Level | Treatment | Use |
|---|---|---|
| Flat | No shadow, no border | Body sections, top nav, hero bands |
| Soft hairline | 1px `{colors.hairline}` border | Inputs, table dividers, occasionally on cards |
| Card surface | `{colors.surface-card}` background — no shadow | Feature cards, testimonials |
| Subtle drop shadow | Faint shadow at low alpha | Pricing tier cards, hover-elevated states (the system uses `0 1px 2px rgba(0,0,0,0.05)` and `0 4px 12px rgba(0,0,0,0.08)`) |
| Board glass panel | Translucent tinted fill + 1px translucent border over `{colors.board-canvas}` | TODO board columns — alpha layering does the elevation work, no shadows |
| Featured tier | `{colors.surface-dark}` background, no shadow needed | The featured pricing tier inverts to dark surface — color contrast does the elevation work |

The elevation philosophy is **soft and modern** — small drop shadows on elevated cards, color-block contrast for emphasis. No heavy shadows, no neumorphism, no glassmorphism.

### Decorative Depth
- Calendar widgets and product UI fragments embedded inside marketing cards carry their own internal shadows from the product UI itself — these are not system tokens, they're product chrome shown as content.
- Avatar circles in testimonial sections sometimes carry pastel fill colors (`{colors.badge-orange}`, `{colors.badge-pink}`, etc.) — adds a small chromatic flourish without breaking the monochrome brand voice.

## Shapes

### Border Radius Scale

| Token | Value | Use |
|---|---|---|
| `{rounded.xs}` | 4px | Almost no use — reserved for badge accents |
| `{rounded.sm}` | 6px | Small inline buttons, dropdown items |
| `{rounded.md}` | 8px | Standard CTA buttons, text inputs, category tabs |
| `{rounded.lg}` | 12px | Content cards (feature cards, testimonial cards, pricing tier cards) |
| `{rounded.xl}` | 16px | Hero app-mockup card (a slightly larger radius for the marquee component) |
| `{rounded.pill}` | 9999px | Nav-pill-group, badge pills |
| `{rounded.full}` | 9999px / 50% | Avatars, icon buttons |

### Photography Geometry
Avatar photos use `{rounded.full}` (perfect circles) at 36px or 40px. Product UI fragments inside marketing cards retain their native chrome (which often has its own internal radii — e.g., calendar grid cells, button rows). Hero illustration zones use 16:9 or 4:3 ratios with `{rounded.xl}` corners.

## Iconography

- Use Font Awesome Free as the default source for interface icons. Choose the semantically closest solid or regular icon before considering a custom drawing.
- Embed only the selected SVG definition locally; do not load icon fonts, kits, or CDN assets at runtime. Preserve the Font Awesome name, version, license attribution, `viewBox`, and path data next to the local definition.
- Render UI icons at 16–18px with `currentColor` so active, muted, and disabled states follow the surrounding control.
- Icon-only buttons require a visible tooltip and a specific accessible label. The SVG itself is decorative and uses `aria-hidden="true"`.
- Do not substitute emoji, Unicode symbols, or improvised SVG paths when Font Awesome contains a suitable icon.

## Components

### Top Navigation

**`top-nav`** — White nav bar pinned to the top of every page. 64px tall, `{colors.canvas}` background. Carries the Cal.com wordmark + logo at left (the lowercase "Cal.com" with the brand circle), primary horizontal menu (Product, Solutions, Resources, Pricing, Enterprise) center, right-side cluster with "Sign in" text-link, "Sign up free" `{component.button-primary}`, and a sometimes-visible language selector. Menu items in `{typography.nav-link}` (Inter 14px / 500).

**`nav-pill-group`** — A small pill-radius wrapper around 2-3 sub-nav segments (e.g., the product-mode switcher between "Personal" / "Teams" / "Enterprise"). Background `{colors.surface-soft}` with internal padding 6px, rounded `{rounded.pill}`. Active segment renders as a white-canvas pill with a subtle drop shadow inside the wrapper. The pill-in-pill treatment is one of Cal.com's signature interactive components.

### Buttons

**`button-primary`** — The signature primary CTA. Background `{colors.primary}` (#111111), text `{colors.on-primary}`, type `{typography.button}` (Inter 14px / 600), padding 12px × 20px, height 40px, rounded `{rounded.md}` (8px). Active state `button-primary-active` shifts to `{colors.primary-active}` (#242424).

**`button-secondary`** — White button with hairline outline. Background `{colors.canvas}`, text `{colors.ink}`, 1px hairline border, same padding + height + radius as primary.

**`button-icon-circular`** — 36 × 36px circular icon button. Background `{colors.canvas}`, hairline border, ink-color icon. Used for share, "view more", carousel arrows.

**`button-compact`** — The sanctioned small button for dense card rows (TODO card actions). Same chrome as `button-secondary` (canvas fill, hairline border, `{rounded.md}`) at reduced metrics: 34px min-height, 8px × 11px padding, 12px / 600 label. Primary and danger variants keep their fills at compact size. Everything else — inputs, dialogs, toast — stays at standard size; `button-compact` is the only sanctioned reduction.

**`button-text-link`** — Inline text button, no background. Used for "Sign in" in the top nav and inline CTA links inside cards.

**`button-danger`** — Secondary-chrome button reserved for destructive actions (delete material, delete repo, remove schedule row). Same metrics as `button-secondary`; border `{colors.error-border}` (#fecaca), text `{colors.error-ink}` (#b91c1c), active fill `{colors.error-surface}` (#fef2f2). Every delete/remove action uses this variant — no other buttons may carry danger chrome.

**`text-link`** — Inline body links in `{colors.ink}` (the brand keeps inline links monochrome). Underlined on hover (not documented per the no-hover policy, but mentioned for context).

### Cards & Containers

**`hero-band`** — White-canvas hero with a 7-5 grid: h1 + sub-headline + button row on the left, `{component.hero-app-mockup-card}` on the right. Vertical padding `{spacing.section}` (96px).

**`hero-app-mockup-card`** — A larger product-UI mockup card showing the actual Cal.com booking widget with calendar grid, time slots, and a primary "Confirm" button inside. Background `{colors.canvas}`, 1px hairline border, rounded `{rounded.xl}` (16px), subtle drop shadow. Used as the hero's right-side artifact.

**`feature-card`** — Used in 3-up feature grids ("With us, appointment scheduling is easy"). Background `{colors.surface-card}` (#f5f5f5), rounded `{rounded.lg}` (12px), internal padding `{spacing.xl}` (32px). Carries a small icon at top, an `{typography.title-md}` headline, and a body description in `{typography.body-md}`.

**`feature-icon-card`** — A simpler card variant used in 4-up feature grids on lower-density bands. Background `{colors.canvas}` with hairline border, rounded `{rounded.lg}`, padding `{spacing.lg}` (24px). Carries a small icon, `{typography.title-sm}` title, short description.

**`product-mockup-card`** — A card showing actual Cal.com product UI fragments (workflow editor, calendar grid, integration grid, automation flow). Background `{colors.canvas}`, rounded `{rounded.lg}`, padding `{spacing.lg}` (24px). The product UI inside has its own internal chrome — these cards display the product, they don't decorate around it.

**`testimonial-card`** — Used in customer-quote grids. Background `{colors.surface-card}`, rounded `{rounded.lg}`, padding `{spacing.lg}` (24px). Top row carries a `{component.avatar-circle}` + name + role; below sits the testimonial quote in `{typography.body-md}`.

**`pricing-tier-card`** — Standard tier card. Background `{colors.canvas}`, rounded `{rounded.lg}`, padding `{spacing.xl}` (32px). Carries the plan name in `{typography.title-lg}`, price in `{typography.display-sm}`, feature checklist in `{typography.body-md}`, and a `{component.button-primary}` at the bottom.

**`pricing-tier-card-featured`** — The featured tier (typically "Teams"). Background flips to `{colors.surface-dark}` (#101010), text inverts to `{colors.on-dark}`. The dark surface IS the featured-tier signal — no accent border, no badge, no scale shift.

### Inputs & Forms

**`text-input`** — Standard text input. Background `{colors.canvas}`, text `{colors.ink}`, type `{typography.body-md}`, rounded `{rounded.md}` (8px), padding 10px × 14px, height 40px. 1px hairline border in `{colors.hairline}`.

**`text-input-focused`** — Focus state. Border thickens or shifts to `{colors.ink}` for emphasis.

### Switch

**`switch`** — Two-state toggle for enable/disable (GitHub repo sources, update schedules). 36 × 20px pill track with a 16px `{colors.canvas}` knob. Off: `{colors.surface-strong}` (#e5e7eb) track. On: `{colors.success}` (#10b981) track. Track fill and knob travel animate over 150ms. Built on a real checkbox: the invisible input keeps keyboard toggling, and focus shows the standard ink `focus-visible` outline around the track. Disabled rows dim or tint their container but the switch itself stays fully interactive. Inside form rows the switch sits in a 40px-high cell so its center aligns with the standard input line.

### Tags / Badges

**`badge-pill`** — Small pill label used for category tags ("Product", "Article", "New") and pastel-fill avatar substitutes. Background `{colors.surface-card}` or one of the badge pastels (`{colors.badge-orange}`, `{colors.badge-pink}`, etc.), text `{colors.ink}`, type `{typography.caption}` (13px / 500), rounded `{rounded.pill}`, padding 4px × 12px.

**`avatar-circle`** — 36px diameter, rounded `{rounded.full}`. Either holds a photo or a pastel fill with initials in `{typography.caption}`.

**`rating-stars`** — Inline star rating in `{colors.badge-orange}` (#fb923c). Used near testimonial avatars to display a 5-star satisfaction score.

### Tab / Filter

**`category-tab`** + **`category-tab-active`** — Used inside the nav-pill-group. Inactive: transparent background, `{colors.muted}` text. Active: `{colors.canvas}` background, `{colors.ink}` text, subtle drop shadow inside the pill-group wrapper. Padding 8px × 14px, rounded `{rounded.md}`.

### CTA

**`cta-band-light`** — A light CTA card. Background `{colors.surface-card}`, rounded `{rounded.lg}`, padding `{spacing.xxl}` (48px). Carries an h2 in `{typography.display-sm}`, a sub-line, and a `{component.button-primary}` centered.

### Page Fold Navigation

**`page-corner`** — The signature shared navigation device: a fixed 188 × 162px zone pinned to the top-right corner, acting as a `role="button"` page fold. At rest a 36px paper triangle (blue-gray gradient, component-scoped art constants — not system tokens) covers the corner; the current page label sits beside it in 17px strong + 9px tracked small caps. On hover / keyboard focus / turn, the fold animates to 104px over 360ms (`cubic-bezier(.25, .9, .3, 1)`), the current label fades out, and the target page label fades in on the fold itself. Clicking flips between 周报 and TODO with a 400ms peel animation and a 280ms view-enter fade on the incoming surface. All motion is disabled under `prefers-reduced-motion`.

- On the board, the labels invert to `{colors.on-dark}` with a text shadow for legibility on the fold.
- The fold is decorative chrome: its SVG-free gradient + clip-path art is fixed; it never carries state beyond the two page labels.
- The `theme-color` meta follows the surface — white on 周报, `{colors.board-canvas}` on the board.

### TODO Board

**`todo-column`** — One kanban column. Translucent tinted fill + 1px translucent border, rounded `{rounded.lg}`, 12px internal padding, 280px min-height, 12px gap between cards. Variants: `todo-column-todo` (blue), `todo-column-doing` (green), `todo-column-closed` (slate). The tint reads as a colored glass panel over the navy floor.

**`todo-column-count`** — Pill counter in the column head. Accent solid fill per column (`{colors.board-accent-blue}` / `-green` / `-slate`), `{colors.on-dark}` text, `{typography.caption}` metrics (12px / 500), padding 4px × 10px, min-width 26px, centered. Same pill geometry as the light surface's `status` badges.

**`todo-card`** — A white card on the dark board. `{colors.canvas}` background, 1px `{colors.hairline}` border, rounded `{rounded.lg}`, 14px padding, subtle drop shadow, 10px internal gap. Carries a 15px/600 title, optional 13px markdown body (inline code 12px mono on `{colors.surface-soft}`), an 11px muted meta line ("更新于 …"), and `{component.button-compact}` action buttons (`开始` / `关闭` secondary+primary, `移回待办`, or `查看项目资料` + danger `删除` on closed cards — destructive actions confirm through the shared `message-dialog`). Closed cards add a `{colors.success}` left-rail close-reason block and a success-soft project tag pill — the same recipe as `status` success badges on the light surface.

**`todo-card-editable`** — An open card in read mode. Cursor text; hover shifts the border to `{colors.board-accent-blue-soft}` with an elevated shadow to signal in-place editing. Keyboard focus shows the 2px board focus outline. Click or Enter swaps it for the editor.

**`todo-draft`** — The "＋ 添加 TODO" affordance pinned at the bottom of the 待办 column. A full-width dashed button (`{colors.board-line-strong}` border, `{colors.board-draft-fill}` fill, min-height 92px) with `{colors.on-dark}` strong label + 11px hint. Hover / active shifts to the blue draft fill (`{colors.board-draft-fill-active}`) with `{colors.board-accent-blue-soft}` border — the dark-surface equivalent of an add-control, never a black primary CTA (which would vanish on navy).

**`todo-card-editor`** — The inline editing state of a card: border shifts to `{colors.board-accent-blue-line}` with a 2px low-alpha ring. Contains a standard 40px `{component.text-input}` for the title (weight 600) and a mono `{typography.code}` textarea for the markdown description, plus an 11px autosave hint. Saves on focus-out; Escape cancels; Cmd/Ctrl+Enter commits.

## Do's and Don'ts

### Do
- Reserve `{colors.primary}` (#111111) for primary CTAs and h1/h2 type. Cal.com's button is near-black, not blue.
- Use Cal Sans for every display headline. Pair with Inter body. Never blur the boundary.
- Apply negative letter-spacing on display sizes (-0.5 to -2px). Cal Sans without it reads as off-brand.
- Use `{component.feature-card}` (light gray) and `{component.product-mockup-card}` (white with chrome) deliberately — the gray cards signal "abstract feature claim", white cards signal "look at the actual product".
- Embed real product UI fragments inside marketing cards. Don't paint marketing illustrations of the product when you can show the product itself.
- Keep avatar circles at 36px, perfect circles, sometimes with pastel fills. Avatars are the only place where badge pastels appear.
- Use `{component.nav-pill-group}` for grouped sub-nav segments. The pill-in-pill treatment is signature.
- Use a locally embedded Font Awesome Free SVG for interface actions such as project settings.
- Let operational pages end with their content area; do not append a decorative footer.
- Treat the 周报工作台 as the source of truth for shared components: the board reuses the same buttons, inputs, dialogs, toast, loading overlay, and badge recipes on its white cards. `{component.button-compact}` is the one sanctioned size reduction, for dense card action rows.
- Keep every TODO-board color in the `board-*` token set (`{colors.board-canvas}`, `{colors.board-todo-fill}`, …) and reference tokens in CSS — never re-hardcode a hex or rgba in a component rule.
- Match badge/pill metrics across surfaces: 12px / 500, padding 4px × 10px, `{rounded.pill}` — count pills, project tags, and status badges all share one geometry.
- Switch the focus outline by floor: ink on light, `{colors.board-accent-blue-soft}` on the board, so keyboard focus is always visible.
- Update the `theme-color` meta with the surface (white ↔ `{colors.board-canvas}`).

### Don't
- Don't use accent colors (`{colors.brand-accent}`, badge pastels) on primary CTAs. The system is monochrome at the action layer.
- Don't bold display weight beyond 600. Cal Sans at 700 reads as bombastic.
- Don't use rounded radius beyond `{rounded.xl}` (16px) on cards. Larger radii read as consumer-app, not professional booking software.
- Don't introduce persistent dark page chrome. Dark surfaces remain a deliberate, scarce signal — the TODO board is the one inverted surface; the light workspace never adopts board tints.
- Don't draw one-off interface icons when Font Awesome Free contains a suitable semantic match.
- Don't restyle shared controls per-surface — dense rows use `{component.button-compact}`, never ad-hoc sizes; inputs, dialogs, and overlays keep standard metrics on both pages.
- Don't let `board-*` accents leak onto the light workspace, and don't put `{colors.brand-accent}` or badge pastels on the board.
- Don't add a third visual theme; new pages adopt the light workspace or board mood wholesale.
- Don't add hover state styling beyond what the system already encodes — primary darkens on press; nothing else changes. (Board edit affordances — editable-card, draft, fold — are the documented exceptions.)

## Responsive Behavior

### Breakpoints

| Name | Width | Key Changes |
|---|---|---|
| Mobile | < 768px | Project switcher becomes horizontal; application title 28→24px; title metadata may wrap; content grids become 1-up; TODO board columns become `minmax(260px, 84vw)` and scroll horizontally; page-corner scales to 85% |
| Tablet | 768–1024px | Top nav stays horizontal but tightens; nav-pill-group wraps; feature cards 2-up; pricing 2-up; TODO board keeps 3 columns and scrolls horizontally |
| Desktop | 1024–1440px | Full top-nav with all menu items; 3-up feature cards; 4-up pricing tiers; TODO board 3-up columns at full width |
| Wide | > 1440px | Same as desktop with more outer breathing room; max content width caps at 1200px (board caps at 1480px) |

### Touch Targets
- `{component.button-primary}` at minimum 40 × 40px.
- `{component.button-icon-circular}` at exactly 36 × 36 — slightly under WCAG's 44 × 44 but the centered icon and full-circle silhouette compensate.
- `{component.text-input}` height is 40px.
- `{component.category-tab}` rendered inside nav-pill-group has 8 × 14 padding; effective tap area meets 44px+ with the surrounding pill.

### Collapsing Strategy
- Top nav collapses to hamburger at < 768px; menu opens as a full-screen sheet.
- Hero band's 7-5 grid collapses to single-column on mobile — h1 + sub-head + buttons first, then the app-mockup card below.
- Feature grids reduce columns rather than scaling cards down.
- Pricing tier cards collapse 4 → 2 → 1; featured-tier dark surface stays visually distinct at every breakpoint.
- Nav-pill-group wraps to multi-row on tablet if the segments don't fit horizontally.
- Avatar + testimonial card layouts stay grid-aligned at every breakpoint.
- The TODO board never reflows to fewer columns — kanban columns stay side-by-side and the board scrolls horizontally below 1024px, preserving the three-state scan.
- The board drops the sidebar entirely (single-column shell); the workspace keeps it until 768px.

### Image Behavior
- Product UI fragments inside cards retain native aspect ratios; the cards themselves resize.
- Avatar photos crop to circles at every breakpoint.
- Hero app-mockup card scales proportionally on mobile — the calendar grid stays legible.

## Iteration Guide

1. Focus on ONE component at a time. Reference its YAML key directly (`{component.feature-card}`, `{component.todo-card}`).
2. Variants of an existing component (`-active`, `-disabled`, `-focused`) live as separate entries in `components:`.
3. Use `{token.refs}` everywhere — never inline hex. Board colors go through the `board-*` tokens, and CSS rules reference the `--board-*` variables.
4. Never document hover. Default and Active/Pressed states only. (The board's edit affordances — editable-card, draft, fold — are the documented exceptions.)
5. Display headlines stay Cal Sans 600 with negative letter-spacing. Body stays Inter 400. The trinity does not blur.
6. Use Font Awesome Free for new interface icons and keep selected SVG definitions local.
7. Operational application pages do not use a decorative footer.
8. When in doubt about emphasis: bigger Cal Sans before bolder Cal Sans.
9. When a shared component and a surface disagree, the 周报工作台 wins; give the board a named token or component instead of an inline override.

## Known Gaps

- The dembrandt frequency analyzer captured `Buttons: 0 variants` — Cal.com renders most CTAs as styled `<a>` link elements rather than `<button>` tags, which dembrandt's button selector doesn't capture. Button styles are documented from screenshot ground-truth + standard Cal Sans / Inter baselines.
- Cal Sans is licensed to Cal.com and not available as a public web font; substitutes are documented in the typography section.
- The badge pastel set (orange / pink / violet / emerald) is documented from observed avatar fill colors; exact hex values may shift seasonally.
- The `board-*` accent set is native to this application (tailwind blue/emerald/slate families at translucent alpha), not Cal.com-derived; it is tuned for contrast on `{colors.board-canvas}` and may be re-tuned as one set.
- Animation and transition timings (calendar slot picker, schedule confirmation, integration grid hover-reveal) are not in scope. The page-fold timings (360ms fold, 400ms peel, 280ms view-enter) are implemented values, not analyzed ones.
- Form validation states beyond `{component.text-input-focused}` are not extracted — error / success states would need a sign-up or booking flow to confirm.
- The actual booking widget surface (cal.com/{username}) is the product, not a marketing surface; its spec is out of scope.
- Avatar photos in testimonial sections sometimes carry pastel circular fills with initials instead of photographs; both treatments coexist on the same page.

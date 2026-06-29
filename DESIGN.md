# Weekly Reports Workspace Design

## Product Shape

This is a local personal workbench for recurring project tracking. The first screen is the usable workspace: project navigation, status summary, settings, plan, sources, reports, and risks. It is not a marketing page.

## Visual Direction

- Use a quiet dark operational interface inspired by dense developer tools.
- Keep content compact and scannable; avoid hero sections, decorative blobs, and nested cards.
- Use one primary accent color for commands and focus states.
- Cards are only for actual panels and repeated records; page sections remain unframed layouts.
- Border radius stays at 8px or below unless a pill badge is needed.
- Text must not scale with viewport width. Letter spacing is `0`.

## Palette

- Canvas: `#090a0d`
- Sidebar: `#0d0f14`
- Panel: `#11141a`
- Panel raised: `#151922`
- Hairline: `#252b36`
- Strong hairline: `#364052`
- Text: `#f4f7fb`
- Muted text: `#a4adbb`
- Subtle text: `#717b8c`
- Primary accent: `#6f7dfb`
- Success: `#3fb950`
- Warning: `#d29922`
- Danger: `#f85149`

## Layout

- Desktop uses a left project sidebar and a main work surface.
- Topbar shows project title, China timezone context, project week, and generation actions.
- Tabs remain visible under the topbar for predictable navigation.
- Overview uses metrics first, then current plan and current report.
- Report page uses a readable Markdown surface and a separate generation history panel.

## Timezone

- The UI presents the default timezone as `中国标准时间 (Asia/Shanghai)`.
- First release should treat China time as the primary UI timezone.
- Stored timezone remains IANA `Asia/Shanghai`.

## Loading States

- Long operations must disable triggering controls and show visible progress.
- Manual report generation shows:
  - Disabled Generate buttons
  - Spinner in the active button
  - Global overlay with operation text
  - Toast on completion or failure

## Implementation Notes

- Keep frontend dependency-free: static HTML/CSS/JS.
- Keep backend dependency-free unless a task explicitly justifies a package.
- Prefer server-rendered JSON APIs and small frontend render helpers.
- Do not introduce authentication, teams, or remote deployment in the first release.

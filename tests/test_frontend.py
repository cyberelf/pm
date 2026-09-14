import shutil
import subprocess
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is required for frontend behavior tests")
class FrontendTest(unittest.TestCase):
    def test_workspace_navigation_and_material_controls_match_current_ui(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertLess(html.index('data-tab="overview"'), html.index('data-tab="sources"'))
        self.assertLess(html.index('data-tab="sources"'), html.index('data-tab="report"'))
        self.assertIn('data-tab="settings"', html)
        self.assertNotIn('data-tab="risks"', html)
        self.assertNotIn('id="tab-risks"', html)
        self.assertLess(html.index('data-tab="sources"'), html.index('data-tab="updates"'))
        self.assertLess(html.index('data-tab="updates"'), html.index('data-tab="report"'))
        self.assertLess(html.index('data-tab="report"'), html.index('data-tab="plan"'))
        self.assertLess(html.index('data-tab="plan"'), html.index('data-tab="settings"'))
        self.assertIn('data-project-settings=', source)
        self.assertIn('data-project-generate=', source)
        self.assertIn('switchTab("settings")', source)
        self.assertIn("function switchPlanSubTab(", source)
        self.assertIn("function switchSettingsSubTab(", source)
        self.assertIn('data-subtab="diagnostics"', source)
        self.assertIn('id="settings-sub-diagnostics"', source)
        self.assertIn('id="plan-sub-risk"', source)
        self.assertIn('const FA_ICONS = {', source)
        self.assertIn('${faIcon("gear")}', source)
        self.assertNotIn('<footer class="app-footer">', html)
        self.assertNotIn("中国标准时间 · 本地个人项目管理", html)
        self.assertIn('id="project-status-dot"', html)
        self.assertIn('return project.progress_status || project.status || "unknown";', source)
        self.assertIn('data-source-tab="files"', source)
        self.assertIn('data-source-tab="manual"', source)
        self.assertLess(source.index('data-source-tab="manual"'), source.index('data-source-tab="files"'))
        self.assertIn('id="material-dropzone"', source)
        self.assertIn('dropzone.addEventListener("drop"', source)
        self.assertIn("setupMaterialDropzone();", source)
        self.assertIn("data-history-week=", source)
        self.assertIn("ontoggle=\"onHistoryReportToggle(this)\"", source)
        self.assertIn("async function onHistoryReportToggle(details)", source)
        self.assertIn('`/api/projects/${state.projectId}/reports/${encodeURIComponent(weekKey)}`', source)
        self.assertIn("body.dataset.loaded === \"1\"", source)
        self.assertIn("async function loadWorkspaceBusy(", source)
        self.assertIn('loadWorkspaceBusy("切换项目")', source)
        self.assertIn("if (shown) setBusy(false);", source)
        self.assertIn('class="switch"', source)
        self.assertIn("toggleRepo(", source)
        self.assertIn("data-schedule-enabled", source)

    def test_git_settings_save_sends_gitlab_url_and_skip_verify(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('payload.gitlab_url = $("gitlab-url-input")?.value.trim() || "";', source)
        self.assertIn('payload.gitlab_skip_verify = !!($("gitlab-skip-verify-input")?.checked);', source)

    def test_project_pause_switch_and_greyed_menu_entries(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("function projectPaused(p)", source)
        self.assertIn('${paused ? " paused" : ""}', source)
        self.assertIn('project-item-flag">已停用</small>', source)
        self.assertIn('if (project.status === "paused" || project.status === "archived") return project.status;', source)
        self.assertIn('paused: "已停用"', source)
        self.assertIn('id="project-enabled-input"', source)
        self.assertIn('payload.status = $("project-enabled-input")?.checked ? "active" : "paused";', source)
        self.assertNotIn('${input("status", "状态", p.status)}', source)
        self.assertIn("function syncProjectToggleState(input)", source)
        self.assertIn("已停用 · 不再自动生成周报", source)
        self.assertIn('panel-actions"><button class="primary" type="submit">保存设置</button>', source)
        self.assertIn('class="wide row settings-save-row"', source)
        self.assertIn(".project-row.paused .project-item strong {", styles)
        self.assertIn(".project-item-flag {", styles)
        self.assertIn(".project-toggle-row {", styles)
        self.assertIn(".project-toggle-state {", styles)
        self.assertIn(".settings-save-row button { width: 100%; }", styles)

    def test_voice_todo_fab_and_global_agent_setting(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('id="voice-todo-fab"', html)
        self.assertIn('id="voice-todo-live"', html)
        self.assertIn('id="voice-todo-progress"', html)
        self.assertIn('id="asr-endpoint-input"', html)
        self.assertIn('id="asr-model-input"', html)
        self.assertIn('id="asr-language-select"', html)
        self.assertIn('<option value="zh">中文</option>', html)
        self.assertIn('<option value="en">English</option>', html)
        self.assertIn('<option value="auto">自动检测</option>', html)
        self.assertIn('id="save-voice-settings"', html)
        self.assertIn("按住说话，创建语音 TODO", html)
        self.assertIn("setupVoiceTodoFab();", source)
        self.assertIn('fab.addEventListener("pointerdown", startVoiceHold)', source)
        self.assertIn('fab.addEventListener("pointerup", endVoiceHold)', source)
        self.assertIn('fab.addEventListener("pointercancel", cancelVoiceHold)', source)
        self.assertIn("navigator.mediaDevices.getUserMedia({ audio: true })", source)
        self.assertIn("new MediaRecorder(stream", source)
        self.assertNotIn("webkitSpeechRecognition", source)
        self.assertIn("audioBufferToWav16kMono(", source)
        self.assertIn("window.isSecureContext", source)
        self.assertIn('`https://${location.hostname}:8443`', source)
        self.assertIn('"/api/todos/voice"', source)
        self.assertIn('throw new Error(`服务响应异常（HTTP ${res.status}）: ${text.slice(0, 100) || "空响应"}`);', source)
        self.assertIn('throw new Error("网络请求失败，请检查网络连接后重试");', source)
        self.assertIn("voiceCancelInFlight", source)
        self.assertIn("`/api/voice-jobs/${id}`", source)
        self.assertIn('"/api/task-queue"', source)
        self.assertIn("`/api/voice-jobs/${id}/cancel`", source)
        self.assertIn("function updateVoiceFabMode()", source)
        self.assertIn("function restoreQueues()", source)
        self.assertIn("restoreQueues();", source)
        self.assertIn("VOICE_FAB_STOP_SVG", source)
        self.assertIn("function truncateVoiceTranscript", source)
        self.assertIn("cleaned.slice(0, 64)", source)
        self.assertIn(".voice-todo-fab.is-stopping {", styles)
        self.assertIn("asr_endpoint: $(\"asr-endpoint-input\")?.value || \"\"", source)
        self.assertIn('asr_language: $("asr-language-select")?.value || ""', source)
        self.assertIn('state.asrLanguage = data.asr_language || "zh";', source)
        self.assertIn('language.value = ["zh", "en", "auto"].includes(state.asrLanguage) ? state.asrLanguage : "zh";', source)
        self.assertIn("voiceFabSuppressClickUntil", source)
        self.assertIn("async function syncUiPreferencesToServer()", source)
        self.assertIn("ui_theme: state.theme, ui_mode: state.appearance", source)
        self.assertIn("if (data.ui_theme && THEMES.some((theme) => theme.id === data.ui_theme)) applyTheme(data.ui_theme, false);", source)
        self.assertIn("function renderVoiceSettings()", source)
        self.assertIn('id="llm-provider-select"', html)
        self.assertIn('id="llm-base-url-input"', html)
        self.assertIn('id="llm-model-input"', html)
        self.assertIn('id="llm-api-key-input"', html)
        self.assertIn('id="save-llm-settings"', html)
        self.assertIn("function renderLlmSettings()", source)
        self.assertIn("async function saveLlmSettings()", source)
        self.assertIn('state.llmApiKeySet = !!data.llm_api_key_set;', source)
        self.assertIn("if (keyInput && keyInput.value.trim()) payload.llm_api_key = keyInput.value.trim();", source)
        self.assertIn('key.placeholder = state.llmApiKeySet ? "已配置，留空保持不变" : "sk-...";', source)
        self.assertIn(".voice-todo-widget {", styles)
        self.assertIn(".voice-todo-fab {", styles)
        self.assertIn("padding: 0;", styles)
        self.assertIn(".voice-todo-fab.is-recording {", styles)
        self.assertIn(".voice-todo-live {", styles)
        self.assertIn(".voice-todo-progress {", styles)
        self.assertIn(".voice-job-transcript {", styles)
        self.assertIn(".voice-settings {", styles)

    def test_responsive_layout_contains_wide_content_overflow(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("ensureTableScrollContainers();", source)
        self.assertIn(".table-scroll {", styles)
        self.assertIn("overflow-x: auto;", styles)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", styles)
        self.assertIn("@media (max-width: 767px)", styles)
        self.assertIn(".status-strip, .form-grid, .schedule-row, .plan-item { grid-template-columns: 1fr; }", styles)

    def test_material_upload_supports_multiple_files_and_summary_editing(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        html = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('type="file" accept=".md,.markdown,.txt,.html,.htm,.pdf" multiple', html)
        self.assertIn("支持 Markdown、纯文本、HTML 和 PDF，可多选", source)
        self.assertIn('Array.from($("material-file").files || [])', source)
        self.assertIn('JSON.stringify({ files: payloads })', source)
        self.assertIn("updateMaterialSummary", source)

    def test_uploaded_and_manual_materials_open_shared_preview_dialog(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="material-preview-dialog"', html)
        self.assertGreaterEqual(source.count("previewMaterial(${m.id})"), 3)
        self.assertIn("async function previewMaterial(id)", source)
        self.assertIn("/materials/${id}`", source)
        self.assertIn('material.preview_kind === "pdf"', source)
        self.assertIn('material.preview_kind === "markdown"', source)
        self.assertIn('material.preview_kind === "html"', source)
        self.assertIn('frame.srcdoc = material.content_html || ""', source)
        self.assertIn('frame.setAttribute("sandbox", "")', source)
        self.assertIn('pdf.removeAttribute("srcdoc")', source)
        self.assertIn('pdf.removeAttribute("sandbox")', source)
        self.assertIn("material.content_html", source)
        self.assertIn("/materials/${id}/content`", source)
        self.assertIn('id="material-preview-pdf"', html)
        self.assertIn('id="material-preview-markdown"', html)
        self.assertIn('$("close-material-preview").onclick', source)

    def test_template_wand_controls_exist(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("wand: {", source)
        self.assertIn('${faIcon("wand")}', source)
        self.assertIn("function templateField(p)", source)
        self.assertIn('<textarea name="report_template">', source)
        self.assertIn('type="button" class="template-wand"', source)
        self.assertIn("async function suggestReportTemplate()", source)
        self.assertIn("/suggest-template", source)
        self.assertIn("模板生成失败", source)
        self.assertIn("模板生成结果为空", source)
        self.assertIn("模板已生成，保存设置后生效", source)
        self.assertIn(".template-wand {", styles)

    def test_suggest_report_template_fills_textarea_and_reports_errors(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
const testElements = new Map();
function testElement() {
  return {
    textContent: "",
    innerHTML: "",
    disabled: false,
    dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    showModal() { this.open = true; },
    close() { this.open = false; },
  };
}
const templateFieldEl = { value: "" };
globalThis.localStorage = { getItem() { return null; }, setItem() {} };
globalThis.document = {
  getElementById(id) {
    if (!testElements.has(id)) testElements.set(id, testElement());
    return testElements.get(id);
  },
  querySelector(selector) {
    return selector.includes("report_template") ? templateFieldEl : null;
  },
  querySelectorAll() { return []; },
};
globalThis.setTimeout = () => 0;
globalThis.window = {};
const responses = [];
const fetchCalls = [];
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  const body = responses.shift();
  if (body === undefined) throw new Error(`unexpected fetch: ${path}`);
  return {
    ok: true,
    text: async () => JSON.stringify(body),
    async json() { return body; },
  };
};
"""
        assertions = r"""
(async () => {
  render = () => {};
  const toasts = [];
  toast = (message) => { toasts.push(message); };
  state.projectId = 1;

  // posts the current content directly (no confirm gate) and fills the textarea
  templateFieldEl.value = "# Requirements";
  responses.push({ template: "# Generated" });
  await suggestReportTemplate();
  if (fetchCalls.length !== 1 || fetchCalls[0].path !== "/api/projects/1/suggest-template" || fetchCalls[0].options.method !== "POST") {
    throw new Error("did not POST to suggest-template");
  }
  if (!fetchCalls[0].options.body.includes('"requirements":"# Requirements"')) {
    throw new Error(`unexpected requirements payload: ${fetchCalls[0].options.body}`);
  }
  if (templateFieldEl.value !== "# Generated") {
    throw new Error("the generated template was not filled into the textarea");
  }
  if (!toasts.some((message) => message.includes("模板已生成"))) {
    throw new Error(`success toast missing: ${toasts.join("|")}`);
  }

  // an empty template payload must not wipe the textarea
  responses.push({ template: "   " });
  await suggestReportTemplate();
  if (templateFieldEl.value !== "# Generated") {
    throw new Error("an empty template result wiped the textarea");
  }
  if (!toasts.some((message) => message.includes("模板生成结果为空"))) {
    throw new Error(`empty-result toast missing: ${toasts.join("|")}`);
  }

  // API failures surface a visible toast and keep the current content
  globalThis.fetch = async () => { throw new Error("internal agent LLM call failed: boom"); };
  await suggestReportTemplate();
  if (templateFieldEl.value !== "# Generated") {
    throw new Error("a failed generation wiped the textarea");
  }
  // the api() wrapper maps network failures to a generic message; what matters
  // is that the failure is surfaced at all (server 400s pass through verbatim)
  if (!toasts.some((message) => message.includes("模板生成失败"))) {
    throw new Error(`failure toast missing: ${toasts.join("|")}`);
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
"""
        result = subprocess.run(
            ["node"],
            input=f"{harness}\n{source}\n{assertions}",
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_supplement_history_and_archive_supplement_controls_exist(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="supplement-history"', source)
        self.assertIn("ws.update_history", source)
        self.assertIn("该周补充", source)
        self.assertIn("data.supplement", source)
        self.assertIn("function supplementFieldsHtml(", source)
        self.assertIn("<h2>本周补充</h2>", source)
        self.assertIn("还没有历史补充。", source)

    def test_unlocked_materials_have_delete_controls(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('m.deletable ? `<button class="danger" onclick="deleteMaterial(${m.id})">删除</button>`', source)
        self.assertNotIn(">Open Report<", source)
        self.assertNotIn(">Save Settings<", source)
        self.assertNotIn(">Save Manual Material<", source)
        self.assertNotIn(">Remove</button>", source)
        self.assertIn('<button type="button" class="danger" onclick="this.closest(\'.plan-item\').remove()">移除</button>', source)
        self.assertGreaterEqual(source.count('onclick="deleteMaterial(${m.id})"'), 2)
        self.assertIn('method: "DELETE"', source)
        self.assertIn('window.confirm("确定删除这条资料？删除后无法恢复。")', source)
        self.assertIn("button.danger {", styles)

    def test_todo_board_is_separate_and_closure_collects_required_context(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('id="page-corner" class="page-corner"', html)
        self.assertIn('role="button" tabindex="0"', html)
        self.assertNotIn('<button id="page-corner"', html)
        self.assertIn('id="page-current-label"', html)
        self.assertIn('id="page-target-label"', html)
        self.assertIn('id="report-confirm-dialog" class="message-dialog"', html)
        self.assertIn('id="report-confirm-message"', html)
        self.assertLess(html.index('id="page-corner"'), html.index('<div class="app-shell">'))
        self.assertNotIn('id="new-todo"', html)
        self.assertNotIn('id="schedule-check"', html)
        self.assertNotIn('id="generate-report"', html)
        self.assertIn('id="todo-view" class="main hidden"', html)
        self.assertIn('id="todo-board"', html)
        self.assertIn('name="reason" required', html)
        self.assertIn('id="close-todo-project"', html)
        self.assertIn('function renderTodoBoard()', source)
        self.assertIn('function openCloseTodo(id)', source)
        self.assertIn('function renderTodoDraft()', source)
        self.assertIn('function renderTodoEditor(todo)', source)
        self.assertIn("if (!event.target.closest('a')) beginTodoEdit(", source)
        self.assertIn("event.key === 'Enter' && !event.target.closest('a')", source)
        self.assertIn('function finishTodoEdit(event, id)', source)
        self.assertIn('function saveTodoEditor(rawId)', source)
        self.assertIn('todo.description_html', source)
        self.assertIn('/api/todos/${id}/close', source)
        self.assertIn('function deleteTodo(id)', source)
        self.assertIn('async function runTodoDelete()', source)
        self.assertIn('$("todo-delete-dialog").showModal()', source)
        self.assertIn('id="todo-delete-dialog" class="message-dialog"', html)
        self.assertIn('id="todo-delete-title"', html)
        self.assertNotIn('确定删除这条已关闭', source)
        self.assertIn('`<button class="danger" onclick="event.stopPropagation(); deleteTodo(${todo.id})">删除</button>`', source)
        self.assertIn('function confirmProjectGeneration(projectId)', source)
        self.assertIn('function runConfirmedProjectGeneration()', source)
        self.assertIn('$("report-confirm-dialog").showModal()', source)
        self.assertNotIn('window.confirm(`要为', source)
        self.assertNotIn('onclick="generateReport()', source)
        self.assertNotIn('async function scheduleCheck()', source)
        self.assertIn('.page-corner {', styles)
        self.assertIn('--fold-size: 36px;', styles)
        self.assertIn('--fold-size: 104px;', styles)
        self.assertIn('transition: clip-path 360ms cubic-bezier(.25, .9, .3, 1);', styles)
        self.assertIn('.page-corner:hover,', styles)
        self.assertIn('calc(188px - var(--fold-size)) 0,', styles)
        self.assertIn('188px var(--fold-size)', styles)
        self.assertIn('calc(188px - var(--fold-size)) var(--fold-size)', styles)
        self.assertIn(':root[data-mode="dark"]', styles)
        self.assertIn("function applyAppearance(", source)
        self.assertIn('class="mode-option', html)
        self.assertIn('id="open-project-bar"', html)
        self.assertNotIn("open-project-sheet", html)
        self.assertNotIn("open-project-sheet", source)
        self.assertIn('id="mobile-tabbar"', html)
        self.assertIn('data-mode-tab="todos"', html)
        self.assertIn('data-mode-tab="reports"', html)
        self.assertIn('btn.dataset.modeTab === (settings ? "settings" : state.mode)', source)
        self.assertIn(".mobile-tabbar { display: none; }", styles)
        self.assertIn(".page-corner { display: none; }", styles)
        self.assertIn("#report-view .topbar { display: none; }", styles)
        self.assertNotIn('class="project-bar todo-bar"', html)
        self.assertIn(".project-heading p {", styles)
        self.assertIn("to { opacity: 1; transform: none; }", styles)
        self.assertIn('setTimeout(() => el.classList.remove("view-enter"), 320)', source)
        self.assertIn("border: 1px solid color-mix(in srgb, var(--accent) 55%, transparent);", styles)
        self.assertIn('id="settings-view"', html)
        self.assertIn('id="appearance-swatches"', html)
        self.assertIn('data-mode-tab="settings"', html)
        self.assertIn('id="open-global-settings"', html)
        self.assertIn("function toggleSettingsView(", source)
        self.assertIn("function syncWorkspaceView()", source)
        self.assertIn("renderAppearanceSettings();", source)
        self.assertNotIn('<h2>外观</h2>', source)
        self.assertIn('.page-corner.turning { animation: corner-peel 400ms', styles)
        self.assertIn('@media (prefers-reduced-motion: reduce)', styles)
        self.assertIn('function playPageTurn()', source)
        self.assertIn('filter: drop-shadow(-6px 7px 9px rgba(15, 23, 42, 0.28));', styles)
        self.assertIn('.todo-column-todo {', styles)
        self.assertIn('.todo-column-doing {', styles)
        self.assertIn('.todo-column-closed {', styles)
        self.assertIn('.message-box {', styles)
        self.assertNotIn("--board-canvas", styles)
        self.assertNotIn("--board-head-ink", styles)
        self.assertNotIn(".todo-mode .page-corner-fold", styles)
        self.assertIn("#todo-view { min-height: 100vh; background: var(--canvas); }", styles)
        self.assertIn("const THEMES = [", source)
        self.assertIn("function applyTheme(", source)
        self.assertIn('class="theme-swatch', source)
        self.assertIn(':root[data-theme="green"]', styles)
        self.assertIn(".tabs button.active {", styles)
        self.assertIn("background: var(--accent);", styles)
        self.assertIn('#todo-view { min-height: 100vh; background: var(--canvas); }', styles)
        self.assertIn('grid-template-columns: repeat(3, minmax(260px, 1fr));', styles)
        self.assertNotIn('scroll-snap-type: x mandatory;', styles)
        self.assertIn('.todo-column { flex: 0 0 calc(100% - 16px); margin-inline: 8px; }', styles)
        self.assertIn('function attachSwipeNav(', source)
        self.assertIn('attachSwipeNav(workspaceElement,', source)
        self.assertIn('attachSwipeNav($("todo-board"));', source)
        self.assertIn("const watchSnap = (target, deadline)", source)
        self.assertIn("watchdogRetries", source)
        self.assertNotIn("reduce ? 80 : 440", source, "the one-shot snap guard is replaced by the watchdog")
        self.assertGreaterEqual(styles.count("touch-action: pan-y;"), 2)
        self.assertIn('el._pageSnapPending = target;', source)
        self.assertIn('if (state.tab !== name) state.tab = name;', source)
        self.assertIn('workspace._pageSnapPending = undefined;', source)
        self.assertIn('board._pageSnapPending = undefined;', source)
        self.assertIn('board.scrollLeft = Math.round(savedScrollLeft / pageWidth) * pageWidth;', source)
        self.assertIn('.todo-mode .app-shell { grid-template-columns: minmax(0, 1fr); }', styles)
        self.assertIn('function ensureWorkspaceDots()', source)
        self.assertIn('dots.id = "workspace-dots";', source)
        self.assertIn("function syncWorkspacePager(", source)
        self.assertIn("workspace.tabPagerIndex = panels.indexOf(el);", source)
        self.assertIn(".pager-dots { display: none; }", styles)
        self.assertIn(".pager-dots, .todo-board-dots {", styles)
        self.assertIn("position: fixed;", styles)
        self.assertIn("transition: height 240ms ease;", styles)

    def test_todo_inline_editor_creates_and_updates_on_auto_save(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
const testElements = new Map();
function testElement() {
  return {
    value: "",
    textContent: "",
    disabled: false,
    dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    setAttribute() {},
    focus() {},
  };
}
globalThis.localStorage = { getItem() { return null; }, setItem() {} };
globalThis.document = {
  body: testElement(),
  activeElement: null,
  getElementById(id) {
    if (!testElements.has(id)) testElements.set(id, testElement());
    return testElements.get(id);
  },
  querySelectorAll() { return []; },
};
globalThis.setTimeout = (callback) => { callback(); return 0; };
globalThis.requestAnimationFrame = (callback) => callback();
const fetchCalls = [];
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  const payload = JSON.parse(options.body);
  const body = { todos: [{ id: 7, title: payload.title, description: payload.description, status: payload.status || "todo" }] };
  return {
    ok: true,
    text: async () => JSON.stringify(body),
    async json() {
      return body;
    },
  };
};
"""
        assertions = r"""
(async () => {
  renderTodoBoard = () => {};
  toast = () => {};
  state.todoEditorId = "draft";
  $("todo-editor-title-draft").value = "Draft title";
  $("todo-editor-description-draft").value = "**Markdown** body";
  await saveTodoEditor("draft");
  if (fetchCalls[0].path !== "/api/todos" || fetchCalls[0].options.method !== "POST") {
    throw new Error("draft card did not create through POST");
  }
  state.todoEditorId = 7;
  $("todo-editor-title-7").value = "Updated title";
  $("todo-editor-description-7").value = "- updated";
  await saveTodoEditor("7");
  if (fetchCalls[1].path !== "/api/todos/7" || fetchCalls[1].options.method !== "PUT") {
    throw new Error("existing card did not update through PUT");
  }
  const updatePayload = JSON.parse(fetchCalls[1].options.body);
  if (updatePayload.status !== "todo" || updatePayload.description !== "- updated") {
    throw new Error("existing card auto-save lost status or Markdown source");
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
"""
        result = subprocess.run(
            ["node"],
            input=f"{harness}\n{source}\n{assertions}",
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_generate_report_submits_async_and_polls_task_queue(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
const testElements = new Map();
function testElement() {
  return {
    textContent: "",
    innerHTML: "",
    disabled: false,
    dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    showModal() { this.open = true; },
    close() { this.open = false; },
  };
}
globalThis.localStorage = { getItem() { return null; }, setItem() {} };
globalThis.document = {
  getElementById(id) {
    if (!testElements.has(id)) testElements.set(id, testElement());
    return testElements.get(id);
  },
  querySelectorAll() { return []; },
};
globalThis.setTimeout = () => 0;
globalThis.setInterval = () => 7;
globalThis.clearInterval = () => {};
globalThis.window = { confirm() { return false; } };
const responses = [];
const fetchCalls = [];
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  const body = responses.shift();
  if (body === undefined) throw new Error(`unexpected fetch: ${path}`);
  const payload = typeof body === "function" ? body() : body;
  return {
    ok: true,
    text: async () => JSON.stringify(payload),
    async json() { return payload; },
  };
};
"""
        assertions = r"""
(async () => {
  const extractedSummary = reportSummary({
    content_md: "# Weekly Report\n\n## 本周总结\n完成核心流程，并修复预览问题。\n\n## 下周计划\n继续验证。",
  });
  if (extractedSummary !== "完成核心流程，并修复预览问题。") {
    throw new Error(`unexpected report summary: ${extractedSummary}`);
  }
  render = () => {};
  toast = () => {};
  state.projectId = 1;
  const runningQueue = {
    capacity: 5,
    parallelism: 2,
    active: 1,
    tasks: [{ kind: "report", id: 9, project_id: 1, project_name: "Demo", week_key: "2026-W36", trigger_type: "manual", status: "running" }],
  };
  const emptyQueue = { capacity: 5, parallelism: 2, active: 0, tasks: [] };
  const finishedWorkspace = {
    project: { id: 1, name: "Demo" },
    jobs: [{ id: 9, status: "success" }],
    report: { content_html: "<h1>Fresh report</h1>" },
  };
  responses.push(
    { id: 9, status: "queued" },
    runningQueue,
    emptyQueue,
    finishedWorkspace,
  );

  await generateReport();

  if (fetchCalls[0].path !== "/api/projects/1/generate" || fetchCalls[0].options.method !== "POST") {
    throw new Error("generation did not POST to the generate endpoint");
  }
  if (!reportJobs.get(9) || reportJobs.get(9).projectId !== 1) {
    throw new Error("submitting generation did not track the queued job");
  }
  if (queuePollTimer === 0) {
    throw new Error("submitting generation did not start queue polling");
  }

  await pollTaskQueue();
  if (reportJobs.get(9).status !== "running") {
    throw new Error("polling did not adopt the running status");
  }
  if (fetchCalls.length !== 2) {
    throw new Error("a running task must not trigger a workspace refresh");
  }

  await pollTaskQueue();
  if (reportJobs.size !== 0) {
    throw new Error("the completed job stayed tracked after leaving the queue");
  }
  if (fetchCalls.length !== 4) {
    throw new Error(`expected task-queue poll then workspace refresh, saw ${fetchCalls.map((c) => c.path).join(",")}`);
  }
  if (fetchCalls[3].path !== "/api/projects/1/workspace") {
    throw new Error(`unexpected completion request: ${fetchCalls[3].path}`);
  }
  if (!state.workspace || state.workspace.project.id !== 1 || state.workspace.report.content_html !== finishedWorkspace.report.content_html) {
    throw new Error("the finished workspace was not adopted");
  }
  if (queuePollTimer !== 0) {
    throw new Error("polling did not stop after the queue drained");
  }

  state.projects = [{ id: 1, name: "Demo" }];
  confirmProjectGeneration(1);
  if (state.pendingReportProjectId !== 1 || !$("report-confirm-dialog").open) {
    throw new Error("project-row generation did not open the app message box");
  }
  responses.push({ id: 10, status: "queued" });
  await runConfirmedProjectGeneration();
  const generateCalls = fetchCalls.filter((call) => call.path === "/api/projects/1/generate");
  if (generateCalls.length !== 2) {
    throw new Error("confirmed project-row generation did not start");
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
"""
        result = subprocess.run(
            ["node"],
            input=f"{harness}\n{source}\n{assertions}",
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_task_queue_settings_and_progress_bubble(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('id="queue-capacity-input"', html)
        self.assertIn('id="queue-parallelism-input"', html)
        self.assertIn('id="save-queue-settings"', html)
        self.assertIn('id="task-queue-progress"', html)
        self.assertIn("function renderQueueSettings()", source)
        self.assertIn("async function saveQueueSettings()", source)
        self.assertIn('queue_capacity: Number($("queue-capacity-input")?.value)', source)
        self.assertIn('queue_parallelism: Number($("queue-parallelism-input")?.value)', source)
        self.assertIn("state.queueCapacity = data.queue_capacity;", source)
        self.assertIn("state.queueParallelism = data.queue_parallelism;", source)
        self.assertIn("state.queueCapacity = data.queue_capacity || 5;", source)
        self.assertIn("state.queueParallelism = data.queue_parallelism || 2;", source)
        self.assertIn("renderQueueSettings();", source)
        self.assertIn('$("save-queue-settings").onclick', source)
        self.assertIn("function renderQueueProgress(data)", source)
        self.assertIn("排队等待中…", source)
        self.assertIn("task queue is full", source)
        self.assertIn("排队中", source)
        self.assertIn("已跳过", source)
        self.assertIn(".task-queue-progress {", styles)
        self.assertIn(".queue-task-line {", styles)
        self.assertIn(".status.queued {", styles)
        self.assertIn(".status.running {", styles)


if __name__ == "__main__":
    unittest.main()

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
        self.assertIn('<span class="status">read-only</span></summary>', source)
        self.assertNotIn("</button></summary>", source)
        self.assertIn("onclick=\"exportReportPdf(", source)
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
        self.assertNotIn('type="submit">保存设置</button>', source)
        self.assertNotIn('settings-save-row', source)
        self.assertIn('setupAutoSave("project-settings", $("settings-form"), saveSettings);', source)
        self.assertIn('修改后自动保存', source)
        self.assertIn(".project-row.paused .project-item strong {", styles)
        self.assertIn(".project-item-flag {", styles)
        self.assertIn(".project-toggle-row {", styles)
        self.assertIn(".project-toggle-state {", styles)
        self.assertIn(".autosave-status {", styles)
        self.assertIn(".autosave-status.is-error {", styles)

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
        self.assertNotIn('id="save-voice-settings"', html)
        self.assertIn('id="voice-settings-panel"', html)
        self.assertIn('setupAutoSave("voice-settings", $("voice-settings-panel"), saveVoiceSettings);', source)
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
        self.assertNotIn('id="save-llm-settings"', html)
        self.assertIn('id="llm-settings-panel"', html)
        self.assertIn('setupAutoSave("llm-settings", $("llm-settings-panel"), saveLlmSettings);', source)
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
        # 新增手工资料走显式「添加资料」按钮，不走自动保存
        self.assertIn('onclick="addManualMaterial()"', source)
        self.assertIn("async function addManualMaterial()", source)
        self.assertNotIn("manual-material-draft", source)

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
        self.assertIn('type="button" id="template-wand-btn" class="template-wand"', source)
        self.assertIn("async function suggestReportTemplate()", source)
        self.assertIn("/suggest-template", source)
        self.assertIn("模板生成任务已提交，完成后自动保存", source)
        self.assertIn("function templateJobPending(", source)
        self.assertIn('id="template-field-hint"', source)
        self.assertIn('id="template-wand-btn"', source)
        self.assertIn("模板生成中，完成后自动保存并刷新", source)
        self.assertIn('task.kind === "report" || task.kind === "template"', source)
        self.assertIn("模板 · ", source)
        self.assertIn("模板生成任务提交失败", source)
        self.assertIn("async function templateJobFinished(", source)
        self.assertIn("周报模板已生成并保存", source)
        self.assertIn("生成后自动保存", source)
        self.assertIn(".template-wand {", styles)

    def test_suggest_report_template_submits_async_and_autosaves(self):
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
  addEventListener() {},
  removeEventListener() {},
};
globalThis.setTimeout = () => 0;
globalThis.window = { addEventListener() {}, removeEventListener() {} };
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

  templateFieldEl.value = "# Requirements";
  responses.push({ id: 77, status: "queued" });
  await suggestReportTemplate();
  if (fetchCalls.length !== 1 || fetchCalls[0].path !== "/api/projects/1/suggest-template" || fetchCalls[0].options.method !== "POST") {
    throw new Error("did not POST to suggest-template");
  }
  if (!fetchCalls[0].options.body.includes('"requirements":"# Requirements"')) {
    throw new Error(`unexpected requirements payload: ${fetchCalls[0].options.body}`);
  }
  const tracked = reportJobs.get(77);
  if (!tracked || tracked.kind !== "template" || tracked.projectId !== 1) {
    throw new Error("the queued template job was not tracked");
  }
  if (!toasts.some((message) => message.includes("模板生成任务已提交"))) {
    throw new Error(`submit toast missing: ${toasts.join("|")}`);
  }

  // polling adopts the running task and completes through the workspace fetch
  responses.push({ active: 1, tasks: [{ kind: "template", id: 77, project_id: 1, status: "running" }] });
  await pollTaskQueue();
  if (reportJobs.get(77).status !== "running") {
    throw new Error("polling did not adopt the running template task");
  }
  responses.push({ active: 0, tasks: [] });
  responses.push({ project: { id: 1, name: "Demo" }, jobs: [], template_job: { id: 77, status: "success" } });
  await pollTaskQueue();
  if (reportJobs.has(77)) {
    throw new Error("the finished template job stayed tracked");
  }
  if (!toasts.some((message) => message.includes("周报模板已生成并保存"))) {
    throw new Error(`success toast missing: ${toasts.join("|")}`);
  }

  // a failed template job reports the recorded failure reason
  responses.push({ id: 78, status: "queued" });
  await suggestReportTemplate();
  responses.push({ active: 0, tasks: [] });
  responses.push({ project: { id: 1, name: "Demo" }, jobs: [], template_job: { id: 78, status: "failed", failure_reason: "模板生成失败：provider down" } });
  await pollTaskQueue();
  if (!toasts.some((message) => message.includes("模板生成失败") && message.includes("provider down"))) {
    throw new Error(`failure toast missing: ${toasts.join("|")}`);
  }

  // submit failures surface a visible toast instead of failing silently
  globalThis.fetch = async () => { throw new Error("boom"); };
  await suggestReportTemplate();
  if (!toasts.some((message) => message.includes("模板生成任务提交失败"))) {
    throw new Error(`submit-failure toast missing: ${toasts.join("|")}`);
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
        self.assertIn('<button type="button" class="danger" onclick="this.closest(\'.plan-item\').remove(); touchAutoSave(\'plan\')">移除</button>', source)
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

    def test_todo_board_supports_drag_reorder_across_lanes(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        # 卡片带稳定 id 锚点，列带 lane 锚点，拖拽落点靠它们读取
        self.assertIn('data-todo-id="${todo.id}"', source)
        self.assertIn('data-lane="${column.status}"', source)
        self.assertIn('ondragstart="return false"', source)
        # 拖拽期间整板重绘会让被拖卡片从 DOM 消失
        self.assertIn("if (todoDrag.active || todoDrag.armed) return;", source)
        self.assertIn("function setupTodoBoardDrag(", source)
        self.assertLess(source.index('attachSwipeNav($("todo-board"));'), source.index("setupTodoBoardDrag();"))
        # 拖拽时看板滑动翻页必须让位
        self.assertIn("if (el._todoDragActive)", source)
        # 触屏长按抬卡；桌面按住移动即拖
        self.assertIn('todoDrag.longPressTimer = setTimeout(() => beginTodoDrag(), 240);', source)
        self.assertIn("/api/todos/reorder", source)
        self.assertIn('body: JSON.stringify({ lanes })', source)
        # 已关闭列只接受列内重排，未关闭卡片不能拖入
        self.assertIn('todoDrag.fromLane === "closed" ? ["closed"] : ["todo", "doing"]', source)
        # 手机分页下拖到边缘自动横向翻页，落点列吸附回正
        self.assertIn("function autoScrollTodoBoard()", source)
        self.assertIn("board.scrollLeft = laneIndex * board.clientWidth;", source)
        # 拖拽失败回滚到服务端顺序
        self.assertIn("toast(error.message);\n      loadTodos();", source)
        self.assertIn(".todo-card-armed {", styles)
        self.assertIn(".todo-card-lifted {", styles)
        self.assertIn(".todo-card-ghost {", styles)
        self.assertIn("body.todo-drag-in-progress {", styles)
        self.assertIn("cursor: grab;", styles)
        self.assertIn("-webkit-touch-callout: none;", styles)

    def test_todo_drag_moves_cards_within_and_across_lanes(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
function makeClassList() {
  const set = new Set();
  return {
    add: (...names) => names.forEach((name) => set.add(name)),
    remove: (...names) => names.forEach((name) => set.delete(name)),
    toggle: () => {},
    contains: (name) => set.has(name),
  };
}
function insertEl(parent, child, ref) {
  if (child.parentNode && child.parentNode !== parent) {
    const old = child.parentNode.children.indexOf(child);
    if (old >= 0) child.parentNode.children.splice(old, 1);
    child.parentNode.children.forEach((c, i) => { c._next = child.parentNode.children[i + 1] || null; });
  }
  const at = parent.children.indexOf(child);
  if (at >= 0) parent.children.splice(at, 1);
  child.parentNode = parent;
  const idx = ref ? parent.children.indexOf(ref) : parent.children.length;
  parent.children.splice(idx, 0, child);
  parent.children.forEach((c, i) => { c._next = parent.children[i + 1] || null; });
}
function makeEl(name, rect) {
  return {
    _name: name,
    _handlers: {},
    dataset: {},
    style: {},
    children: [],
    parentNode: null,
    _next: null,
    getBoundingClientRect: () => rect,
    classList: makeClassList(),
    appendChild(child) { insertEl(this, child, null); },
    insertBefore(child, ref) { insertEl(this, child, ref); },
    remove() { if (this.parentNode) insertEl(this.parentNode, this, this); },
    removeAttribute() {},
    cloneNode() { return makeEl(`${name}-ghost`, rect); },
    closest(selector) {
      let cur = this;
      while (cur) {
        if (selector === ".todo-column" && cur._isColumn) return cur;
        if (selector === ".todo-card-list" && cur._isList) return cur;
        if (selector === ".todo-card[data-todo-id]" && cur._isCard) return cur;
        if (selector === "button, a, input, textarea, [data-todo-editor]" && cur._isInteractive) return cur;
        cur = cur.parentNode;
      }
      return null;
    },
    querySelector(selector) {
      if (selector === ".todo-card-list") return this.children.find((c) => c._isList) || null;
      if (selector === ".todo-draft, .todo-empty") return this.children.find((c) => c._isDraft || c._isEmpty) || null;
      return null;
    },
    querySelectorAll(selector) {
      const collect = (el, pred) => {
        const found = [];
        for (const child of el.children) {
          if (pred(child)) found.push(child);
          found.push(...collect(child, pred));
        }
        return found;
      };
      if (selector === ".todo-card[data-todo-id]") return collect(this, (c) => c._isCard);
      if (selector === ".todo-column") return collect(this, (c) => c._isColumn);
      return [];
    },
    addEventListener(type, handler) { this._handlers[type] = handler; },
  };
}
const cardIds = (el) => el.children.filter((c) => c._isCard).map((c) => c.dataset.todoId);

const columns = {};
const laneBounds = { todo: [0, 320], doing: [320, 640], closed: [640, 960] };
for (const lane of ["todo", "doing", "closed"]) {
  const column = makeEl(`column-${lane}`, { left: laneBounds[lane][0], top: 0, right: laneBounds[lane][1], bottom: 900 });
  column._isColumn = true;
  column.dataset.lane = lane;
  const list = makeEl(`list-${lane}`, { left: laneBounds[lane][0], top: 40, right: laneBounds[lane][1], bottom: 900 });
  list._isList = true;
  column.appendChild(list);
  columns[lane] = { column, list };
}
const draft = makeEl("draft", { left: 0, top: 300, right: 320, bottom: 380 });
draft._isDraft = true;
const emptyNote = makeEl("empty", { left: 640, top: 60, right: 960, bottom: 100 });
emptyNote._isEmpty = true;
function makeCard(id, rect) {
  const card = makeEl(`card-${id}`, rect);
  card._isCard = true;
  card.dataset.todoId = String(id);
  return card;
}
const cardA = makeCard(1, { left: 0, top: 60, right: 320, bottom: 140 });
const cardB = makeCard(2, { left: 0, top: 150, right: 320, bottom: 230 });
const cardC = makeCard(3, { left: 320, top: 60, right: 640, bottom: 140 });
const cardD = makeCard(4, { left: 640, top: 60, right: 960, bottom: 140 });
columns.todo.list.appendChild(cardA);
columns.todo.list.appendChild(cardB);
columns.todo.list.appendChild(draft);
columns.doing.list.appendChild(cardC);
columns.closed.list.appendChild(cardD);
columns.closed.list.appendChild(emptyNote);

const board = makeEl("board", { left: 0, top: 0, right: 960, bottom: 900 });
board.scrollWidth = 960;
board.clientWidth = 960;
board.scrollLeft = 0;
for (const lane of ["todo", "doing", "closed"]) board.appendChild(columns[lane].column);

const elements = new Map([["todo-board", board]]);
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.document = {
  body: makeEl("body", { left: 0, top: 0, right: 960, bottom: 900 }),
  getElementById: (id) => elements.get(id) || null,
  querySelectorAll: () => [],
  addEventListener() {},
  removeEventListener() {},
  scrollingElement: { scrollTop: 0 },
};
globalThis.window = {
  innerHeight: 900,
  _handlers: {},
  addEventListener(type, handler) { (this._handlers[type] = this._handlers[type] || []).push(handler); },
  removeEventListener(type, handler) { this._handlers[type] = (this._handlers[type] || []).filter((h) => h !== handler); },
};
globalThis.navigator = {};
const rafQueue = [];
globalThis.requestAnimationFrame = (callback) => rafQueue.push(callback);
globalThis.cancelAnimationFrame = () => {};
globalThis.setTimeout = () => 0;
globalThis.clearTimeout = () => {};
const fetchCalls = [];
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  return { ok: true, text: async () => JSON.stringify({ todos: [] }), json: async () => ({ todos: [] }) };
};
const pump = () => rafQueue.splice(0).forEach((callback) => callback());
const pointerEvent = (type, x, y, target) => ({
  pointerId: 1, pointerType: "mouse", button: 0, clientX: x, clientY: y, target,
  preventDefault() {},
});
const fire = (type, event) => {
  const boardHandler = board._handlers[type];
  if (boardHandler) boardHandler(event);
  for (const handler of [...(globalThis.window._handlers[type] || [])]) handler(event);
};
"""
        assertions = r"""
(async () => {
  renderTodoBoard = () => {};
  toast = () => {};
  state.todos = [
    { id: 1, title: "A", status: "todo", position: 0 },
    { id: 2, title: "B", status: "todo", position: 1 },
    { id: 3, title: "C", status: "doing", position: 0 },
    { id: 4, title: "D", status: "closed", position: 0 },
  ];
  setupTodoBoardDrag();

  // 桌面鼠标：按住待办卡片 A 向下移动即抬起
  fire("pointerdown", pointerEvent("pointerdown", 160, 100, cardA));
  fire("pointermove", pointerEvent("pointermove", 160, 250, cardA));
  if (!todoDrag.active) throw new Error("mouse drag did not lift the card");
  // 仍在「待办」列内：A 应排到 B 之后、草稿卡片之前
  pump();
  if (cardIds(columns.todo.list).join() !== "2,1") {
    throw new Error(`same-lane reorder failed: ${cardIds(columns.todo.list)}`);
  }
  // 指针进入「进行中」列且低于 C 的中点：A 应跨列排在 C 之后
  fire("pointermove", pointerEvent("pointermove", 500, 200, cardA));
  pump();
  if (cardA.parentNode !== columns.doing.list) throw new Error("card did not cross into the doing lane");
  if (cardIds(columns.doing.list).join() !== "3,1") {
    throw new Error(`cross-lane order wrong: ${cardIds(columns.doing.list)}`);
  }
  fire("pointerup", pointerEvent("pointerup", 500, 200, cardA));
  if (fetchCalls.length !== 1 || fetchCalls[0].path !== "/api/todos/reorder") {
    throw new Error(`expected reorder POST, got ${JSON.stringify(fetchCalls)}`);
  }
  const lanes = JSON.parse(fetchCalls[0].options.body).lanes;
  if (JSON.stringify(lanes) !== JSON.stringify({ todo: [2], doing: [3, 1], closed: [4] })) {
    throw new Error(`unexpected lanes payload: ${JSON.stringify(lanes)}`);
  }
  if (JSON.stringify(state.todos.map((t) => t.id)) !== "[2,3,1,4]") {
    throw new Error(`optimistic state wrong: ${JSON.stringify(state.todos.map((t) => t.id))}`);
  }
  if (todoDrag.active) throw new Error("drag state leaked after drop");

  // 已关闭卡片：拖到「待办」列上方也不得离开「已关闭」列
  fire("pointerdown", pointerEvent("pointerdown", 800, 100, cardD));
  fire("pointermove", pointerEvent("pointermove", 800, 260, cardD));
  if (!todoDrag.active) throw new Error("closed card drag did not lift");
  fire("pointermove", pointerEvent("pointermove", 160, 250, cardD));
  pump();
  if (cardD.parentNode !== columns.closed.list) throw new Error("closed card left the closed lane");
  fire("pointerup", pointerEvent("pointerup", 160, 250, cardD));
  const closedLanes = JSON.parse(fetchCalls[1].options.body).lanes;
  if (closedLanes.closed[0] !== 4 || closedLanes.todo.includes(4)) {
    throw new Error(`closed lane payload wrong: ${JSON.stringify(closedLanes)}`);
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

    def test_settings_autosave_skips_untouched_forms_and_saves_edits(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
function makeClassList() {
  const set = new Set();
  return {
    add: (...names) => names.forEach((name) => set.add(name)),
    remove: (...names) => names.forEach((name) => set.delete(name)),
    toggle: (name, force) => {
      const target = force === undefined ? !set.has(name) : force;
      if (target) set.add(name); else set.delete(name);
    },
    contains: (name) => set.has(name),
  };
}
const capacityField = { id: "queue-capacity-input", value: "5" };
const parallelField = { id: "queue-parallelism-input", value: "2" };
const statusEl = { textContent: "", classList: makeClassList() };
const panel = {
  _handlers: {},
  addEventListener(type, handler) { (this._handlers[type] = this._handlers[type] || []).push(handler); },
  querySelector(selector) { return selector === ".autosave-status" ? statusEl : null; },
  querySelectorAll(selector) {
    if (selector === "input, textarea, select") return [capacityField, parallelField];
    return [];
  },
  contains: () => false,
};
const elements = new Map([
  ["queue-settings-panel", panel],
  ["queue-capacity-input", capacityField],
  ["queue-parallelism-input", parallelField],
]);
globalThis.document = {
  getElementById: (id) => elements.get(id) || null,
  querySelectorAll: () => [],
  querySelector: () => null,
  addEventListener() {},
  removeEventListener() {},
};
globalThis.localStorage = { getItem: () => null, setItem: () => {} };
globalThis.window = { addEventListener() {}, removeEventListener() {} };
const timers = [];
globalThis.setTimeout = (callback) => { timers.push(callback); return timers.length; };
globalThis.clearTimeout = () => {};
const pump = () => timers.splice(0).forEach((callback) => callback());
const fire = (type, event) => { for (const handler of panel._handlers[type] || []) handler(event); };
const fetchCalls = [];
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  return {
    ok: true,
    text: async () => JSON.stringify({ queue_capacity: JSON.parse(options.body).queue_capacity, queue_parallelism: 2 }),
    json: async () => ({ queue_capacity: JSON.parse(options.body).queue_capacity, queue_parallelism: 2 }),
  };
};
"""
        assertions = r"""
(async () => {
  toast = () => {};
  setupAutoSave("queue-settings", panel, saveQueueSettings);

  // 没有任何编辑时失焦不产生请求
  fire("focusout", {});
  pump();
  pump();
  if (fetchCalls.length !== 0) {
    throw new Error(`untouched form should not save, got ${JSON.stringify(fetchCalls)}`);
  }

  // 输入过程（input）不落盘，失焦（change）才保存
  capacityField.value = "7";
  fire("input", {});
  pump();
  if (fetchCalls.length !== 0) {
    throw new Error(`typing alone should not save, got ${JSON.stringify(fetchCalls)}`);
  }
  fire("change", {});
  pump();
  if (fetchCalls.length !== 1 || fetchCalls[0].path !== "/api/settings") {
    throw new Error(`expected one settings PUT, got ${JSON.stringify(fetchCalls)}`);
  }
  if (JSON.parse(fetchCalls[0].options.body).queue_capacity !== 7) {
    throw new Error(`unexpected payload: ${fetchCalls[0].options.body}`);
  }

  // 保存后再次失焦：快照一致，不重复保存
  fire("focusout", {});
  pump();
  pump();
  if (fetchCalls.length !== 1) throw new Error("clean form re-saved on blur");

  // 非法输入报错且不发请求
  capacityField.value = "abc";
  fire("change", {});
  pump();
  for (let i = 0; i < 10; i++) {
    await new Promise((resolve) => timers.push(resolve));
    pump();
    await Promise.resolve();
  }
  if (fetchCalls.length !== 1) throw new Error("invalid number should not PUT");
  if (!statusEl.classList.contains("is-error")) throw new Error("invalid input did not surface an error status");
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
  addEventListener() {},
  removeEventListener() {},
};
globalThis.window = { addEventListener() {}, removeEventListener() {} };
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
  addEventListener() {},
  removeEventListener() {},
};
globalThis.setTimeout = () => 0;
globalThis.setInterval = () => 7;
globalThis.clearInterval = () => {};
globalThis.window = { confirm() { return false; }, addEventListener() {}, removeEventListener() {} };
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
        self.assertNotIn('id="save-queue-settings"', html)
        self.assertIn('id="queue-settings-panel"', html)
        self.assertIn('id="task-queue-progress"', html)
        self.assertIn("function renderQueueSettings()", source)
        self.assertIn("async function saveQueueSettings()", source)
        self.assertIn("queue_capacity: capacity,", source)
        self.assertIn("queue_parallelism: parallelism,", source)
        self.assertIn('setupAutoSave("queue-settings", $("queue-settings-panel"), saveQueueSettings);', source)
        self.assertIn("state.queueCapacity = data.queue_capacity;", source)
        self.assertIn("state.queueParallelism = data.queue_parallelism;", source)
        self.assertIn("state.queueCapacity = data.queue_capacity || 5;", source)
        self.assertIn("state.queueParallelism = data.queue_parallelism || 2;", source)
        self.assertIn("renderQueueSettings();", source)
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

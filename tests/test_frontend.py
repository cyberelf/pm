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
        self.assertLess(html.index('data-tab="report"'), html.index('data-tab="settings"'))
        # 计划和风险 moved into the 工作线 tab
        self.assertNotIn('data-tab="plan"', html)
        self.assertNotIn('id="tab-plan"', html)
        self.assertIn('data-project-settings=', source)
        self.assertIn('data-project-generate=', source)
        self.assertIn('switchTab("settings")', source)
        self.assertNotIn("function switchPlanSubTab(", source)
        self.assertIn("function renderWorkstreamPlan(", source)
        self.assertIn("function renderWorkstreamRisks(", source)
        self.assertIn("function switchSettingsSubTab(", source)
        self.assertIn('data-subtab="diagnostics"', source)
        self.assertIn('id="settings-sub-diagnostics"', source)
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

    def test_repo_row_branch_selection_has_visible_autosave_feedback(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        # 分支行内要有保存状态元素（否则 setAutoSaveStatus 静默空跑，勾选分支看起来像没保存）
        self.assertIn('${renderBranchPicker(r)}<div class="autosave-status" aria-live="polite"></div>` : `<span>${escapeHtml(trackedBranchSummary(r))}</span>`}', source)
        # 保存成功后同步 picker 摘要与已选分支
        self.assertIn('summary.textContent = branches.includes(TRACK_ALL_BRANCHES) ? "All" : branches.join(", ")', source)
        # 编辑完全回退时清除残留的失败提示
        self.assertIn('if (status && status.classList.contains("is-error")) setAutoSaveStatus(root, "idle")', source)

    def test_project_sharing_ui_roles_and_owner_share_panel(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        # 角色判定助手：owner > manage > write > read，共享项目行带角色徽标
        self.assertIn('const SHARE_ROLE_LABELS = { owner: "所有者", read: "只读", write: "读写", manage: "管理" }', source)
        self.assertIn("function projectRoleOf(p)", source)
        self.assertIn("function projectCanWrite(p)", source)
        self.assertIn("function projectCanManage(p)", source)
        self.assertIn("function canWriteWorkspace()", source)
        self.assertIn("function canManageWorkspace()", source)
        self.assertIn("function isProjectOwner()", source)
        self.assertIn("共享 · ${SHARE_ROLE_LABELS[projectRoleOf(p)]}", source)
        # 侧栏入口按角色裁剪：只读没有生成/设置按钮
        self.assertIn("${projectCanWrite(p) ? `\n      <button class=\"project-generate\"", source)
        self.assertIn("${projectCanManage(p) ? `", source)
        self.assertIn('data-project-settings="${p.id}"', source)
        # 顶部项目元信息标注共享来源与权限
        self.assertIn("共享 · ${SHARE_ROLE_LABELS[wsRole]}权限", source)
        # 设置页：无管理权限时停用整个表单（停用控件不触发自动保存）
        self.assertIn('if (!manage) {\n    $("settings-form").querySelectorAll("input, textarea, select, button").forEach((el) => { el.disabled = true; });\n  }', source)
        # 共享管理子页仅 owner 可见，切换到该页时拉取共享列表
        self.assertIn('data-subtab="sharing"', source)
        self.assertIn('id="settings-sub-sharing"', source)
        self.assertIn('if (tab === "sharing" && isProjectOwner()) {\n    loadProjectShares();\n    loadShareCandidates();\n  }', source)
        self.assertIn('id="share-table-body"', source)
        # 添加成员：账号下拉（来自 candidates 接口），不再是手输用户名
        self.assertIn('id="share-user-select"', source)
        self.assertNotIn('id="share-username-input"', source)
        self.assertIn("`/api/projects/${state.projectId}/shares/candidates`", source)
        self.assertIn("function renderShareUserOptions()", source)
        self.assertIn("async function loadShareCandidates()", source)
        self.assertIn('id="share-role-select"', source)
        self.assertIn("`/api/projects/${state.projectId}/shares`", source)
        self.assertIn("`/api/projects/${state.projectId}/shares/${userId}`", source)
        self.assertIn("async function addProjectShare()", source)
        self.assertIn("async function changeShareRole(userId, role)", source)
        self.assertIn("async function removeProjectShare(userId)", source)
        # 关闭 TODO 归档下拉只列出可写项目
        self.assertIn("state.projects.filter(projectCanWrite)", source)
        # 周报编辑按钮需要写权限
        self.assertIn("${canWriteWorkspace() ? `<button onclick=\"openReportEditor()\">编辑</button>` : \"\"}", source)

    def test_repo_fetch_flags_cover_repo_and_org_projects_github_only(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        # 仓库 Project 与组织 Project 都是 GitHub 专属开关；GitLab 没有看板
        self.assertIn('["fetch_repo_projects", "Project", "抓取仓库自己的 GitHub Projects 看板", "github"]', source)
        self.assertIn('["fetch_org_projects", "组织Project", "读取 GitHub 组织 Projects 看板（同组织多个仓库只读取一次）", "github"]', source)
        self.assertIn(".filter(([, , , scope]) => scope === \"both\" || !gitlab)", source)
        # 抓取开关与启用开关即时保存、不进行自动保存表单，避免冒泡触发
        # saveRepoNotes 的 PUT 与即时 PUT 竞态互踩（读旧行值覆盖新开关）
        self.assertIn('input:not([data-autosave-ignore]), textarea, select', source)
        self.assertIn('<input type="checkbox" data-autosave-ignore aria-label="${label}抓取开关"', source)
        self.assertIn('<input type="checkbox" data-autosave-ignore aria-label="启用或停用该仓库"', source)

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
        self.assertIn('type="file" accept=".md,.markdown,.txt,.html,.htm,.pdf,.xlsx,.xls,.docx,.doc,.png,.jpg,.jpeg,.gif,.webp" multiple', html)
        self.assertIn("支持 Markdown、纯文本、HTML、PDF、Excel、Word 和图片，可多选", source)
        self.assertIn('Array.from($("material-file").files || [])', source)
        self.assertIn('const body = { files: payloads };', source)
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
        self.assertIn('["report", "template", "workstreams"].includes(task.kind)', source)
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
        self.assertIn("if (!event.target.closest('a, button')) beginTodoEdit(", source)
        self.assertIn("event.key === 'Enter' && !event.target.closest('a, button')", source)
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

    def test_todo_star_control_pins_starred_cards_to_top(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        # 卡片右上有星标按钮，星标/未星标两态图标
        self.assertIn('star: {\n    viewBox: "0 0 576 512",', source)
        self.assertIn("starOutline: {", source)
        self.assertIn('class="todo-card-star${starred ? " starred" : ""}"', source)
        self.assertIn('aria-pressed="${starred}"', source)
        self.assertIn('onclick="event.stopPropagation(); toggleTodoStar(${todo.id})"', source)
        # 星标点击不得触发卡片编辑；按钮上按 Enter 也不得
        self.assertIn("event.target.closest('a, button')) beginTodoEdit(", source)
        # 星标走专用切换接口，回包整板刷新（置顶排序由服务端完成）
        self.assertIn("async function toggleTodoStar(id)", source)
        self.assertIn("`/api/todos/${id}/star`", source)
        self.assertIn('{ method: "POST" }', source)
        # 按钮绝对定位在卡片右上角，标题文字让位；拖拽幽灵卡不显示星标
        self.assertIn(".todo-card {", styles)
        self.assertIn("position: relative;", styles)
        self.assertIn("position: absolute; top: 8px; right: 8px;", styles)
        self.assertIn(".todo-card-star.starred {", styles)
        self.assertIn(".todo-card-ghost .todo-card-star { display: none; }", styles)

    def test_todo_closed_lane_fold_markup_exists(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        # 已关闭列：当天完成的直接展示，更早的默认折叠；折叠条固定列尾，点击展开/收起
        self.assertIn("function renderTodoColumnItems(", source)
        self.assertIn("function isClosedToday(todo)", source)
        self.assertIn("timeZone: CHINA_TIMEZONE", source)
        self.assertNotIn("todo-closed-fold-sentinel", source)
        self.assertNotIn("revealMoreClosedTodos", source)
        self.assertNotIn("setupTodoClosedFold", source)
        self.assertIn("function toggleTodoClosedExpand()", source)
        self.assertIn('class="todo-fold-bar"', source)
        self.assertIn(".todo-fold-bar {", styles)
        self.assertNotIn(".todo-fold-sentinel {", styles)

    def test_todo_star_toggle_posts_and_rerenders_board(self):
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
let starFlag = 0;
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  const body = { starred: starFlag === 0 ? (starFlag = 1) : (starFlag = 0), todos: [{ id: 9, title: "Starred item", starred: starFlag }] };
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
  let rerendered = 0;
  renderTodoBoard = () => { rerendered += 1; };
  toast = () => {};
  await toggleTodoStar(9);
  if (fetchCalls[0].path !== "/api/todos/9/star" || fetchCalls[0].options.method !== "POST") {
    throw new Error("star toggle did not POST to /api/todos/:id/star");
  }
  if (state.todos[0].starred !== 1 || rerendered !== 1) {
    throw new Error("star toggle did not adopt response and rerender the board");
  }
  await toggleTodoStar(9);
  if (fetchCalls[1].path !== "/api/todos/9/star" || state.todos[0].starred !== 0) {
    throw new Error("second star toggle did not clear the flag");
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

    def test_todo_closed_lane_folds_older_cards_and_toggles_on_click(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
const testElements = new Map();
function testElement() {
  return {
    value: "",
    textContent: "",
    innerHTML: "",
    scrollLeft: 0, scrollWidth: 0, clientWidth: 0, clientHeight: 0,
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
globalThis.window = { addEventListener() {}, removeEventListener() {}, innerHeight: 800 };
globalThis.setTimeout = (callback) => { callback(); return 0; };
globalThis.requestAnimationFrame = (callback) => callback();
"""
        assertions = r"""
(async () => {
  syncTodoBoardDots = () => {};
  const board = document.getElementById("todo-board");
  const now = new Date();
  const daysAgo = (n) => new Date(now.getTime() - n * 86400000).toISOString();
  state.todos = [
    { id: 1, title: "进行中卡片", status: "doing", starred: 0, description: "", updated_at: daysAgo(0) },
    { id: 2, title: "今天完成的", status: "closed", starred: 0, description: "", close_reason_html: "收工", closed_at: now.toISOString(), updated_at: daysAgo(0) },
    { id: 3, title: "旧卡片甲", status: "closed", starred: 1, description: "", close_reason_html: "早", closed_at: daysAgo(3), updated_at: daysAgo(3) },
    { id: 4, title: "旧卡片乙", status: "closed", starred: 0, description: "", close_reason_html: "早", closed_at: daysAgo(5), updated_at: daysAgo(5) },
    { id: 5, title: "旧卡片丙", status: "closed", starred: 0, description: "", close_reason_html: "早", closed_at: daysAgo(6), updated_at: daysAgo(6) },
  ];
  renderTodoBoard();
  if (!board.innerHTML.includes("今天完成的")) throw new Error("today closed card should stay visible");
  if (!board.innerHTML.includes("折叠了 3 条更早完成")) throw new Error("fold bar missing");
  if (board.innerHTML.includes("旧卡片甲")) throw new Error("older closed card should be folded");
  // 折叠条之后不能再有卡片（位于列尾）
  const barIndex = board.innerHTML.indexOf('class="todo-fold-bar"');
  if (barIndex < 0) throw new Error("fold bar missing from markup");
  if (board.innerHTML.slice(barIndex).includes("data-todo-id")) {
    throw new Error("fold bar must sit at the bottom of the closed lane");
  }
  toggleTodoClosedExpand(); // 点击展开全部更早完成
  if (!board.innerHTML.includes("收起更早完成") || !board.innerHTML.includes("旧卡片丙")) {
    throw new Error("expand should show all older cards");
  }
  const expandedBarIndex = board.innerHTML.indexOf('class="todo-fold-bar"');
  if (board.innerHTML.slice(expandedBarIndex).includes("data-todo-id")) {
    throw new Error("fold bar must stay at the bottom after expanding");
  }
  toggleTodoClosedExpand(); // 再点收起，更早完成的重新隐藏
  if (board.innerHTML.includes("旧卡片甲") || !board.innerHTML.includes("折叠了 3 条更早完成")) {
    throw new Error("collapse should hide older cards again");
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
    if (selector.startsWith("input") && selector.includes("textarea, select")) return [capacityField, parallelField];
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


    def test_assistant_panel_streams_runs_and_applies(self):
        html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="assistant-panel"', html)
        self.assertIn('id="open-assistant"', html)
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
const testElements = new Map();
function testElement() {
  return {
    textContent: "",
    innerHTML: "",
    value: "",
    disabled: false,
    dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    setAttribute() {},
  };
}
globalThis.localStorage = { getItem() { return null; }, setItem() {} };
globalThis.document = {
  body: testElement(),
  getElementById(id) {
    if (!testElements.has(id)) testElements.set(id, testElement());
    return testElements.get(id);
  },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
  removeEventListener() {},
};
globalThis.setTimeout = () => 0;
globalThis.window = { addEventListener() {}, removeEventListener() {}, confirm() { return true; } };
const sources = [];
globalThis.EventSource = class {
  constructor(url) { this.url = url; this.listeners = {}; this.readyState = 1; this.closed = false; sources.push(this); }
  addEventListener(type, fn) { this.listeners[type] = fn; }
  close() { this.closed = true; this.readyState = 2; }
  fire(type, data) { this.listeners[type]({ data: JSON.stringify(data) }); }
};
const responses = [];
const fetchCalls = [];
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  const body = responses.shift();
  if (body === undefined) throw new Error(`unexpected fetch: ${path}`);
  if (body instanceof Error) return { ok: false, status: 400, text: async () => JSON.stringify({ error: body.message }) };
  return { ok: true, status: 200, text: async () => JSON.stringify(body) };
};
"""
        assertions = r"""
(async () => {
  render = () => {};
  const toasts = [];
  toast = (message) => { toasts.push(message); };
  state.projectId = 1;
  state.mode = "reports";
  state.workspace = { project: { id: 1, name: "Demo" }, week_key: "2026-W47", role: "owner", report: { week_key: "2026-W47" } };
  const box = () => document.getElementById("assistant-messages").innerHTML;

  // opening the panel reattaches to an answer still running server-side
  responses.push({ week_key: "2026-W47", has_report: true, messages: [], active_run: { id: "r0", question: "旧问题" } });
  toggleAssistant(true);
  await new Promise((resolve) => setImmediate(resolve));
  if (fetchCalls[0].path !== "/api/projects/1/assistant") throw new Error("thread was not loaded on open");
  if (sources[0].url !== "/api/projects/1/assistant/runs/r0/events") throw new Error(`did not reattach: ${sources[0] && sources[0].url}`);
  sources[0].fire("cancelled", {});
  if (!sources[0].closed || state.assistant.run) throw new Error("terminal event must close the stream");

  responses.push({ run: { id: "r1", question: "把总结改短", done: false } });
  await sendAssistantQuestion("把总结改短");
  if (fetchCalls[1].options.body !== JSON.stringify({ question: "把总结改短" })) throw new Error("bad ask body");
  const es = sources[1];
  if (es.url !== "/api/projects/1/assistant/runs/r1/events") throw new Error("stream not opened");
  if (document.getElementById("assistant-send").textContent !== "停止") throw new Error("send should turn into stop");

  es.fire("round", { round: 0, t: 0.1 });
  if (!box().includes("工作中") || !box().includes("思考中")) throw new Error(`thinking row missing: ${box()}`);
  es.fire("text", { delta: "我先查一下", t: 0.5 });
  es.fire("tool_start", { id: "a", name: "weekly_show", args: { week_key: "2026-W46" }, t: 8.9 });
  es.fire("tool_start", { id: "b", name: "plan_show", args: {}, t: 9.0 });
  if (!box().includes("<code>weekly_show</code>") || !box().includes("{&quot;week_key&quot;:&quot;2026-W46&quot;}")) {
    throw new Error(`raw tool call row missing: ${box()}`);
  }
  if ((box().match(/work-row is-tool is-live/g) || []).length !== 2) throw new Error(`both tools should be live: ${box()}`);
  if (!box().includes("思考</span>") || !box().includes("0.4s")) throw new Error(`finished thinking row needs its duration: ${box()}`);
  if (!box().includes("我先查一下")) throw new Error("interim text should stay as a note row");
  es.fire("tool_end", { id: "a", name: "weekly_show", args: { week_key: "2026-W46" }, ms: 1200, error: false, chars: 30, preview: '{"id": 1}', t: 10.1 });
  if ((box().match(/work-row is-tool is-live/g) || []).length !== 1) throw new Error("finished tool still live");
  if (!box().includes("1.2s") || !box().includes("{&quot;id&quot;: 1}")) throw new Error(`tool duration/result missing: ${box()}`);
  es.fire("tool_end", { id: "b", name: "plan_show", args: {}, ms: 30, error: true, chars: 20, preview: '{"error": "x"}', t: 10.2 });
  if (!box().includes("work-fail")) throw new Error("failed tool needs a failure mark");
  if (!box().includes(">30ms<")) throw new Error(`sub-100ms durations show in ms: ${box()}`);
  es.fire("round", { round: 1, t: 10.3 });
  es.fire("text", { delta: "已调整。\n<<<REPORT>>>\n# 新周报", t: 27.0 });
  if (!box().includes("已调整。") || box().includes("# 新周报") || !box().includes("正在生成周报修改稿")) {
    throw new Error(`report draft must stay hidden while streaming: ${box()}`);
  }
  if (!box().includes("16s")) throw new Error(`second thinking segment should last ~16.7s: ${box()}`);

  es.fire("done", { week_key: "2026-W47", has_report: true, messages: [
    { id: 1, role: "user", content: "把总结改短" },
    { id: 2, role: "assistant", content: "已调整", content_html: "<p>已调整</p>",
      work: { elapsed_ms: 35100, items: [{ kind: "thinking", t: 0.1, ms: 400 }, { kind: "tool", id: "a", name: "weekly_show", args: { week_key: "2026-W46" }, ms: 1200, preview: "{}" }] },
      proposal: { content_md: "# 新", content_html: "<h1>新</h1>", applied_at: "" } },
  ] });
  if (!es.closed || state.assistant.run) throw new Error("done must close the stream");
  if (!box().includes("已工作 35s · 1 次工具调用") || !box().includes("<code>weekly_show</code>") || !box().includes("applyAssistantProposal(2")) {
    throw new Error(`final thread not rendered: ${box()}`);
  }

  responses.push({ report: { edited_at: "2026-11-21T00:00:00+00:00" }, week_key: "2026-W47", has_report: true, messages: [] });
  responses.push({ project: { id: 1, name: "Demo" }, week_key: "2026-W47", role: "owner", jobs: [] });
  await applyAssistantProposal(2);
  if (fetchCalls[2].path !== "/api/projects/1/assistant/messages/2/apply") throw new Error("apply hit the wrong path");
  if (!toasts.some((m) => m.includes("已应用"))) throw new Error("apply toast missing");

  // stop: cancel request, then the cancelled event ends the run
  responses.push({ run: { id: "r2", question: "长问题", done: false } });
  await sendAssistantQuestion("长问题");
  responses.push({ run: { id: "r2", done: false } });
  await stopAssistantRun();
  if (fetchCalls[fetchCalls.length - 1].path !== "/api/projects/1/assistant/runs/r2/cancel") throw new Error("cancel not sent");
  sources[2].fire("cancelled", {});
  if (state.assistant.run || !toasts.some((m) => m.includes("已停止"))) throw new Error("stop did not finish");
  if (document.getElementById("assistant-input").value !== "长问题") throw new Error("stopped question not restored");
  document.getElementById("assistant-input").value = "";

  // a failed run keeps the question for retry and shows the error
  responses.push({ run: { id: "r3", question: "本周进展？", done: false } });
  await sendAssistantQuestion("本周进展？");
  sources[3].fire("error", { message: "助手回答失败：provider down" });
  if (!box().includes("provider down")) throw new Error("error not shown");
  if (document.getElementById("assistant-input").value !== "本周进展？") throw new Error("question was not restored");
  // a busy server (409) is surfaced too
  responses.push(new Error("助手还在回答上一个问题"));
  await sendAssistantQuestion("再问");
  if (!box().includes("还在回答")) throw new Error("409 not shown");
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

if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(shutil.which("node"), "Node.js is required for frontend behavior tests")
class WorkstreamFrontendTest(unittest.TestCase):
    def test_workstream_tab_markup_and_wiring(self):
        html = (ROOT_DIR / "static" / "index.html").read_text(encoding="utf-8")
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertLess(html.index('data-tab="overview"'), html.index('data-tab="workstreams"'))
        self.assertLess(html.index('data-tab="workstreams"'), html.index('data-tab="sources"'))
        for marker in ('id="tab-workstreams"', 'id="workstream-dialog"', 'id="workstream-assign-dialog"', 'id="workstream-assign-primary"'):
            self.assertIn(marker, html)
        self.assertIn('id="workstream-parent-select"', html)
        for marker in ("/workstreams/seed", "/workstreams/organize", "/workstreams/reorder", "/snapshots", '"items"', '"milestones"',
                       "project_milestones", "body.parent_id",
                       "/api/todos/${target.id}/workstreams", 'kind === "workstreams"', "workstream_options",
                       'name="workstream_id"', "body.workstream_id = wsFilter"):
            self.assertIn(marker, source)
        for marker in (".ws-matrix {", ".ws-tag, .todo-ws-tag {", ".workstream-timeline {", ".ws-progress-track {", ".ws-item {"):
            self.assertIn(marker, styles)

    def test_matrix_filter_and_assignment_behaviour(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
const testElements = new Map();
function testElement() {
  return {
    value: "", textContent: "", innerHTML: "", disabled: false, dataset: {},
    classList: { add() {}, remove() {}, toggle() {}, contains() { return false; } },
    setAttribute() {}, focus() {}, showModal() { this.open = true; }, close() { this.open = false; },
    querySelectorAll() { return []; },
  };
}
globalThis.localStorage = { getItem() { return null; }, setItem() {} };
globalThis.document = {
  body: testElement(), activeElement: null,
  getElementById(id) { if (!testElements.has(id)) testElements.set(id, testElement()); return testElements.get(id); },
  querySelectorAll() { return []; }, addEventListener() {}, removeEventListener() {},
};
globalThis.window = { addEventListener() {}, removeEventListener() {}, confirm() { return true; } };
globalThis.setTimeout = (callback) => { callback(); return 0; };
globalThis.requestAnimationFrame = (callback) => callback();
const fetchCalls = [];
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  const body = { project: { id: 3 }, materials: [] };
  return { ok: true, text: async () => JSON.stringify(body), async json() { return body; } };
};
"""
        assertions = r"""
(async () => {
  const cell = (week, snapshot, materials) => ({ week_key: week, snapshot, materials });
  state.projectId = 3;
  state.workspace = {
    project: { id: 3, name: "agent guard" }, role: "owner", plan: { objectives: "1. 东风交付" },
    materials: [
      { id: 5, filename: "a.md", workstreams: { primary: 11, related: [12], source: "auto" } },
      { id: 6, filename: "b.md", workstreams: { primary: null, related: [], source: "" } },
    ],
    workstream_job: { id: 1, status: "success", output_md: "归类 3 份资料，补齐 2 周快照", completed_at: "2026-11-23T10:00:00+00:00" },
    workstreams: {
      weeks: ["2026-W47", "2026-W48"], current_week: "2026-W48", unassigned_materials: 1,
      workstreams: [
        { id: 11, name: "东风交付", status: "active", health: "on track", owner_label: "高鹏", target_date: "", material_total: 2,
          cells: [cell("2026-W47", { status: "advanced", summary: "完成联调", next_step: "验收" }, 1), cell("2026-W48", null, 2)] },
        { id: 12, name: "融资", status: "paused", health: "paused", owner_label: "", target_date: "", material_total: 0,
          cells: [cell("2026-W47", null, 0), cell("2026-W48", null, 0)] },
      ],
    },
  };
  if (state.workstreamView !== "progress") throw new Error("progress view should be the default");
  state.workstreamView = "matrix";
  renderWorkstreams(state.workspace);
  const html = document.getElementById("ws-board").innerHTML;
  for (const needle of ["完成联调", "2 份资料", ">W48<", "未归类资料 1", "AI 整理", 'data-workstream-id="12"', "归类 3 份资料", "高鹏"]) {
    if (!html.includes(needle)) throw new Error(`matrix missing ${needle}`);
  }

  // progress view: one lane segment per timeline week, markers placed by date, item progress
  Object.assign(state.workspace.workstreams, {
    today: "2026-11-24",
    timeline: [
      { week_key: "2026-W47", start: "2026-11-16" }, { week_key: "2026-W48", start: "2026-11-23" },
      { week_key: "2026-W49", start: "2026-11-30" }, { week_key: "2026-W50", start: "2026-12-07" },
    ],
  });
  Object.assign(state.workspace.workstreams.workstreams[0], {
    target_date: "2026-12-07", items_open: 2, items_done: 1, items_overdue: 1,
    milestones: [{ title: "实车测试", target_date: "2026-11-30", status: "planned" }],
  });
  state.workstreamView = "progress";
  renderWorkstreams(state.workspace);
  const lanes = document.getElementById("ws-board").innerHTML;
  for (const needle of ['ws-seg is-advanced"', "is-pending is-current", 'ws-seg is-future"', "里程碑：实车测试（2026-11-30）",
                        'ws-target" style="left:75.00%"', 'class="ws-today" style="left:28.57%"', "1 逾期", "width:33%", "2 待跟踪",
                        "本周有进展"]) {
    if (!lanes.includes(needle)) throw new Error(`progress view missing ${needle}`);
  }
  if (lanes.includes("ws-matrix")) throw new Error("progress view should not render the matrix");
  const [linked, unassigned] = state.workspace.materials;
  if (!materialMatchesWorkstream(linked, 12) || materialMatchesWorkstream(unassigned, 11) || !materialMatchesWorkstream(unassigned, "none")) {
    throw new Error("workstream filter matched the wrong materials");
  }
  state.sourceWorkstreamFilter = 99;
  if (sourceFilterActive() !== "all") throw new Error("unknown workstream filter should fall back to all");
  if (!materialWorkstreamTag(linked, true).includes("东风交付 +1")) throw new Error("material tag should show primary plus related count");

  let adopted = null;
  updateWorkspace = (workspace) => { adopted = workspace; };
  toast = () => {};
  openWorkstreamAssign("material", 5);
  if (!document.getElementById("workstream-assign-dialog").open) throw new Error("assign dialog did not open");
  if (!document.getElementById("workstream-assign-primary").innerHTML.includes('value="11" selected')) throw new Error("current primary not preselected");
  document.getElementById("workstream-assign-primary").value = "12";
  await submitWorkstreamAssign({ preventDefault() {} });
  const call = fetchCalls.at(-1);
  if (call.path !== "/api/projects/3/materials/5/workstreams" || call.options.method !== "PUT") throw new Error(`unexpected call ${call.path}`);
  if (JSON.stringify(JSON.parse(call.options.body)) !== JSON.stringify({ primary: 12, related: [] })) throw new Error(`unexpected body ${call.options.body}`);
  if (!adopted) throw new Error("assignment response was not adopted");

  // tracking items in the detail panel: open first, done folded, edits go to the items API
  state.workstreamId = 11;
  state.workstreamDetail = {
    id: 11, projectId: 3, name: "东风交付", health: "at risk", current_week: "2026-W48", snapshots: [], materials: [], todos: [], milestones: [],
    items: [
      { id: 7, title: "确认实车排期", owner_label: "高鹏", due_date: "2026-11-20", status: "open", source: "auto" },
      { id: 8, title: "签署确认单", owner_label: "", due_date: "", status: "done", source: "manual", done_at: "2026-11-23T10:00:00+00:00" },
    ],
  };
  renderWorkstreamDetail();
  const detail = document.getElementById("workstream-detail").innerHTML;
  for (const needle of ["待跟踪项", "1 项待跟踪", "已逾期 · 2026-11-20", "AI 提取", "已完成 1", "本周 W48", "过去的周已锁定"]) {
    if (!detail.includes(needle)) throw new Error(`detail missing ${needle}`);
  }
  if (detail.includes('id="ws-snap-week"')) throw new Error("past weeks should not be selectable");
  loadWorkspace = async () => {};
  await toggleWorkstreamItem(11, 7, true);
  const toggle = fetchCalls.at(-1);
  if (toggle.path !== "/api/projects/3/workstreams/11/items/7" || toggle.options.method !== "PUT" || JSON.parse(toggle.options.body).status !== "done") {
    throw new Error(`unexpected toggle ${toggle.path} ${toggle.options.body}`);
  }

  // 子工作线: nested lanes with a fold toggle, parent filters include children, sibling-only moves
  const lines = state.workspace.workstreams.workstreams;
  Object.assign(lines[0], { children: [13], own_health: "on track", health: "at risk" });
  lines.splice(1, 0, { id: 13, name: "实车测试", parent_id: 11, children: [], status: "active", health: "at risk", own_health: "at risk",
    owner_label: "", target_date: "", material_total: 1, cells: [cell("2026-W47", null, 0), cell("2026-W48", null, 1)] });
  Object.assign(lines[2], { children: [] });
  renderWorkstreams(state.workspace);
  const nested = document.getElementById("ws-board").innerHTML;
  for (const needle of ['is-child', 'data-workstream-id="13"', '收起 1 条子工作线', 'class="ws-branch"', 'class="ws-fold-space"']) {
    if (!nested.includes(needle)) throw new Error(`nested lanes missing ${needle}`);
  }
  if (!/<strong>1<\/strong><span>有风险/.test(nested)) throw new Error("summary should count each line by its own health");
  toggleWorkstreamCollapse({ stopPropagation() {} }, 11);
  const folded = document.getElementById("ws-board").innerHTML;
  if (folded.includes('data-workstream-id="13"') || !folded.includes('class="ws-kids">+1')) throw new Error("collapsed parent should hide its children");
  toggleWorkstreamCollapse({ stopPropagation() {} }, 11);
  if (!materialMatchesWorkstream({ workstreams: { primary: 13, related: [] } }, 11)) throw new Error("parent filter should include child material");
  if (materialMatchesWorkstream({ workstreams: { primary: 11, related: [] } }, 13)) throw new Error("child filter should not include parent material");
  if (JSON.stringify(wsSiblings(13)) !== "[13]" || JSON.stringify(wsSiblings(12)) !== "[11,12]") throw new Error(`unexpected siblings ${wsSiblings(12)}`);
  await moveWorkstream(12, -1);
  const reorder = fetchCalls.at(-1);
  if (reorder.path !== "/api/projects/3/workstreams/reorder" || JSON.stringify(JSON.parse(reorder.options.body).ids) !== "[12,11,13]") {
    throw new Error(`parent should move with its children: ${reorder.options.body}`);
  }
  document.getElementById("workstream-form").elements = Object.fromEntries(
    ["id", "name", "goal", "owner_label", "target_date", "status"].map((name) => [name, { value: "" }]));
  openWorkstreamDialog(null, 11);
  const parentSelect = document.getElementById("workstream-parent-select");
  if (parentSelect.value !== "11" || parentSelect.innerHTML.includes('value="13"')) throw new Error("sub-workstream dialog should preset the parent and list only top-level lines");

  // detail: children and editable milestones
  state.workstreamId = 11;
  state.workstreamDetail = { id: 11, projectId: 3, name: "东风交付", health: "at risk", current_week: "2026-W48", snapshots: [], materials: [],
    todos: [], items: [], children: [13], parent: null, child_alerts: ["子工作线「实车测试」有风险"],
    child_items: [{ id: 13, name: "实车测试", status: "active", health: "at risk", owner_label: "", target_date: "", items_open: 2, items_overdue: 0 }],
    milestones: [{ id: 2, title: "验收", target_date: "2026-12-20", status: "planned", workstream_id: 11 },
                 { id: 1, title: "联调", target_date: "2026-11-10", status: "complete", workstream_id: 11 }] };
  renderWorkstreamDetail();
  const family = document.getElementById("workstream-detail").innerHTML;
  for (const needle of ["子工作线 <small>1</small>", "实车测试", "2 待跟踪", "子工作线「实车测试」有风险", "已完成 1/2", "新增里程碑", "＋ 子工作线"]) {
    if (!family.includes(needle)) throw new Error(`detail missing ${needle}`);
  }
  if (family.indexOf("联调") > family.indexOf("验收")) throw new Error("milestones should be ordered by date");
  await toggleWorkstreamMilestone(11, 2, true);
  const done = fetchCalls.at(-1);
  if (done.path !== "/api/projects/3/workstreams/11/milestones/2" || JSON.parse(done.options.body).status !== "complete") {
    throw new Error(`unexpected milestone toggle ${done.path} ${done.options.body}`);
  }

  // PR / issue activity: detail list, unassigned list, single-workstream assignment
  state.workstreamDetail.git_items = [
    { id: 41, repo: "CogDefend/cogdefend", kind: "pr", number: 12, title: "规则引擎重构", state: "merged", url: "https://x/12", author: "dev", week_key: "2026-W48", workstream_id: 11, link_source: "repo" },
  ];
  renderWorkstreamDetail();
  const gitDetail = document.getElementById("workstream-detail").innerHTML;
  for (const needle of ["PR / Issue <small>1</small>", "已合并", "cogdefend#12", "仓库默认", "openWorkstreamAssign('git', 41)"]) {
    if (!gitDetail.includes(needle)) throw new Error(`git detail missing ${needle}`);
  }
  state.workspace.workstreams.unassigned_git = [
    { id: 42, repo: "CogDefend/cloud", kind: "issue", number: 7, title: "升级依赖", state: "open", url: "https://x/7", author: "", week_key: "2026-W48", workstream_id: null, link_source: "" },
  ];
  state.workspace.workstreams.workstreams[0].cells[1].git = 3;
  state.workstreamView = "matrix";
  renderWorkstreams(state.workspace);
  const board = document.getElementById("ws-board").innerHTML;
  for (const needle of ["本周未归类 PR/Issue 1", "升级依赖", "归到工作线", "3 条 PR/Issue"]) {
    if (!board.includes(needle)) throw new Error(`board missing ${needle}`);
  }
  state.workstreamView = "progress";
  openWorkstreamAssign("git", 42);
  document.getElementById("workstream-assign-primary").value = "13";
  await submitWorkstreamAssign({ preventDefault() {} });
  const link = fetchCalls.find((c) => c.path.endsWith("/workstreams/git/42/link"));
  if (!link || link.options.method !== "PUT" || JSON.parse(link.options.body).workstream_id !== 13) throw new Error("git assignment call missing");
  if (!renderRepoWorkstream({ id: 3, workstream_id: 11 }).includes('value="11" selected')) throw new Error("repo default workstream not preselected");

  // risks moved into the tab; a workstream warning links to its line
  state.workspace.progress_status = "at risk";
  state.workspace.risks = [{ rule: "workstream_item_overdue", severity: "medium", title: "工作线「东风交付」有 1 条待跟踪项逾期", details: "", status: "active", source_ref: "workstream:11" }];
  renderWorkstreamRisks(state.workspace);
  const risks = document.getElementById("ws-risks").innerHTML;
  for (const needle of ["风险提醒", "待跟踪项逾期", "focusWorkstream(11)", "本周 1 条活跃"]) {
    if (!risks.includes(needle)) throw new Error(`risk panel missing ${needle}`);
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });
"""
        result = subprocess.run(
            ["node"], input=f"{harness}\n{source}\n{assertions}", cwd=ROOT_DIR, text=True, capture_output=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

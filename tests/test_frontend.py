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
        self.assertNotIn('data-tab="settings"', html)
        self.assertIn('data-project-settings=', source)
        self.assertIn('data-project-generate=', source)
        self.assertIn('switchTab("settings")', source)
        self.assertIn('const FA_ICONS = {', source)
        self.assertIn('${faIcon("gear")}', source)
        self.assertNotIn('<footer class="app-footer">', html)
        self.assertNotIn("中国标准时间 · 本地个人项目管理", html)
        self.assertIn('id="project-status-dot"', html)
        self.assertIn('return project.progress_status || project.status || "unknown";', source)
        self.assertIn('data-source-tab="files"', source)
        self.assertIn('data-source-tab="manual"', source)
        self.assertIn('id="material-dropzone"', source)
        self.assertIn('dropzone.addEventListener("drop"', source)
        self.assertIn("setupMaterialDropzone();", source)

    def test_responsive_layout_contains_wide_content_overflow(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("ensureTableScrollContainers();", source)
        self.assertIn(".table-scroll {", styles)
        self.assertIn("overflow-x: auto;", styles)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", styles)
        self.assertIn("@media (max-width: 767px)", styles)
        self.assertIn(".status-strip, .form-grid, .schedule-row, .plan-item, .outcome-item { grid-template-columns: 1fr; }", styles)

    def test_material_upload_supports_multiple_files_and_summary_editing(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        html = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn('type="file" accept=".md,.markdown,.txt,.pdf" multiple', html)
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
        self.assertIn("material.content_html", source)
        self.assertIn("/materials/${id}/content`", source)
        self.assertIn('id="material-preview-pdf"', html)
        self.assertIn('id="material-preview-markdown"', html)
        self.assertIn('$("close-material-preview").onclick', source)

    def test_unlocked_materials_have_delete_controls(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT_DIR / "static" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('m.deletable ? `<button class="danger" onclick="deleteMaterial(${m.id})">Delete</button>`', source)
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
        self.assertIn('.todo-mode .page-corner-fold { color: var(--on-dark);', styles)
        self.assertIn('.page-corner.turning { animation: corner-peel 400ms', styles)
        self.assertIn('@media (prefers-reduced-motion: reduce)', styles)
        self.assertIn('function playPageTurn()', source)
        self.assertIn('filter: drop-shadow(-6px 7px 9px rgba(15, 23, 42, 0.28));', styles)
        self.assertIn('.todo-column-todo {', styles)
        self.assertIn('.todo-column-doing {', styles)
        self.assertIn('.todo-column-closed {', styles)
        self.assertIn('.message-box {', styles)
        self.assertIn('--board-canvas: #172033;', styles)
        self.assertIn('#todo-view { min-height: 100vh; background: var(--board-canvas); }', styles)
        self.assertIn('grid-template-columns: repeat(3, minmax(260px, 1fr));', styles)
        self.assertIn('grid-template-columns: repeat(3, minmax(260px, 84vw));', styles)
        self.assertIn('.todo-mode .app-shell { grid-template-columns: minmax(0, 1fr); }', styles)

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
    classList: { add() {}, remove() {}, toggle() {} },
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
  return {
    ok: true,
    async json() {
      return { todos: [{ id: 7, title: payload.title, description: payload.description, status: payload.status || "todo" }] };
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

    def test_generate_report_renders_returned_workspace_without_second_request(self):
        source = (ROOT_DIR / "static" / "app.js").read_text(encoding="utf-8")
        source = source.split('\n$("new-project").onclick', 1)[0]
        harness = r"""
const testElements = new Map();
function testElement() {
  return {
    textContent: "",
    disabled: false,
    dataset: {},
    classList: { add() {}, remove() {}, toggle() {} },
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
globalThis.window = { confirm() { return false; } };
const returnedWorkspace = {
  project: { id: 1, name: "Demo" },
  report: { content_html: "<h1>Fresh report</h1>" },
};
const fetchCalls = [];
globalThis.fetch = async (path, options) => {
  fetchCalls.push({ path, options });
  return { ok: true, async json() { return returnedWorkspace; } };
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
  let renderedWorkspace = null;
  render = () => { renderedWorkspace = state.workspace; };
  state.projectId = 1;

  await generateReport();

  if (state.workspace !== returnedWorkspace || renderedWorkspace !== returnedWorkspace) {
    throw new Error("generateReport did not render the workspace returned by POST");
  }
  if (fetchCalls.length !== 1) {
    throw new Error(`expected one generation request, received ${fetchCalls.length}`);
  }
  if (fetchCalls[0].path !== "/api/projects/1/generate") {
    throw new Error(`unexpected request path: ${fetchCalls[0].path}`);
  }
  if (fetchCalls[0].options.method !== "POST" || fetchCalls[0].options.cache !== "no-store") {
    throw new Error("generation request did not use POST with cache disabled");
  }

  state.projects = [{ id: 1, name: "Demo" }];
  confirmProjectGeneration(1);
  if (fetchCalls.length !== 1) {
    throw new Error("opening the message box started generation prematurely");
  }
  if (state.pendingReportProjectId !== 1 || !$("report-confirm-dialog").open) {
    throw new Error("project-row generation did not open the app message box");
  }
  await runConfirmedProjectGeneration();
  if (fetchCalls.length !== 2 || fetchCalls[1].path !== "/api/projects/1/generate") {
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


if __name__ == "__main__":
    unittest.main()

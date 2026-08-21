import shutil
import subprocess
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("node"), "Node.js is required for frontend behavior tests")
class FrontendTest(unittest.TestCase):
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
        self.assertIn('$("material-preview-content").textContent = material.content', source)
        self.assertIn('$("close-material-preview").onclick', source)

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

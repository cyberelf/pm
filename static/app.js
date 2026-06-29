const CHINA_TIMEZONE = "Asia/Shanghai";
const state = {
  projects: [],
  projectId: Number(localStorage.getItem("currentProjectId")) || null,
  workspace: null,
  tab: "overview",
  busy: false,
};

const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "request failed");
  return data;
}

async function withBusy(title, detail, fn) {
  setBusy(true, title, detail);
  try {
    return await fn();
  } finally {
    setBusy(false);
  }
}

function setBusy(active, title = "Working", detail = "Please wait...") {
  state.busy = active;
  $("loading-title").textContent = title;
  $("loading-detail").textContent = detail;
  $("loading-overlay").classList.toggle("hidden", !active);
  document.querySelectorAll("button").forEach((button) => {
    if (active) {
      button.dataset.wasDisabled = button.disabled ? "1" : "0";
      button.disabled = true;
    } else if (button.dataset.wasDisabled !== "1") {
      button.disabled = false;
    }
  });
}

function toast(message) {
  const el = $("toast");
  el.textContent = message;
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 2800);
}

async function loadState() {
  const data = await api("/api/state");
  state.projects = data.projects;
  if (!state.projectId && state.projects.length) state.projectId = state.projects[0].id;
  if (state.projectId && !state.projects.some((p) => p.id === state.projectId)) {
    state.projectId = state.projects.length ? state.projects[0].id : null;
  }
  renderProjects();
  if (state.projectId) await loadWorkspace();
}

async function loadWorkspace() {
  state.workspace = await api(`/api/projects/${state.projectId}/workspace`);
  render();
}

function renderProjects() {
  $("project-list").innerHTML = state.projects.map(p => `
    <button class="project-item ${p.id === state.projectId ? "active" : ""}" data-project="${p.id}">
      <strong>${escapeHtml(p.name)}</strong>
      <span>${escapeHtml(p.status)} · ${timezoneLabel(p.timezone)}</span>
    </button>
  `).join("");
  document.querySelectorAll("[data-project]").forEach(btn => {
    btn.onclick = async () => {
      state.projectId = Number(btn.dataset.project);
      localStorage.setItem("currentProjectId", String(state.projectId));
      await loadWorkspace();
      renderProjects();
    };
  });
}

function render() {
  const ws = state.workspace;
  $("empty-state").classList.toggle("hidden", !!ws);
  $("workspace").classList.toggle("hidden", !ws);
  if (!ws) return;
  $("project-title").textContent = ws.project.name;
  $("project-meta").textContent = `${ws.week_key} · ${timezoneLabel(ws.project.timezone)} · ${ws.progress_status}`;
  renderOverview(ws);
  renderSettings(ws);
  renderPlan(ws);
  renderUpdates(ws);
  renderSources(ws);
  renderReport(ws);
  renderRisks(ws);
  switchTab(state.tab);
}

function renderOverview(ws) {
  $("tab-overview").innerHTML = `
    <div class="status-strip">
      <div class="metric"><span>项目周</span><strong>${ws.week_key}</strong><small>${timezoneLabel(ws.project.timezone)}</small></div>
      <div class="metric"><span>进度状态</span><strong>${escapeHtml(ws.progress_status)}</strong><small>deterministic rules</small></div>
      <div class="metric"><span>活跃风险</span><strong>${ws.risks.filter(r => r.status === "active").length}</strong><small>visible warnings</small></div>
      <div class="metric"><span>资料源</span><strong>${ws.materials.length + ws.repos.length}</strong><small>materials + repos</small></div>
    </div>
    <div class="grid-2">
      <div class="panel">
        <div class="panel-head"><h2>当前计划</h2><span>Plan baseline</span></div>
        <p>${escapeHtml(ws.plan.objectives || "No objectives yet.")}</p>
        <table class="table"><tbody>${ws.plan.milestones.map(rowItem).join("") || "<tr><td>No milestones.</td></tr>"}</tbody></table>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>当前周报</h2><span>Canonical report</span></div>
        <p>${ws.report ? `Generated ${escapeHtml(formatChinaTime(ws.report.updated_at))}` : "No report generated yet."}</p>
        <div class="row"><button class="primary generate-action" onclick="generateReport()">Generate</button><button onclick="switchTab('report')">Open Report</button></div>
      </div>
    </div>
  `;
}

function renderSettings(ws) {
  const p = ws.project;
  $("tab-settings").innerHTML = `
    <form id="settings-form" class="panel form-grid">
      <div class="panel-head wide"><h2>项目设置</h2><span>Local runtime · China time</span></div>
      ${input("name", "Name", p.name)}
      ${input("status", "Status", p.status)}
      ${input("start_date", "Start date", p.start_date, "date")}
      ${input("end_date", "End date", p.end_date || "", "date")}
      ${timezoneSelect("timezone", "Timezone", p.timezone)}
      <label>Provider<select name="report_provider"><option value="codex" ${p.report_provider === "codex" ? "selected" : ""}>Codex CLI</option><option value="claude" ${p.report_provider === "claude" ? "selected" : ""}>Claude Code CLI</option></select></label>
      ${textarea("description", "Description", p.description, "wide")}
      ${textarea("manual_background", "Background", p.manual_background, "wide")}
      ${textarea("manual_objectives", "Objectives", p.manual_objectives, "wide")}
      ${textarea("manual_constraints", "Constraints", p.manual_constraints, "wide")}
      ${textarea("system_prompt", "System Prompt", p.system_prompt, "wide")}
      ${textarea("report_template", "Project Report Template", p.report_template, "wide")}
      <div class="wide panel">
        <div class="panel-head"><h3>更新时间点</h3><span>同一项目周内覆盖当前周报</span></div>
        <div id="schedule-list">${renderSchedules(ws.schedules, p.timezone)}</div>
        <button type="button" onclick="addSchedule()">+ Schedule</button>
      </div>
      <div class="wide row"><button class="primary">Save Settings</button></div>
    </form>
    <div class="panel">
      <div class="panel-head"><h2>GitHub</h2><span>本周 commits 会进入生成上下文</span></div>
      <div class="row"><input id="repo-input" placeholder="owner/repo"><input id="repo-notes-input" placeholder="补充说明，例如正式名称、模块边界"><button type="button" onclick="addRepo()">Add Repo</button></div>
      <table class="table"><thead><tr><th>Repo</th><th>补充说明</th><th>Status</th><th>Action</th></tr></thead><tbody>${ws.repos.map(r => `<tr><td>${escapeHtml(r.repo)}</td><td><textarea id="repo-notes-${r.id}" class="table-textarea">${escapeHtml(r.notes || "")}</textarea></td><td><span class="status ${r.status}">${escapeHtml(r.status)}</span><br>${escapeHtml(r.status_message || "")}</td><td><button type="button" onclick="saveRepoNotes(${r.id})">Save Note</button><button type="button" onclick="refreshRepo(${r.id})">Refresh</button></td></tr>`).join("") || "<tr><td colspan='4'>No repositories.</td></tr>"}</tbody></table>
    </div>
  `;
  $("settings-form").onsubmit = saveSettings;
}

function renderSchedules(schedules, timezone) {
  const rows = schedules.length ? schedules : [{ weekday: 5, local_time: "18:00", timezone: CHINA_TIMEZONE }];
  return rows.map((s, i) => `
    <div class="row schedule-row">
      <label>Weekday <input name="schedule_weekday" type="number" min="1" max="7" value="${s.weekday}"></label>
      <label>Time <input name="schedule_time" value="${escapeHtml(s.local_time)}"></label>
      ${timezoneSelect("schedule_timezone", "Timezone", s.timezone)}
      <button type="button" onclick="this.closest('.schedule-row').remove()">Remove</button>
    </div>
  `).join("");
}

function addSchedule() {
  $("schedule-list").insertAdjacentHTML("beforeend", renderSchedules([{ weekday: 5, local_time: "18:00", timezone: CHINA_TIMEZONE }], CHINA_TIMEZONE));
}

async function saveSettings(event) {
  event.preventDefault();
  const fd = new FormData(event.target);
  const weekdays = fd.getAll("schedule_weekday");
  const times = fd.getAll("schedule_time");
  const zones = fd.getAll("schedule_timezone");
  const schedules = weekdays.map((w, i) => ({ weekday: Number(w), local_time: times[i], timezone: zones[i] })).filter(s => s.local_time);
  const payload = Object.fromEntries(fd.entries());
  payload.schedules = schedules;
  await api(`/api/projects/${state.projectId}/settings`, { method: "PUT", body: JSON.stringify(payload) });
  toast("Settings saved");
  await loadWorkspace();
}

function renderPlan(ws) {
  $("tab-plan").innerHTML = `
    <form id="plan-form" class="panel">
      <div class="panel-head"><h2>项目计划</h2><span>Milestones and deliverables</span></div>
      ${textarea("objectives", "Objectives", ws.plan.objectives)}
      <h3>Milestones</h3>
      <div id="milestones">${renderPlanItems(ws.plan.milestones)}</div>
      <button type="button" onclick="addPlanItem('milestones')">+ Milestone</button>
      <h3>Deliverables</h3>
      <div id="deliverables">${renderPlanItems(ws.plan.deliverables)}</div>
      <button type="button" onclick="addPlanItem('deliverables')">+ Deliverable</button>
      <div class="row"><button class="primary">Save Plan</button></div>
    </form>
    <form id="outcome-form" class="panel">
      <div class="panel-head"><h2>本周计划产出</h2><span>${escapeHtml(ws.week_key)}</span></div>
      <div id="outcomes">${renderOutcomes(ws.outcomes)}</div>
      <button type="button" onclick="addOutcome()">+ Outcome</button>
      <div class="row"><button class="primary">Save Outcomes</button></div>
    </form>
  `;
  $("plan-form").onsubmit = savePlan;
  $("outcome-form").onsubmit = saveOutcomes;
}

function renderPlanItems(items) {
  return (items.length ? items : [{ title: "", status: "planned", owner_label: "", target_date: "" }]).map(item => `
    <div class="row plan-item">
      <input name="title" placeholder="Title" value="${escapeAttr(item.title || "")}">
      <input name="owner_label" placeholder="Owner label" value="${escapeAttr(item.owner_label || "")}">
      <input name="target_date" type="date" value="${escapeAttr(item.target_date || "")}">
      <select name="status">${statusOptions(item.status)}</select>
      <button type="button" onclick="this.closest('.plan-item').remove()">Remove</button>
    </div>
  `).join("");
}

function addPlanItem(id) {
  $(id).insertAdjacentHTML("beforeend", renderPlanItems([{ title: "", status: "planned" }]));
}

async function savePlan(event) {
  event.preventDefault();
  const groups = (id) => Array.from($(id).querySelectorAll(".plan-item")).map(row => itemPayload(row)).filter(i => i.title);
  await api(`/api/projects/${state.projectId}/plan`, { method: "PUT", body: JSON.stringify({ objectives: event.target.objectives.value, milestones: groups("milestones"), deliverables: groups("deliverables") }) });
  toast("Plan saved");
  await loadWorkspace();
}

function renderOutcomes(items) {
  return (items.length ? items : [{ title: "", details: "", status: "planned", owner_label: "" }]).map(item => `
    <div class="row outcome-item">
      <input name="title" placeholder="Outcome" value="${escapeAttr(item.title || "")}">
      <input name="owner_label" placeholder="Owner label" value="${escapeAttr(item.owner_label || "")}">
      <select name="status">${statusOptions(item.status)}</select>
      <input name="details" placeholder="Details" value="${escapeAttr(item.details || "")}">
      <button type="button" onclick="this.closest('.outcome-item').remove()">Remove</button>
    </div>
  `).join("");
}

function addOutcome() { $("outcomes").insertAdjacentHTML("beforeend", renderOutcomes([{ title: "", status: "planned" }])); }

async function saveOutcomes(event) {
  event.preventDefault();
  const outcomes = Array.from($("outcomes").querySelectorAll(".outcome-item")).map(row => itemPayload(row)).filter(i => i.title);
  await api(`/api/projects/${state.projectId}/weekly-outcomes`, { method: "PUT", body: JSON.stringify({ outcomes }) });
  toast("Outcomes saved");
  await loadWorkspace();
}

function renderUpdates(ws) {
  const u = ws.weekly_update || {};
  $("tab-updates").innerHTML = `
    <form id="update-form" class="panel form-grid">
      <div class="panel-head wide"><h2>本周进展</h2><span>${escapeHtml(ws.week_key)} · ${timezoneLabel(ws.project.timezone)}</span></div>
      ${textarea("completed", "Completed", u.completed || "", "wide")}
      ${textarea("in_progress", "In Progress", u.in_progress || "", "wide")}
      ${textarea("blockers", "Blockers", u.blockers || "", "wide")}
      ${textarea("risks", "Risks", u.risks || "", "wide")}
      ${textarea("next_steps", "Next Steps", u.next_steps || "", "wide")}
      <div class="wide row"><button class="primary">Save Update</button></div>
    </form>
  `;
  $("update-form").onsubmit = async (event) => {
    event.preventDefault();
    await api(`/api/projects/${state.projectId}/weekly-update`, { method: "PUT", body: JSON.stringify(Object.fromEntries(new FormData(event.target).entries())) });
    toast("Weekly update saved");
    await loadWorkspace();
  };
}

function renderSources(ws) {
  $("tab-sources").innerHTML = `
    <div class="grid-2">
      <div class="panel">
        <div class="panel-head"><h2>文件资料</h2><span>本周新增资料会进入生成上下文</span></div>
        <input id="material-file" type="file" accept=".md,.markdown,.txt,.pdf">
        <button onclick="uploadMaterial()">Upload</button>
        <table class="table"><thead><tr><th>File</th><th>Status</th><th>Created</th><th>Updated</th><th>Message</th></tr></thead><tbody>${ws.materials.filter(m => m.source_type !== "manual").map(m => `<tr><td>${escapeHtml(m.filename)}</td><td><span class="status ${m.extraction_status}">${m.extraction_status}</span></td><td>${escapeHtml(formatChinaTime(m.created_at))}</td><td>${escapeHtml(formatChinaTime(m.updated_at))}</td><td>${escapeHtml(m.extraction_error || "")}</td></tr>`).join("") || "<tr><td colspan='5'>No uploaded materials.</td></tr>"}</tbody></table>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>手工资料</h2><span>仅本周录入的资料可以修改</span></div>
        <div class="manual-material-form">
          <input id="manual-material-title" placeholder="资料标题">
          <textarea id="manual-material-content" placeholder="输入本周新增的背景、决策、会议记录或补充资料"></textarea>
          <button onclick="saveManualMaterial()">Save Manual Material</button>
        </div>
        <table class="table"><thead><tr><th>Title</th><th>Content</th><th>Created</th><th>Updated</th><th>Action</th></tr></thead><tbody>${ws.materials.filter(m => m.source_type === "manual").map(renderManualMaterialRow).join("") || "<tr><td colspan='5'>No manual materials.</td></tr>"}</tbody></table>
      </div>
    </div>
  `;
}

function renderManualMaterialRow(m) {
  const content = escapeHtml(m.content || "");
  if (m.editable) {
    return `<tr><td><input id="manual-title-${m.id}" value="${escapeAttr(m.filename)}"></td><td><textarea id="manual-content-${m.id}" class="table-textarea material-editor">${content}</textarea></td><td>${escapeHtml(formatChinaTime(m.created_at))}</td><td>${escapeHtml(formatChinaTime(m.updated_at))}</td><td><button onclick="updateManualMaterial(${m.id})">Save</button></td></tr>`;
  }
  return `<tr><td>${escapeHtml(m.filename)}</td><td><div class="locked-material">${content}</div></td><td>${escapeHtml(formatChinaTime(m.created_at))}</td><td>${escapeHtml(formatChinaTime(m.updated_at))}</td><td><span class="status">locked</span></td></tr>`;
}

async function uploadMaterial() {
  const file = $("material-file").files[0];
  if (!file) return toast("Choose a file");
  const content_base64 = await fileToBase64(file);
  await api(`/api/projects/${state.projectId}/materials`, { method: "POST", body: JSON.stringify({ filename: file.name, content_type: file.type, content_base64 }) });
  toast("Material uploaded");
  await loadWorkspace();
}

async function saveManualMaterial() {
  await api(`/api/projects/${state.projectId}/materials`, {
    method: "POST",
    body: JSON.stringify({
      source_type: "manual",
      title: $("manual-material-title").value,
      content: $("manual-material-content").value,
    }),
  });
  toast("Manual material saved");
  await loadWorkspace();
}

async function updateManualMaterial(id) {
  await api(`/api/projects/${state.projectId}/materials/${id}`, {
    method: "PUT",
    body: JSON.stringify({
      title: $(`manual-title-${id}`).value,
      content: $(`manual-content-${id}`).value,
    }),
  });
  toast("Manual material updated");
  await loadWorkspace();
}

async function addRepo() {
  await api(`/api/projects/${state.projectId}/repos`, { method: "POST", body: JSON.stringify({ repo: $("repo-input").value, notes: $("repo-notes-input").value }) });
  toast("Repository saved");
  await loadWorkspace();
}

async function saveRepoNotes(id) {
  await api(`/api/projects/${state.projectId}/repos/${id}`, { method: "PUT", body: JSON.stringify({ notes: $(`repo-notes-${id}`).value }) });
  toast("Repository note saved");
  await loadWorkspace();
}

async function refreshRepo(id) {
  await api(`/api/projects/${state.projectId}/repos/${id}/refresh`, { method: "POST", body: "{}" });
  toast("Repository refreshed");
  await loadWorkspace();
}

function renderReport(ws) {
  const latestJob = (ws.jobs || [])[0];
  const staleReport = latestJob && latestJob.status === "failed" && ws.report && ws.report.latest_job_id !== latestJob.id;
  const jobNotice = staleReport
    ? `<div class="notice danger"><strong>最新生成失败。</strong><span>下面显示的是上一份成功周报。输入：${escapeHtml(latestJob.input_summary || "")}</span><span>${escapeHtml(latestJob.failure_reason || "")}</span></div>`
    : "";
  const history = (ws.report_history || []).filter((report) => !report.is_current_week);
  $("tab-report").innerHTML = `
    <div class="panel">
      <div class="panel-head"><h2>当前周报</h2><span>Latest successful Markdown</span><button class="primary generate-action" onclick="generateReport()">Regenerate</button></div>
      ${jobNotice}
      ${ws.report ? `<article class="report">${ws.report.content_html}</article>` : "<p>No report generated yet.</p>"}
    </div>
    <div class="panel">
      <div class="panel-head"><h2>历史周报</h2><span>Read-only archive</span></div>
      <div class="report-history">
        ${history.map(renderHistoryReport).join("") || "<p>No historical reports yet.</p>"}
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>生成历史</h2><span>Run metadata only</span></div>
      <table class="table"><thead><tr><th>Trigger</th><th>Provider</th><th>Status</th><th>Input</th><th>Failure</th></tr></thead><tbody>${ws.jobs.map(j => `<tr><td>${escapeHtml(j.trigger_type)}<br>${escapeHtml(formatChinaTime(j.started_at))}</td><td>${escapeHtml(j.provider)}</td><td><span class="status ${j.status}">${j.status}</span></td><td>${escapeHtml(j.input_summary || j.input_snapshot_hash)}</td><td>${escapeHtml(j.failure_reason || "")}</td></tr>`).join("") || "<tr><td colspan='5'>No generation runs.</td></tr>"}</tbody></table>
    </div>
  `;
}

function renderHistoryReport(report) {
  return `
    <details class="history-report">
      <summary><strong>${escapeHtml(report.week_key)}</strong><span>${escapeHtml(formatChinaTime(report.updated_at))}</span><span class="status">read-only</span></summary>
      <article class="report">${report.content_html}</article>
    </details>
  `;
}

function renderRisks(ws) {
  $("tab-risks").innerHTML = `
    <div class="panel">
      <div class="panel-head"><h2>进度和风险</h2><span>Deterministic warnings</span></div>
      <p>Progress status: <span class="status ${ws.progress_status.replace(" ", "-")}">${escapeHtml(ws.progress_status)}</span></p>
      <table class="table"><thead><tr><th>Severity</th><th>Rule</th><th>Title</th><th>Status</th></tr></thead><tbody>${ws.risks.map(r => `<tr><td><span class="status ${r.severity}">${r.severity}</span></td><td>${escapeHtml(r.rule)}</td><td>${escapeHtml(r.title)}<br>${escapeHtml(r.details || "")}</td><td>${escapeHtml(r.status)}</td></tr>`).join("") || "<tr><td colspan='4'>No risks.</td></tr>"}</tbody></table>
    </div>
  `;
}

async function generateReport() {
  await withBusy("正在生成周报", "正在收集本周新增资料、GitHub commits，并等待本地 CLI 返回结果...", async () => {
    document.querySelectorAll(".generate-action").forEach((button) => button.classList.add("is-loading"));
    try {
      toast("Generation started");
      await api(`/api/projects/${state.projectId}/generate`, { method: "POST", body: JSON.stringify({ force: true }) });
      await loadWorkspace();
      toast("Generation finished");
    } finally {
      document.querySelectorAll(".generate-action").forEach((button) => button.classList.remove("is-loading"));
    }
  });
}

async function scheduleCheck() {
  await withBusy("正在检查更新时间点", "正在按中国时区判断本周是否需要重新生成...", async () => {
    await api(`/api/projects/${state.projectId}/schedule-check`, { method: "POST", body: "{}" });
    await loadWorkspace();
    toast("Schedule checked");
  });
}

function switchTab(tab) {
  state.tab = tab;
  document.querySelectorAll(".tabs button").forEach(btn => btn.classList.toggle("active", btn.dataset.tab === tab));
  document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.add("hidden"));
  const el = $(`tab-${tab}`);
  if (el) el.classList.remove("hidden");
}

function input(name, label, value, type = "text") { return `<label>${label}<input name="${name}" type="${type}" value="${escapeAttr(value || "")}"></label>`; }
function timezoneSelect(name, label, value) {
  return `<label>${label}<select name="${name}"><option value="${CHINA_TIMEZONE}" ${(value || CHINA_TIMEZONE) === CHINA_TIMEZONE ? "selected" : ""}>中国标准时间 (Asia/Shanghai)</option></select></label>`;
}
function textarea(name, label, value, cls = "") { return `<label class="${cls}">${label}<textarea name="${name}">${escapeHtml(value || "")}</textarea></label>`; }
function rowItem(item) { return `<tr><td>${escapeHtml(item.title || "")}</td><td>${escapeHtml(item.owner_label || "")}</td><td>${escapeHtml(item.status || "")}</td></tr>`; }
function itemPayload(row) {
  const payload = {};
  row.querySelectorAll("input, select, textarea").forEach((control) => {
    if (control.name) payload[control.name] = control.value;
  });
  return payload;
}
function statusOptions(value) {
  return ["planned", "in_progress", "blocked", "complete"]
    .map((status) => `<option value="${status}" ${sel(value, status)}>${status}</option>`)
    .join("");
}
function sel(value, expected) { return (value || "planned") === expected ? "selected" : ""; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c])); }
function escapeAttr(value) { return escapeHtml(value); }
function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}
function timezoneLabel(value) {
  return (value || CHINA_TIMEZONE) === CHINA_TIMEZONE ? "中国标准时间 (Asia/Shanghai)" : escapeHtml(value);
}
function formatChinaTime(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    timeZone: CHINA_TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}

$("new-project").onclick = () => {
  $("project-form").reset();
  $("project-form").start_date.value = new Date().toISOString().slice(0, 10);
  $("project-dialog").showModal();
};
$("project-form").onsubmit = async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.target).entries());
  const data = await api("/api/projects", { method: "POST", body: JSON.stringify(payload) });
  $("project-dialog").close();
  state.projectId = data.id;
  localStorage.setItem("currentProjectId", String(state.projectId));
  await loadState();
  toast("Project created");
};
$("generate-report").onclick = generateReport;
$("schedule-check").onclick = scheduleCheck;
document.querySelectorAll(".tabs button").forEach(btn => btn.onclick = () => switchTab(btn.dataset.tab));

loadState().catch(err => toast(err.message));

const CHINA_TIMEZONE = "Asia/Shanghai";
const TRACK_ALL_BRANCHES = "*";
// Font Awesome Free 6.7.2, CC BY 4.0: https://fontawesome.com/license/free
const FA_ICONS = {
  gear: {
    viewBox: "0 0 512 512",
    path: "M495.9 166.6c3.2 8.7 .5 18.4-6.4 24.6l-43.3 39.4c1.1 8.3 1.7 16.8 1.7 25.4s-.6 17.1-1.7 25.4l43.3 39.4c6.9 6.2 9.6 15.9 6.4 24.6c-4.4 11.9-9.7 23.3-15.8 34.3l-4.7 8.1c-6.6 11-14 21.4-22.1 31.2c-5.9 7.2-15.7 9.6-24.5 6.8l-55.7-17.7c-13.4 10.3-28.2 18.9-44 25.4l-12.5 57.1c-2 9.1-9 16.3-18.2 17.8c-13.8 2.3-28 3.5-42.5 3.5s-28.7-1.2-42.5-3.5c-9.2-1.5-16.2-8.7-18.2-17.8l-12.5-57.1c-15.8-6.5-30.6-15.1-44-25.4L83.1 425.9c-8.8 2.8-18.6 .3-24.5-6.8c-8.1-9.8-15.5-20.2-22.1-31.2l-4.7-8.1c-6.1-11-11.4-22.4-15.8-34.3c-3.2-8.7-.5-18.4 6.4-24.6l43.3-39.4C64.6 273.1 64 264.6 64 256s.6-17.1 1.7-25.4L22.4 191.2c-6.9-6.2-9.6-15.9-6.4-24.6c4.4-11.9 9.7-23.3 15.8-34.3l4.7-8.1c6.6-11 14-21.4 22.1-31.2c5.9-7.2 15.7-9.6 24.5-6.8l55.7 17.7c13.4-10.3 28.2-18.9 44-25.4l12.5-57.1c2-9.1 9-16.3 18.2-17.8C227.3 1.2 241.5 0 256 0s28.7 1.2 42.5 3.5c9.2 1.5 16.2 8.7 18.2 17.8l12.5 57.1c15.8 6.5 30.6 15.1 44 25.4l55.7-17.7c8.8-2.8 18.6-.3 24.5 6.8c8.1 9.8 15.5 20.2 22.1 31.2l4.7 8.1c6.1 11 11.4 22.4 15.8 34.3zM256 336a80 80 0 1 0 0-160 80 80 0 1 0 0 160z",
  },
  report: {
    viewBox: "0 0 384 512",
    path: "M64 0C28.7 0 0 28.7 0 64V448c0 35.3 28.7 64 64 64H320c35.3 0 64-28.7 64-64V160H256c-17.7 0-32-14.3-32-32V0H64zM256 0V128H384L256 0zM96 224c0-8.8 7.2-16 16-16H272c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16zm0 64c0-8.8 7.2-16 16-16H272c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16zm0 64c0-8.8 7.2-16 16-16H208c8.8 0 16 7.2 16 16s-7.2 16-16 16H112c-8.8 0-16-7.2-16-16z",
  },
};
const state = {
  projects: [],
  projectId: Number(localStorage.getItem("currentProjectId")) || null,
  workspace: null,
  todos: [],
  todoEditorId: null,
  pendingReportProjectId: null,
  pendingDeleteTodoId: null,
  mode: localStorage.getItem("workspaceMode") === "todos" ? "todos" : "reports",
  settingsView: false,
  theme: "blue",
  appearance: "light",
  branchOptions: {},
  tab: "overview",
  sourceTab: "files",
  busy: false,
};

const $ = (id) => document.getElementById(id);

const THEMES = [
  { id: "blue", label: "经典蓝", color: "#2563eb" },
  { id: "graphite", label: "石墨黑", color: "#111827" },
  { id: "green", label: "松石绿", color: "#059669" },
  { id: "purple", label: "雅紫", color: "#7c3aed" },
  { id: "orange", label: "落日橙", color: "#ea580c" },
  { id: "pink", label: "樱粉", color: "#db2777" },
];

function updateThemeColorSurface() {
  const themeColor = document.querySelector?.('meta[name="theme-color"]');
  if (!themeColor || typeof getComputedStyle !== "function") return;
  const surface = getComputedStyle(document.documentElement).backgroundColor;
  if (surface) themeColor.setAttribute("content", surface);
}

function applyTheme(themeId, persist = true) {
  if (!THEMES.some((theme) => theme.id === themeId)) themeId = "blue";
  state.theme = themeId;
  const root = document.documentElement;
  if (root) root.dataset.theme = themeId;
  document.querySelectorAll(".theme-swatch").forEach((btn) => btn.classList.toggle("active", btn.dataset.themeId === themeId));
  if (persist) localStorage.setItem("appTheme", themeId);
  updateThemeColorSurface();
}

function applyAppearance(mode, persist = true) {
  const normalized = mode === "dark" ? "dark" : "light";
  state.appearance = normalized;
  const root = document.documentElement;
  if (root) root.dataset.mode = normalized;
  document.querySelectorAll(".mode-option").forEach((btn) => btn.classList.toggle("active", btn.dataset.modeOption === normalized));
  if (persist) localStorage.setItem("appAppearance", normalized);
  updateThemeColorSurface();
}
applyTheme(localStorage.getItem("appTheme") || "blue", false);
applyAppearance(localStorage.getItem("appAppearance") || "light", false);

function renderAppearanceSettings() {
  const swatches = $("appearance-swatches");
  if (!swatches) return;
  swatches.innerHTML = THEMES.map((theme) =>
    `<button type="button" class="theme-swatch${theme.id === state.theme ? " active" : ""}" data-theme-id="${theme.id}" onclick="applyTheme('${theme.id}')"><span class="theme-swatch-dot" style="background:${theme.color}"></span>${theme.label}</button>`).join("");
}
renderAppearanceSettings();

async function api(path, options = {}) {
  const res = await fetch(path, {
    cache: "no-store",
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
  await switchAppMode(state.mode, false);
}

async function loadWorkspace() {
  updateWorkspace(await api(`/api/projects/${state.projectId}/workspace`));
}

function updateWorkspace(workspace) {
  state.workspace = workspace;
  render();
}

async function loadTodos() {
  const data = await api("/api/todos");
  state.todos = data.todos || [];
  renderTodoBoard();
}

function updateTodos(data) {
  state.todos = data.todos || [];
  renderTodoBoard();
}

function syncWorkspaceView() {
  const settings = state.settingsView;
  $("settings-view").classList.toggle("hidden", !settings);
  $("report-view").classList.toggle("hidden", settings || state.mode !== "reports");
  $("todo-view").classList.toggle("hidden", settings || state.mode !== "todos");
  document.querySelectorAll("[data-mode-tab]").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.modeTab === (settings ? "settings" : state.mode));
  });
}

function toggleSettingsView(force) {
  state.settingsView = typeof force === "boolean" ? force : !state.settingsView;
  const showingTodos = state.mode === "todos" && !state.settingsView;
  document.body.classList.toggle("todo-mode", showingTodos);
  $("project-sidebar").classList.toggle("hidden", showingTodos);
  syncWorkspaceView();
  updateThemeColorSurface();
}

async function switchAppMode(mode, persist = true) {
  state.mode = mode === "todos" ? "todos" : "reports";
  state.settingsView = false;
  if (persist) localStorage.setItem("workspaceMode", state.mode);
  const showingTodos = state.mode === "todos";
  document.body.classList.toggle("todo-mode", showingTodos);
  $("project-sidebar").classList.toggle("hidden", showingTodos);
  syncWorkspaceView();
  updateThemeColorSurface();
  $("page-current-label").textContent = showingTodos ? "TODO" : "周报";
  $("page-target-label").textContent = showingTodos ? "周报" : "TODO";
  $("page-corner").setAttribute("aria-label", `当前页面：${showingTodos ? "TODO" : "周报"}；切换到${showingTodos ? "周报" : "TODO"}`);
  if (persist) playPageTurn();
  if (showingTodos) {
    await loadTodos();
  } else if (state.projectId) {
    await loadWorkspace();
  }
}

function playPageTurn() {
  const corner = $("page-corner");
  corner.classList.remove("turning");
  void corner.offsetWidth;
  corner.classList.add("turning");
  setTimeout(() => corner.classList.remove("turning"), 430);
  const entering = document.querySelectorAll(state.mode === "todos" ? "#todo-view" : "#report-view, #project-sidebar");
  entering.forEach((el) => {
    el.classList.remove("view-enter");
    void el.offsetWidth;
    el.classList.add("view-enter");
    setTimeout(() => el.classList.remove("view-enter"), 320);
  });
}

function renderTodoBoard() {
  const board = $("todo-board");
  if (!board) return;
  const columns = [
    { status: "todo", title: "待办" },
    { status: "doing", title: "进行中" },
    { status: "closed", title: "已关闭" },
  ];
  const savedScrollLeft = board.scrollLeft;
  board.innerHTML = columns.map((column) => {
    const items = state.todos.filter((todo) => todo.status === column.status);
    return `
      <section class="todo-column todo-column-${column.status}">
        <div class="todo-column-head"><h2>${column.title}</h2><span>${items.length}</span></div>
        <div class="todo-card-list">
          ${items.map(renderTodoCard).join("")}
          ${column.status === "todo" ? renderTodoDraft() : (!items.length ? `<p class="todo-empty">暂无${column.title}事项</p>` : "")}
        </div>
      </section>
    `;
  }).join("");
  ensureTodoBoardDots(board);
  const dots = $("todo-board-dots");
  if (dots) {
    dots.innerHTML = columns.map((column, index) =>
      `<button type="button" data-column="${index}" aria-label="${column.title}"></button>`).join("");
    board.scrollLeft = savedScrollLeft;
    syncTodoBoardDots(board);
  }
}

function ensureTodoBoardDots(board) {
  if ($("todo-board-dots")) return;
  const dots = document.createElement("div");
  dots.id = "todo-board-dots";
  dots.className = "todo-board-dots";
  dots.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-column]");
    if (!button) return;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    board.scrollTo({ left: Number(button.dataset.column) * board.clientWidth, behavior: reduceMotion ? "auto" : "smooth" });
  });
  board.after(dots);
  board.addEventListener("scroll", () => {
    if (board.todoDotRaf) return;
    board.todoDotRaf = requestAnimationFrame(() => {
      board.todoDotRaf = 0;
      syncTodoBoardDots(board);
    });
  }, { passive: true });
}

function syncTodoBoardDots(board) {
  const dots = $("todo-board-dots");
  if (!dots) return;
  const index = Math.round(board.scrollLeft / (board.clientWidth || 1));
  dots.querySelectorAll("button").forEach((dot, i) => dot.classList.toggle("active", i === index));
}

function renderTodoCard(todo) {
  if (state.todoEditorId === todo.id) return renderTodoEditor(todo);
  const openActions = todo.status === "todo"
    ? `<button onclick="event.stopPropagation(); moveTodo(${todo.id}, 'doing')">开始</button><button class="primary" onclick="event.stopPropagation(); openCloseTodo(${todo.id})">关闭</button>`
    : todo.status === "doing"
      ? `<button onclick="event.stopPropagation(); moveTodo(${todo.id}, 'todo')">移回待办</button><button class="primary" onclick="event.stopPropagation(); openCloseTodo(${todo.id})">关闭</button>`
      : "";
  const archive = todo.project_id
    ? `<button onclick="event.stopPropagation(); openTodoMaterial(${todo.project_id}, ${todo.material_id})">查看项目资料</button>`
    : "";
  const remove = todo.status === "closed"
    ? `<button class="danger" onclick="event.stopPropagation(); deleteTodo(${todo.id})">删除</button>`
    : "";
  const editable = true;
  return `
    <article class="todo-card ${editable ? "todo-card-editable" : "todo-card-closed"}" ${editable ? `onclick="if (!event.target.closest('a')) beginTodoEdit(${todo.id})" tabindex="0" onkeydown="if (event.key === 'Enter' && !event.target.closest('a')) beginTodoEdit(${todo.id})"` : ""}>
      <h3>${escapeHtml(todo.title)}</h3>
      ${todo.description ? `<div class="todo-markdown">${todo.description_html}</div>` : ""}
      ${todo.status === "closed" ? `
        <div class="todo-close-reason"><span>关闭原因</span><div class="todo-markdown">${todo.close_reason_html}</div></div>
        ${todo.project_name ? `<span class="todo-project">${escapeHtml(todo.project_name)}</span>` : ""}
      ` : ""}
      <div class="todo-card-meta">更新于 ${escapeHtml(formatChinaTime(todo.updated_at))}</div>
      ${(openActions || archive || remove) ? `<div class="todo-card-actions">${openActions}${archive}${remove}</div>` : ""}
    </article>
  `;
}

function renderTodoDraft() {
  if (state.todoEditorId === "draft") {
    return renderTodoEditor({ id: "draft", title: "", description: "" });
  }
  return `
    <button class="todo-draft" type="button" onclick="beginTodoEdit('draft')">
      <strong>＋ 添加 TODO</strong>
      <span>点击直接编辑 · 支持 Markdown</span>
    </button>
  `;
}

function renderTodoEditor(todo) {
  const id = todo.id;
  return `
    <article class="todo-card todo-card-editor" data-todo-editor="${id}" onfocusout="finishTodoEdit(event, '${id}')" onkeydown="handleTodoEditorKey(event, '${id}')">
      <input id="todo-editor-title-${id}" class="todo-title-input" maxlength="200" placeholder="TODO 标题" value="${escapeAttr(todo.title || "")}">
      <textarea id="todo-editor-description-${id}" class="todo-description-input" maxlength="4000" placeholder="补充说明，支持 Markdown">${escapeHtml(todo.description || "")}</textarea>
      <span class="todo-autosave-hint">离开卡片后自动保存</span>
    </article>
  `;
}

function beginTodoEdit(id) {
  if (state.todoEditorId === id) return;
  state.todoEditorId = id;
  renderTodoBoard();
  requestAnimationFrame(() => {
    const title = $(`todo-editor-title-${id}`);
    if (title) title.focus();
  });
}

function handleTodoEditorKey(event, id) {
  if (event.key === "Escape") {
    event.preventDefault();
    state.todoEditorId = null;
    renderTodoBoard();
  } else if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
    event.preventDefault();
    event.currentTarget.querySelector("textarea")?.blur();
    event.currentTarget.querySelector("input")?.blur();
  }
}

function finishTodoEdit(event, id) {
  const card = event.currentTarget;
  setTimeout(() => {
    if (card.contains(document.activeElement)) return;
    saveTodoEditor(id).catch((error) => toast(error.message));
  }, 0);
}

async function saveTodoEditor(rawId) {
  if (String(state.todoEditorId) !== String(rawId)) return;
  const title = $(`todo-editor-title-${rawId}`)?.value.trim() || "";
  const description = $(`todo-editor-description-${rawId}`)?.value || "";
  if (!title) {
    if (rawId === "draft") {
      state.todoEditorId = null;
      renderTodoBoard();
      return;
    }
    toast("TODO 标题不能为空");
    $(`todo-editor-title-${rawId}`)?.focus();
    return;
  }
  const path = rawId === "draft" ? "/api/todos" : `/api/todos/${Number(rawId)}`;
  const method = rawId === "draft" ? "POST" : "PUT";
  const todo = rawId === "draft" ? null : state.todos.find((item) => item.id === Number(rawId));
  const payload = { title, description };
  if (todo) payload.status = todo.status;
  const data = await api(path, { method, body: JSON.stringify(payload) });
  state.todoEditorId = null;
  updateTodos(data);
  toast(rawId === "draft" ? "TODO 已创建" : "TODO 已自动保存");
}

async function moveTodo(id, status) {
  updateTodos(await api(`/api/todos/${id}`, {
    method: "PUT",
    body: JSON.stringify({ status }),
  }));
}

function deleteTodo(id) {
  const todo = state.todos.find((item) => item.id === id);
  if (!todo) return;
  state.pendingDeleteTodoId = id;
  $("todo-delete-title").textContent = todo.title;
  $("todo-delete-dialog").showModal();
}

async function runTodoDelete() {
  const id = state.pendingDeleteTodoId;
  state.pendingDeleteTodoId = null;
  if (!id) return;
  updateTodos(await api(`/api/todos/${id}`, { method: "DELETE" }));
  toast("TODO 已删除");
}

function openCloseTodo(id) {
  const todo = state.todos.find((item) => item.id === id);
  if (!todo) return;
  $("close-todo-id").value = String(id);
  $("close-todo-title").textContent = todo.title;
  $("close-todo-project").innerHTML = `
    <option value="">不归属项目</option>
    ${state.projects.map((project) => `<option value="${project.id}">${escapeHtml(project.name)}</option>`).join("")}
  `;
  $("close-todo-form").elements.reason.value = "";
  $("close-todo-dialog").showModal();
}

async function openTodoMaterial(projectId, materialId) {
  state.projectId = Number(projectId);
  localStorage.setItem("currentProjectId", String(state.projectId));
  await switchAppMode("reports");
  switchTab("sources");
  switchSourceTab("manual");
  if (materialId) await previewMaterial(Number(materialId));
}

function projectRowHtml(p) {
  return `
    <div class="project-row ${p.id === state.projectId ? "active" : ""}">
      <button class="project-item" data-project="${p.id}" aria-label="${escapeAttr(`${p.name}，${projectDisplayStatus(p)}`)}">
        ${statusDot(projectDisplayStatus(p), "project-item-status")}
        <strong>${escapeHtml(p.name)}</strong>
      </button>
      <button class="project-generate" data-project-generate="${p.id}" aria-label="为 ${escapeAttr(p.name)} 生成周报" title="生成周报">
        ${faIcon("report")}
      </button>
      <button class="project-settings ${p.id === state.projectId && state.tab === "settings" ? "active" : ""}" data-project-settings="${p.id}" aria-label="打开 ${escapeAttr(p.name)} 的设置" title="项目设置">
        ${faIcon("gear")}
      </button>
    </div>
  `;
}

function renderProjects() {
  const rows = state.projects.map(projectRowHtml).join("");
  $("project-list").innerHTML = rows;
  $("sheet-project-list").innerHTML = rows +
    `<button type="button" class="sheet-add-row" data-add-project><span aria-hidden="true">＋</span>新建项目</button>`;
  const addProjectButton = document.querySelector("[data-add-project]");
  if (addProjectButton) addProjectButton.onclick = openNewProjectDialog;
  document.querySelectorAll("[data-project]").forEach(btn => {
    btn.onclick = async () => {
      closeProjectSheet();
      state.projectId = Number(btn.dataset.project);
      localStorage.setItem("currentProjectId", String(state.projectId));
      await loadWorkspace();
      renderProjects();
    };
  });
  document.querySelectorAll("[data-project-settings]").forEach(btn => {
    btn.onclick = async () => {
      closeProjectSheet();
      const projectId = Number(btn.dataset.projectSettings);
      if (state.projectId !== projectId) {
        state.projectId = projectId;
        localStorage.setItem("currentProjectId", String(state.projectId));
        await loadWorkspace();
      }
      switchTab("settings");
      renderProjects();
    };
  });
  document.querySelectorAll("[data-project-generate]").forEach(btn => {
    btn.onclick = () => {
      closeProjectSheet();
      confirmProjectGeneration(Number(btn.dataset.projectGenerate));
    };
  });
}

function closeProjectSheet() {
  const sheet = $("project-sheet");
  if (sheet.open) sheet.close();
}

function render() {
  const ws = state.workspace;
  $("empty-state").classList.toggle("hidden", !!ws);
  $("workspace").classList.toggle("hidden", !ws);
  if (!ws) return;
  $("project-title").textContent = ws.project.name;
  $("project-bar-name").textContent = ws.project.name;
  $("open-project-bar").classList.remove("hidden");
  const projectBarDot = $("project-bar-dot");
  projectBarDot.className = `status-dot ${statusTone(ws.progress_status)}`;
  projectBarDot.title = ws.progress_status;
  $("project-meta").textContent = ws.week_key;
  const projectStatusDot = $("project-status-dot");
  projectStatusDot.className = `status-dot ${statusTone(ws.progress_status)}`;
  projectStatusDot.title = ws.progress_status;
  projectStatusDot.setAttribute("aria-label", `项目状态：${ws.progress_status}`);
  renderProjects();
  renderOverview(ws);
  renderSettings(ws);
  renderPlan(ws);
  renderUpdates(ws);
  renderSources(ws);
  renderReport(ws);
  renderRisks(ws);
  ensureTableScrollContainers();
  switchTab(state.tab);
}

function ensureTableScrollContainers() {
  document.querySelectorAll("table.table").forEach((table) => {
    if (table.parentElement && table.parentElement.classList.contains("table-scroll")) return;
    const scroller = document.createElement("div");
    scroller.className = "table-scroll";
    table.parentNode.insertBefore(scroller, table);
    scroller.appendChild(table);
  });
}

function renderOverview(ws) {
  $("tab-overview").innerHTML = `
    <div class="status-strip">
      <div class="metric"><span>项目周</span><strong>${ws.week_key}</strong><small>当前项目周</small></div>
      <div class="metric"><span>进度状态</span><strong>${escapeHtml(statusLabel(ws.progress_status))}</strong><small>确定性规则计算</small></div>
      <div class="metric"><span>活跃风险</span><strong>${ws.risks.filter(r => r.status === "active").length}</strong><small>当前活跃</small></div>
      <div class="metric"><span>资料源</span><strong>${ws.materials.length + ws.repos.length}</strong><small>资料 + 仓库</small></div>
    </div>
    <div class="grid-2">
      <div class="panel">
        <div class="panel-head"><h2>当前计划</h2><span>计划基线</span></div>
        <p>${escapeHtml(ws.plan.objectives || "暂无目标。")}</p>
        <table class="table"><tbody>${ws.plan.milestones.map(rowItem).join("") || "<tr><td>暂无里程碑。</td></tr>"}</tbody></table>
      </div>
      <div class="panel">
        <div class="panel-head"><h2>当前周报</h2><span>正式周报</span></div>
        ${ws.report ? `
          <div class="overview-report-summary">
            <span>周报摘要</span>
            <p>${escapeHtml(reportSummary(ws.report))}</p>
          </div>
          <p class="report-updated">更新于 ${escapeHtml(formatChinaTime(ws.report.updated_at))}</p>
        ` : "<p>当前项目周还没有生成周报。</p>"}
        <div class="row"><button onclick="switchTab('report')">打开周报</button></div>
      </div>
    </div>
  `;
}

function renderSettings(ws) {
  const p = ws.project;
  $("tab-settings").innerHTML = `
    <form id="settings-form" class="panel form-grid">
      <div class="panel-head wide"><h2>项目设置</h2><span>项目与报告配置</span></div>
      ${input("name", "名称", p.name)}
      ${input("status", "状态", p.status)}
      ${input("start_date", "开始日期", p.start_date, "date")}
      ${input("end_date", "结束日期", p.end_date || "", "date")}
      ${timezoneSelect("timezone", "时区", p.timezone)}
      <label>生成器<select name="report_provider"><option value="codex" ${p.report_provider === "codex" ? "selected" : ""}>Codex CLI</option><option value="claude" ${p.report_provider === "claude" ? "selected" : ""}>Claude Code CLI</option></select></label>
      ${textarea("description", "描述", p.description, "wide")}
      ${textarea("manual_background", "背景", p.manual_background, "wide")}
      ${textarea("manual_objectives", "目标", p.manual_objectives, "wide")}
      ${textarea("manual_constraints", "约束", p.manual_constraints, "wide")}
      ${textarea("system_prompt", "系统提示词", p.system_prompt, "wide")}
      ${textarea("report_template", "项目周报模板", p.report_template, "wide")}
      <div class="wide panel">
        <div class="panel-head"><h3>更新时间点</h3><span>同一项目周内覆盖当前周报</span></div>
        <div id="schedule-list">${renderSchedules(ws.schedules, p.timezone)}</div>
        <button type="button" onclick="addSchedule()">+ 添加时间点</button>
      </div>
      <div class="wide row"><button class="primary">保存设置</button></div>
    </form>
    <div class="panel">
      <div class="panel-head"><h2>Git 仓库</h2><span>GitHub / GitLab，本周 commits 会进入生成上下文</span></div>
      <div class="row">
        <select id="repo-mode-input" onchange="onRepoModeChange()" aria-label="Git 模式"><option value="github">GitHub</option><option value="gitlab">GitLab</option></select>
        <input id="repo-input" placeholder="owner/repo">
        <input id="repo-server-input" placeholder="GitLab 服务器地址，如 https://gitlab.example.com" class="hidden">
        <input id="repo-notes-input" placeholder="补充说明，例如正式名称、模块边界">
        <button type="button" onclick="addRepo()">添加仓库</button>
      </div>
      <table class="table"><thead><tr><th>仓库</th><th>跟踪分支</th><th>补充说明</th><th>状态</th><th>操作</th></tr></thead><tbody>${ws.repos.map(renderRepoRow).join("") || "<tr><td colspan='5'>暂无仓库。</td></tr>"}</tbody></table>
    </div>
  `;
  $("settings-form").onsubmit = saveSettings;
  onRepoModeChange();
}

function onRepoModeChange() {
  const gitlab = $("repo-mode-input") && $("repo-mode-input").value === "gitlab";
  if (!$("repo-server-input")) return;
  $("repo-server-input").classList.toggle("hidden", !gitlab);
  $("repo-input").placeholder = gitlab ? "group/project 或 group/sub-group/project" : "owner/repo";
}

function renderRepoRow(r) {
  const enabled = Number(r.enabled) !== 0;
  const gitlab = r.git_mode === "gitlab";
  const modeLabel = gitlab ? "GitLab" : "GitHub";
  const target = gitlab
    ? `<input id="repo-server-${r.id}" class="table-input" placeholder="https://gitlab.com（自建实例可改）" value="${escapeAttr(r.gitlab_server || "")}">`
    : "";
  return `
    <tr class="${enabled ? "" : "repo-row-disabled"}">
      <td data-label="仓库"><span class="status">${modeLabel}</span><br>${escapeHtml(r.repo)}${target ? `<br>${target}` : ""}</td>
      <td data-label="跟踪分支">${renderBranchPicker(r)}</td>
      <td data-label="补充说明"><textarea id="repo-notes-${r.id}" class="table-textarea">${escapeHtml(r.notes || "")}</textarea></td>
      <td data-label="启用">${enabled
        ? `<span class="status ${r.status}">${escapeHtml(r.status)}</span><br>${escapeHtml(r.status_message || "")}`
        : `<span class="status disabled">已停用</span><br>不参与周报生成`}</td>
      <td data-label="操作"><div class="table-actions"><label class="switch" title="${enabled ? "已启用 · 参与周报生成" : "已停用 · 不参与周报生成"}"><input type="checkbox" aria-label="启用或停用该仓库" ${enabled ? "checked" : ""} onchange="toggleRepo(${r.id}, this.checked)"><span class="switch-slider"></span></label><button type="button" onclick="saveRepoNotes(${r.id})">保存</button><button type="button" onclick="refreshRepo(${r.id})">刷新</button><button type="button" class="danger" onclick="deleteRepo(${r.id})">删除</button></div></td>
    </tr>
  `;
}

function renderBranchPicker(repo) {
  const selected = repo.tracked_branches && repo.tracked_branches.length ? repo.tracked_branches : ["main"];
  const options = branchOptionsFor(repo);
  const summary = selected.includes(TRACK_ALL_BRANCHES) ? "All" : selected.join(", ");
  return `
    <details class="branch-picker" id="branch-picker-${repo.id}">
      <summary>${escapeHtml(summary)}</summary>
      <div class="branch-menu">
        <div class="branch-actions"><button type="button" onclick="loadRepoBranches(${repo.id})">加载分支</button></div>
        <div class="branch-options">
          ${options.map(branch => `
            <label class="branch-option">
              <input type="checkbox" value="${escapeAttr(branch)}" ${selected.includes(branch) ? "checked" : ""} onchange="toggleAllBranches(${repo.id}, this)">
              <span>${branch === TRACK_ALL_BRANCHES ? "All" : escapeHtml(branch)}</span>
            </label>
          `).join("")}
        </div>
      </div>
    </details>
  `;
}

function branchOptionsFor(repo) {
  const selected = repo.tracked_branches && repo.tracked_branches.length ? repo.tracked_branches : ["main"];
  const loaded = state.branchOptions[repo.id] || [];
  return [TRACK_ALL_BRANCHES, ...selected, ...loaded].filter((branch, index, all) => branch && all.indexOf(branch) === index);
}

function toggleAllBranches(id, changed) {
  const picker = $(`branch-picker-${id}`);
  if (!picker || !changed.checked) return;
  picker.querySelectorAll("input[type='checkbox']").forEach(input => {
    if (input !== changed && (changed.value === TRACK_ALL_BRANCHES || input.value === TRACK_ALL_BRANCHES)) {
      input.checked = false;
    }
  });
}

function renderSchedules(schedules, timezone) {
  const rows = schedules.length ? schedules : [{ weekday: 5, local_time: "18:00", timezone: CHINA_TIMEZONE, enabled: 1 }];
  return rows.map((s) => {
    const enabled = Number(s.enabled) !== 0;
    return `
    <div class="row schedule-row${enabled ? "" : " schedule-row-disabled"}">
      <label class="switch" title="${enabled ? "已启用" : "已停用"}"><input type="checkbox" data-schedule-enabled ${enabled ? "checked" : ""}><span class="switch-slider"></span></label>
      <label>星期 <input name="schedule_weekday" type="number" min="1" max="7" value="${s.weekday}"></label>
      <label>时间 <input name="schedule_time" value="${escapeHtml(s.local_time)}"></label>
      ${timezoneSelect("schedule_timezone", "时区", s.timezone)}
      <button type="button" class="danger" onclick="this.closest('.schedule-row').remove()">移除</button>
      <small class="schedule-last-fire">${s.last_checked_at ? `上次触发 ${escapeHtml(formatChinaTime(s.last_checked_at))}` : "尚未触发"}</small>
    </div>
  `;}).join("");
}

function addSchedule() {
  $("schedule-list").insertAdjacentHTML("beforeend", renderSchedules([{ weekday: 5, local_time: "18:00", timezone: CHINA_TIMEZONE }], CHINA_TIMEZONE));
}

async function saveSettings(event) {
  event.preventDefault();
  const fd = new FormData(event.target);
  const schedules = Array.from(document.querySelectorAll("#schedule-list .schedule-row"))
    .map(row => ({
      enabled: row.querySelector("input[data-schedule-enabled]").checked,
      weekday: Number(row.querySelector("input[name='schedule_weekday']").value),
      local_time: row.querySelector("input[name='schedule_time']").value,
      timezone: row.querySelector("select[name='schedule_timezone']").value,
    }))
    .filter(s => s.local_time);
  const payload = Object.fromEntries(fd.entries());
  payload.schedules = schedules;
  await api(`/api/projects/${state.projectId}/settings`, { method: "PUT", body: JSON.stringify(payload) });
  toast("设置已保存");
  await loadWorkspace();
}

function renderPlan(ws) {
  $("tab-plan").innerHTML = `
    <form id="plan-form" class="panel">
      <div class="panel-head"><h2>项目计划</h2><span>里程碑与交付物</span></div>
      ${textarea("objectives", "目标", ws.plan.objectives)}
      <h3>里程碑</h3>
      <div id="milestones">${renderPlanItems(ws.plan.milestones)}</div>
      <button type="button" onclick="addPlanItem('milestones')">+ 添加里程碑</button>
      <h3>交付物</h3>
      <div id="deliverables">${renderPlanItems(ws.plan.deliverables)}</div>
      <button type="button" onclick="addPlanItem('deliverables')">+ 添加交付物</button>
      <div class="row"><button class="primary">保存计划</button></div>
    </form>
    <form id="outcome-form" class="panel">
      <div class="panel-head"><h2>本周计划产出</h2><span>${escapeHtml(ws.week_key)}</span></div>
      <div id="outcomes">${renderOutcomes(ws.outcomes)}</div>
      <button type="button" onclick="addOutcome()">+ 添加产出</button>
      <div class="row"><button class="primary">保存产出</button></div>
    </form>
  `;
  $("plan-form").onsubmit = savePlan;
  $("outcome-form").onsubmit = saveOutcomes;
}

function renderPlanItems(items) {
  return (items.length ? items : [{ title: "", status: "planned", owner_label: "", target_date: "" }]).map(item => `
    <div class="row plan-item">
      <input name="title" placeholder="标题" value="${escapeAttr(item.title || "")}">
      <input name="owner_label" placeholder="负责人" value="${escapeAttr(item.owner_label || "")}">
      <input name="target_date" type="date" value="${escapeAttr(item.target_date || "")}">
      <select name="status">${statusOptions(item.status)}</select>
      <button type="button" class="danger" onclick="this.closest('.plan-item').remove()">移除</button>
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
  toast("计划已保存");
  await loadWorkspace();
}

function renderOutcomes(items) {
  return (items.length ? items : [{ title: "", details: "", status: "planned", owner_label: "" }]).map(item => `
    <div class="row outcome-item">
      <input name="title" placeholder="产出" value="${escapeAttr(item.title || "")}">
      <input name="owner_label" placeholder="负责人" value="${escapeAttr(item.owner_label || "")}">
      <select name="status">${statusOptions(item.status)}</select>
      <input name="details" placeholder="说明" value="${escapeAttr(item.details || "")}">
      <button type="button" class="danger" onclick="this.closest('.outcome-item').remove()">移除</button>
    </div>
  `).join("");
}

function addOutcome() { $("outcomes").insertAdjacentHTML("beforeend", renderOutcomes([{ title: "", status: "planned" }])); }

async function saveOutcomes(event) {
  event.preventDefault();
  const outcomes = Array.from($("outcomes").querySelectorAll(".outcome-item")).map(row => itemPayload(row)).filter(i => i.title);
  await api(`/api/projects/${state.projectId}/weekly-outcomes`, { method: "PUT", body: JSON.stringify({ outcomes }) });
  toast("产出已保存");
  await loadWorkspace();
}

function renderUpdates(ws) {
  const u = ws.weekly_update || {};
  $("tab-updates").innerHTML = `
    <form id="update-form" class="panel form-grid">
      <div class="panel-head wide"><h2>本周进展</h2><span>${escapeHtml(ws.week_key)}</span></div>
      ${textarea("completed", "已完成", u.completed || "", "wide")}
      ${textarea("in_progress", "进行中", u.in_progress || "", "wide")}
      ${textarea("blockers", "阻塞事项", u.blockers || "", "wide")}
      ${textarea("risks", "风险", u.risks || "", "wide")}
      ${textarea("next_steps", "下一步计划", u.next_steps || "", "wide")}
      <div class="wide row"><button class="primary">保存进展</button></div>
    </form>
  `;
  $("update-form").onsubmit = async (event) => {
    event.preventDefault();
    await api(`/api/projects/${state.projectId}/weekly-update`, { method: "PUT", body: JSON.stringify(Object.fromEntries(new FormData(event.target).entries())) });
    toast("本周进展已保存");
    await loadWorkspace();
  };
}

function renderSources(ws) {
  $("tab-sources").innerHTML = `
    <div class="source-tabs" role="tablist" aria-label="资料类型">
      <button type="button" data-source-tab="files" role="tab" onclick="switchSourceTab('files')">文件资料</button>
      <button type="button" data-source-tab="manual" role="tab" onclick="switchSourceTab('manual')">手工资料</button>
    </div>
    <section id="source-files" class="source-view" role="tabpanel">
      <div class="panel source-panel">
        <div class="panel-head"><h2>文件资料</h2><span>本周新增资料会进入生成上下文</span></div>
        <label id="material-dropzone" class="upload-dropzone" for="material-file" role="button" tabindex="0">
          <input id="material-file" class="visually-hidden" type="file" accept=".md,.markdown,.txt,.pdf" multiple>
          <span class="upload-icon" aria-hidden="true">↑</span>
          <strong>拖入文件，或点击选择</strong>
          <span id="material-selection">支持 Markdown、纯文本和 PDF，可多选</span>
        </label>
        <div class="upload-actions">
          <button class="primary" type="button" onclick="uploadMaterial()">上传所选文件</button>
        </div>
        <table class="table material-table"><thead><tr><th>文件</th><th>提取</th><th>摘要</th><th>更新时间</th><th>操作</th></tr></thead><tbody>${ws.materials.filter(m => m.source_type !== "manual").map(renderUploadedMaterialRow).join("") || "<tr><td colspan='5'>暂无上传资料。</td></tr>"}</tbody></table>
      </div>
    </section>
    <section id="source-manual" class="source-view hidden" role="tabpanel">
      <div class="panel source-panel">
        <div class="panel-head"><h2>手工资料</h2><span>仅本周录入的资料可以修改</span></div>
        <div class="manual-material-form">
          <input id="manual-material-title" placeholder="资料标题">
          <textarea id="manual-material-content" placeholder="输入本周新增的背景、决策、会议记录或补充资料"></textarea>
          <button onclick="saveManualMaterial()">保存手工资料</button>
        </div>
        <table class="table"><thead><tr><th>标题</th><th>内容</th><th>创建时间</th><th>更新时间</th><th>操作</th></tr></thead><tbody>${ws.materials.filter(m => m.source_type === "manual").map(renderManualMaterialRow).join("") || "<tr><td colspan='5'>暂无手工资料。</td></tr>"}</tbody></table>
      </div>
    </section>
  `;
  switchSourceTab(state.sourceTab);
  setupMaterialDropzone();
}

function switchSourceTab(tab) {
  state.sourceTab = tab;
  document.querySelectorAll("[data-source-tab]").forEach((button) => {
    const active = button.dataset.sourceTab === tab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  ["files", "manual"].forEach((name) => {
    const view = $(`source-${name}`);
    if (view) view.classList.toggle("hidden", name !== tab);
  });
}

function setupMaterialDropzone() {
  const dropzone = $("material-dropzone");
  const input = $("material-file");
  if (!dropzone || !input) return;
  const stopDrag = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };
  ["dragenter", "dragover"].forEach((name) => dropzone.addEventListener(name, (event) => {
    stopDrag(event);
    dropzone.classList.add("is-dragging");
  }));
  ["dragleave", "drop"].forEach((name) => dropzone.addEventListener(name, (event) => {
    stopDrag(event);
    dropzone.classList.remove("is-dragging");
  }));
  dropzone.addEventListener("drop", (event) => {
    if (!event.dataTransfer || !event.dataTransfer.files.length) return;
    input.files = event.dataTransfer.files;
    updateMaterialSelection();
  });
  dropzone.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    input.click();
  });
  input.addEventListener("change", updateMaterialSelection);
}

function updateMaterialSelection() {
  const files = Array.from($("material-file")?.files || []);
  const label = $("material-selection");
  if (!label) return;
  label.textContent = files.length
    ? `已选择 ${files.length} 个文件：${files.map((file) => file.name).join("、")}`
    : "支持 Markdown、纯文本和 PDF，可多选";
}

function renderUploadedMaterialRow(m) {
  const extractionMessage = m.extraction_error ? `<div class="material-message">${escapeHtml(m.extraction_error)}</div>` : "";
  const summaryMessage = m.summary_error ? `<div class="material-message">AI 摘要失败，当前显示回退摘要：${escapeHtml(m.summary_error)}</div>` : "";
  return `<tr>
    <td data-label="文件"><strong>${escapeHtml(m.filename)}</strong><small>${formatBytes(m.size_bytes)}</small></td>
    <td data-label="提取"><span class="status ${m.extraction_status}">${escapeHtml(m.extraction_status)}</span>${extractionMessage}</td>
    <td data-label="摘要"><textarea id="material-summary-${m.id}" class="table-textarea summary-editor">${escapeHtml(m.summary || "")}</textarea>${summaryMessage}</td>
    <td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}<small><span class="status ${m.summary_status}">${escapeHtml(m.summary_status)}</span></small></td>
    <td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button><button onclick="updateMaterialSummary(${m.id})">保存摘要</button>${m.deletable ? `<button class="danger" onclick="deleteMaterial(${m.id})">删除</button>` : ""}</div></td>
  </tr>`;
}

function renderManualMaterialRow(m) {
  const content = escapeHtml(m.content || "");
  if (m.editable) {
    return `<tr><td data-label="标题"><input id="manual-title-${m.id}" value="${escapeAttr(m.filename)}"></td><td data-label="内容"><textarea id="manual-content-${m.id}" class="table-textarea material-editor">${content}</textarea></td><td data-label="创建时间">${escapeHtml(formatChinaTime(m.created_at))}</td><td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}</td><td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button><button onclick="updateManualMaterial(${m.id})">保存</button><button class="danger" onclick="deleteMaterial(${m.id})">删除</button></div></td></tr>`;
  }
  return `<tr><td data-label="标题">${escapeHtml(m.filename)}</td><td data-label="内容"><div class="locked-material">${content}</div></td><td data-label="创建时间">${escapeHtml(formatChinaTime(m.created_at))}</td><td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}</td><td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button><span class="status">已锁定</span></div></td></tr>`;
}

async function previewMaterial(id) {
  const dialog = $("material-preview-dialog");
  $("material-preview-title").textContent = "正在加载资料…";
  $("material-preview-meta").textContent = "";
  resetMaterialPreview();
  dialog.showModal();
  try {
    const material = await api(`/api/projects/${state.projectId}/materials/${id}`);
    $("material-preview-title").textContent = material.filename;
    $("material-preview-meta").textContent = `${material.source_type === "manual" ? "手工资料" : material.content_type} · ${formatBytes(material.size_bytes)} · ${material.extraction_status}`;
    if (material.preview_kind === "pdf") {
      const frame = $("material-preview-pdf");
      frame.src = `/api/projects/${state.projectId}/materials/${id}/content`;
      frame.classList.remove("hidden");
    } else if (material.preview_kind === "markdown") {
      const markdown = $("material-preview-markdown");
      markdown.innerHTML = material.content_html || "<p>暂无可预览的内容</p>";
      markdown.classList.remove("hidden");
    } else {
      const text = $("material-preview-content");
      text.textContent = material.content || "暂无可预览的文本内容";
      text.classList.remove("hidden");
    }
  } catch (error) {
    $("material-preview-title").textContent = "资料预览失败";
    const text = $("material-preview-content");
    text.textContent = error.message;
    text.classList.remove("hidden");
  }
}

function resetMaterialPreview() {
  const text = $("material-preview-content");
  const markdown = $("material-preview-markdown");
  const pdf = $("material-preview-pdf");
  text.textContent = "";
  markdown.innerHTML = "";
  pdf.removeAttribute("src");
  [text, markdown, pdf].forEach((element) => element.classList.add("hidden"));
}

async function uploadMaterial() {
  const files = Array.from($("material-file").files || []);
  if (!files.length) return toast("请选择要上传的文件");
  await withBusy("正在上传资料", `正在提取 ${files.length} 个文件并生成 AI 摘要…`, async () => {
    const payloads = await Promise.all(files.map(async (file) => ({
      filename: file.name,
      content_type: file.type,
      content_base64: await fileToBase64(file),
    })));
    await api(`/api/projects/${state.projectId}/materials`, { method: "POST", body: JSON.stringify({ files: payloads }) });
    await loadWorkspace();
  });
  toast(`${files.length} 个资料文件已上传`);
}

async function updateMaterialSummary(id) {
  await api(`/api/projects/${state.projectId}/materials/${id}`, {
    method: "PUT",
    body: JSON.stringify({ summary: $(`material-summary-${id}`).value }),
  });
  toast("资料摘要已更新");
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
  toast("手工资料已保存");
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
  toast("手工资料已更新");
  await loadWorkspace();
}

async function deleteMaterial(id) {
  if (!window.confirm("确定删除这条资料？删除后无法恢复。")) return;
  const workspace = await api(`/api/projects/${state.projectId}/materials/${id}`, { method: "DELETE" });
  updateWorkspace(workspace);
  toast("资料已删除");
}

async function addRepo() {
  const gitMode = $("repo-mode-input").value;
  const payload = { repo: $("repo-input").value, notes: $("repo-notes-input").value, git_mode: gitMode };
  if (gitMode === "gitlab") payload.gitlab_server = $("repo-server-input").value;
  await api(`/api/projects/${state.projectId}/repos`, { method: "POST", body: JSON.stringify(payload) });
  toast("仓库已保存");
  await loadWorkspace();
}

async function saveRepoNotes(id) {
  const branches = selectedRepoBranches(id);
  if (!branches.length) return toast("请至少选择一个分支");
  const repo = (state.workspace.repos || []).find((item) => item.id === id);
  const payload = { notes: $(`repo-notes-${id}`).value, branches, git_mode: repo && repo.git_mode === "gitlab" ? "gitlab" : "github" };
  if (payload.git_mode === "gitlab") payload.gitlab_server = $(`repo-server-${id}`).value;
  await api(`/api/projects/${state.projectId}/repos/${id}`, { method: "PUT", body: JSON.stringify(payload) });
  toast("仓库已保存");
  await loadWorkspace();
}

async function refreshRepo(id) {
  await api(`/api/projects/${state.projectId}/repos/${id}/refresh`, { method: "POST", body: "{}" });
  toast("仓库已刷新");
  await loadWorkspace();
}

async function toggleRepo(id, enabled) {
  await api(`/api/projects/${state.projectId}/repos/${id}`, { method: "PUT", body: JSON.stringify({ enabled }) });
  toast(enabled ? "Repository enabled" : "Repository disabled");
  await loadWorkspace();
}

async function deleteRepo(id) {
  if (!window.confirm("确定删除该仓库？仅移除周报关联与配置，不会影响 GitHub / GitLab 上的仓库。")) return;
  await api(`/api/projects/${state.projectId}/repos/${id}`, { method: "DELETE" });
  toast("仓库已删除");
  await loadWorkspace();
}

async function loadRepoBranches(id) {
  const repo = (state.workspace.repos || []).find((item) => item.id === id);
  const via = repo && repo.git_mode === "gitlab" ? "glab" : "gh";
  const data = await withBusy("正在读取分支", `正在通过本地 ${via} 获取仓库分支列表...`, async () => (
    api(`/api/projects/${state.projectId}/repos/${id}/branches`)
  ));
  if (data.status !== "ok") {
    toast(data.status_message || "Failed to load branches");
    return;
  }
  state.branchOptions[id] = data.branches || [];
  renderSettings(state.workspace);
  ensureTableScrollContainers();
  const picker = $(`branch-picker-${id}`);
  if (picker) picker.open = true;
}

function selectedRepoBranches(id) {
  const picker = $(`branch-picker-${id}`);
  if (!picker) return [];
  return Array.from(picker.querySelectorAll("input[type='checkbox']:checked")).map(input => input.value);
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
      <div class="panel-head">
        <div class="panel-title"><h2>当前周报</h2><span>最近一次成功生成的 Markdown</span></div>
        <div class="panel-actions">${ws.report ? `<button onclick="exportReportPdf('${escapeAttr(ws.report.week_key)}')">导出 PDF</button>` : ""}</div>
      </div>
      ${jobNotice}
      ${ws.report ? `<article class="report">${ws.report.content_html}</article>` : "<p>当前项目周还没有生成周报。</p>"}
    </div>
    <div class="panel">
      <div class="panel-head"><h2>历史周报</h2><span>只读归档</span></div>
      <div class="report-history">
        ${history.map(renderHistoryReport).join("") || "<p>还没有历史周报。</p>"}
      </div>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>生成历史</h2><span>仅记录运行信息</span></div>
      <table class="table"><thead><tr><th>触发</th><th>生成器</th><th>状态</th><th>输入</th><th>失败原因</th></tr></thead><tbody>${ws.jobs.map(j => `<tr><td data-label="触发">${escapeHtml(statusLabel(j.trigger_type))}<br>${escapeHtml(formatChinaTime(j.started_at))}</td><td data-label="生成器">${escapeHtml(j.provider)}</td><td data-label="状态"><span class="status ${j.status}">${statusLabel(j.status)}</span></td><td data-label="输入">${escapeHtml(j.input_summary || j.input_snapshot_hash)}</td><td data-label="失败原因">${escapeHtml(j.failure_reason || "")}</td></tr>`).join("") || "<tr><td colspan='5'>暂无生成记录。</td></tr>"}</tbody></table>
    </div>
  `;
}

function renderHistoryReport(report) {
  return `
    <details class="history-report">
      <summary><strong>${escapeHtml(report.week_key)}</strong><span>${escapeHtml(formatChinaTime(report.updated_at))}</span><span class="status">read-only</span><button onclick="event.preventDefault(); exportReportPdf('${escapeAttr(report.week_key)}')">导出 PDF</button></summary>
      <article class="report">${report.content_html}</article>
    </details>
  `;
}

function exportReportPdf(weekKey) {
  window.location.href = `/api/projects/${state.projectId}/reports/${encodeURIComponent(weekKey)}/pdf`;
}

function renderRisks(ws) {
  $("tab-risks").innerHTML = `
    <div class="panel">
      <div class="panel-head"><h2>进度和风险</h2><span>仅项目相关风险</span></div>
      <p>进度状态：<span class="status ${ws.progress_status.replace(" ", "-")}">${escapeHtml(statusLabel(ws.progress_status))}</span></p>
      <table class="table"><thead><tr><th>严重度</th><th>规则</th><th>标题</th><th>状态</th></tr></thead><tbody>${ws.risks.map(r => `<tr><td data-label="严重度"><span class="status ${r.severity}">${statusLabel(r.severity)}</span></td><td data-label="规则">${escapeHtml(r.rule)}</td><td data-label="标题">${escapeHtml(r.title)}<br>${escapeHtml(r.details || "")}</td><td data-label="状态">${escapeHtml(statusLabel(r.status))}</td></tr>`).join("") || "<tr><td colspan='4'>暂无风险。</td></tr>"}</tbody></table>
    </div>
    <div class="panel">
      <div class="panel-head"><h2>系统诊断</h2><span>资料源与生成状态</span></div>
      <table class="table"><thead><tr><th>类型</th><th>严重度</th><th>标题</th><th>更新时间</th></tr></thead><tbody>${(ws.source_diagnostics || []).map(d => `<tr><td>${escapeHtml(d.kind)}</td><td><span class="status ${d.severity}">${escapeHtml(statusLabel(d.severity))}</span></td><td>${escapeHtml(d.title)}<br>${escapeHtml(d.details || "")}</td><td>${escapeHtml(formatChinaTime(d.updated_at))}</td></tr>`).join("") || "<tr><td colspan='4'>暂无诊断信息。</td></tr>"}</tbody></table>
    </div>
  `;
}

async function generateReport() {
  await withBusy("正在生成周报", "正在收集本周新增资料、GitHub commits，并等待本地 CLI 返回结果...", async () => {
    toast("已开始生成");
    const workspace = await api(`/api/projects/${state.projectId}/generate`, {
      method: "POST",
      body: JSON.stringify({ force: true }),
    });
    updateWorkspace(workspace);
    toast("生成完成");
  });
}

function confirmProjectGeneration(projectId) {
  const project = state.projects.find((item) => item.id === projectId);
  if (!project) return;
  state.pendingReportProjectId = projectId;
  $("report-confirm-message").textContent = `项目「${project.name}」将生成或覆盖当前项目周的可见周报。`;
  $("report-confirm-dialog").showModal();
}

async function runConfirmedProjectGeneration() {
  const projectId = state.pendingReportProjectId;
  state.pendingReportProjectId = null;
  if (!projectId) return;
  if (state.projectId !== projectId) {
    state.projectId = projectId;
    localStorage.setItem("currentProjectId", String(state.projectId));
    await loadWorkspace();
  }
  if (state.mode !== "reports") await switchAppMode("reports");
  switchTab("report");
  await generateReport();
}

function switchTab(tab) {
  if (state.settingsView) toggleSettingsView(false);
  state.tab = tab;
  document.querySelectorAll(".tabs button").forEach(btn => btn.classList.toggle("active", btn.dataset.tab === tab));
  document.querySelectorAll("[data-project-settings]").forEach(btn => {
    btn.classList.toggle("active", tab === "settings" && Number(btn.dataset.projectSettings) === state.projectId);
  });
  const workspace = $("workspace");
  const el = $(`tab-${tab}`);
  if (workspace.classList.contains("pager-mode")) {
    workspace.querySelectorAll(".tab-panel").forEach(panel => panel.classList.remove("hidden"));
    if (el && workspace.clientWidth) {
      const panels = [...workspace.querySelectorAll(".tab-panel")];
      const reduce = typeof window !== "undefined" && window.matchMedia
        && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      workspace.scrollTo({ left: panels.indexOf(el) * workspace.clientWidth, behavior: reduce ? "auto" : "smooth" });
      centerTabStrip(reduce ? "auto" : "smooth");
      workspace.tabPagerIndex = panels.indexOf(el);
      syncWorkspacePager(panels.indexOf(el));
    }
    return;
  }
  document.querySelectorAll(".tab-panel").forEach(panel => panel.classList.add("hidden"));
  if (el) el.classList.remove("hidden");
}

function centerTabStrip(behavior) {
  const strip = document.querySelector(".tabs");
  const active = strip && strip.querySelector("button.active");
  if (!strip || !active) return;
  const stripRect = strip.getBoundingClientRect();
  const buttonRect = active.getBoundingClientRect();
  strip.scrollTo({
    left: strip.scrollLeft + buttonRect.left - stripRect.left - (strip.clientWidth - buttonRect.width) / 2,
    behavior: behavior || "auto",
  });
}

function ensureWorkspaceDots() {
  if ($("workspace-dots")) return;
  const dots = document.createElement("div");
  dots.id = "workspace-dots";
  dots.className = "pager-dots hidden";
  dots.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-page]");
    if (!button) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    workspaceElement.scrollTo({ left: Number(button.dataset.page) * workspaceElement.clientWidth, behavior: reduce ? "auto" : "smooth" });
  });
  workspaceElement.after(dots);
}

function syncWorkspacePager(index) {
  const pager = workspaceElement.classList.contains("pager-mode");
  const dots = $("workspace-dots");
  const panels = [...workspaceElement.querySelectorAll(".tab-panel")];
  if (dots) {
    if (pager && dots.childElementCount !== panels.length) {
      dots.innerHTML = panels.map((panel, i) =>
        `<button type="button" data-page="${i}" aria-label="${panel.id.replace(/^tab-/, "")}"></button>`).join("");
    }
    dots.querySelectorAll("button").forEach((dot, i) => dot.classList.toggle("active", pager && i === index));
    dots.classList.toggle("hidden", !pager || workspaceElement.classList.contains("hidden"));
  }
  if (!pager) {
    workspaceElement.style.height = "";
    return;
  }
  const panel = panels[index];
  if (panel) workspaceElement.style.height = `${panel.offsetHeight}px`;
}

function input(name, label, value, type = "text") { return `<label>${label}<input name="${name}" type="${type}" value="${escapeAttr(value || "")}"></label>`; }
function faIcon(name) {
  const icon = FA_ICONS[name];
  if (!icon) return "";
  return `<svg class="fa-icon" aria-hidden="true" viewBox="${icon.viewBox}"><path d="${icon.path}"></path></svg>`;
}
function timezoneSelect(name, label, value) {
  return `<label>${label}<select name="${name}"><option value="${CHINA_TIMEZONE}" ${(value || CHINA_TIMEZONE) === CHINA_TIMEZONE ? "selected" : ""}>中国标准时间 (Asia/Shanghai)</option></select></label>`;
}
function textarea(name, label, value, cls = "") { return `<label class="${cls}">${label}<textarea name="${name}">${escapeHtml(value || "")}</textarea></label>`; }
function rowItem(item) { return `<tr><td data-label="标题">${escapeHtml(item.title || "")}</td><td data-label="负责人">${escapeHtml(item.owner_label || "")}</td><td data-label="状态">${escapeHtml(statusLabel(item.status || ""))}</td></tr>`; }
function itemPayload(row) {
  const payload = {};
  row.querySelectorAll("input, select, textarea").forEach((control) => {
    if (control.name) payload[control.name] = control.value;
  });
  return payload;
}
const STATUS_LABELS = {
  planned: "计划中",
  in_progress: "进行中",
  blocked: "受阻",
  complete: "已完成",
  high: "高",
  medium: "中",
  low: "低",
  info: "提示",
  active: "活跃",
  resolved: "已解决",
  "on track": "进展顺利",
  "at risk": "有风险",
  "off track": "已偏离",
  done: "已完成",
  unknown: "未知",
  pending: "等待中",
  running: "生成中",
  succeeded: "已成功",
  failed: "已失败",
  schedule: "定时",
  manual: "手动",
};

function statusLabel(value) {
  const key = String(value ?? "").toLowerCase();
  return STATUS_LABELS[key] || value;
}

function statusOptions(value) {
  return ["planned", "in_progress", "blocked", "complete"]
    .map((status) => `<option value="${status}" ${sel(value, status)}>${statusLabel(status)}</option>`)
    .join("");
}
function sel(value, expected) { return (value || "planned") === expected ? "selected" : ""; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[c])); }
function escapeAttr(value) { return escapeHtml(value); }
function formatBytes(value) {
  const bytes = Number(value) || 0;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
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

function projectDisplayStatus(project) {
  if (project.id === state.projectId && state.workspace?.project?.id === project.id) {
    return state.workspace.progress_status;
  }
  return project.progress_status || project.status || "unknown";
}

function statusTone(value) {
  const status = String(value || "").toLowerCase().replaceAll("_", "-").replaceAll(" ", "-");
  if (["on-track", "complete", "active", "success", "connected"].includes(status)) return "is-success";
  if (["at-risk", "medium", "inaccessible", "unauthenticated"].includes(status)) return "is-warning";
  if (["blocked", "failed", "high"].includes(status)) return "is-error";
  return "is-neutral";
}

function statusDot(value, extraClass = "", toneOverride = "") {
  return `<span class="status-dot ${toneOverride || statusTone(value)} ${extraClass}" role="img" title="${escapeAttr(value)}" aria-label="状态：${escapeAttr(value)}"></span>`;
}

function reportSummary(report) {
  const markdown = String(report?.content_md || "").trim();
  if (!markdown) return "暂无可用的周报摘要。";
  const section = markdown.match(
    /(?:^|\n)#{1,6}\s*(?:本周总结|本周摘要|周报摘要|this week's summary|this week summary|summary)[^\n]*\n([\s\S]*?)(?=\n#{1,6}\s|$)/i
  );
  const source = section ? section[1] : markdown;
  const cleaned = source
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/!\[[^\]]*\]\([^)]+\)/g, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .split(/\r?\n/)
    .filter((line) => !/^\s*#{1,6}\s/.test(line) && !/^\s*\|?\s*:?-{3,}/.test(line))
    .map((line) => line
      .replace(/^\s*(?:[-*+]\s+|\d+[.)]\s+|>\s*)/, "")
      .replace(/\|/g, " ")
      .replace(/[*_~`]/g, "")
      .replace(/<[^>]+>/g, "")
      .trim())
    .filter(Boolean)
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
  if (!cleaned) return "暂无可用的周报摘要。";
  const characters = Array.from(cleaned);
  return characters.length > 280 ? `${characters.slice(0, 280).join("")}…` : cleaned;
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

function openNewProjectDialog() {
  closeProjectSheet();
  $("project-form").reset();
  $("project-form").start_date.value = new Date().toISOString().slice(0, 10);
  $("project-dialog").showModal();
}
$("new-project").onclick = openNewProjectDialog;
$("open-project-bar").onclick = () => $("project-sheet").showModal();
$("close-project-sheet").onclick = () => $("project-sheet").close();
const workspacePagerQuery = window.matchMedia("(max-width: 767px)");
const workspaceElement = $("workspace");
function attachSwipeNav(el, options = {}) {
  let startX = 0;
  let startY = 0;
  let startLeft = 0;
  let lastX = 0;
  let startedAt = 0;
  let gesture = "idle";
  const enabled = options.enabled || (() => true);
  el.addEventListener("touchstart", (event) => {
    if (event.touches.length !== 1 || !enabled()) {
      gesture = "idle";
      return;
    }
    gesture = "pending";
    startX = lastX = event.touches[0].clientX;
    startY = event.touches[0].clientY;
    startLeft = el.scrollLeft;
    startedAt = Date.now();
  }, { passive: true });
  el.addEventListener("touchmove", (event) => {
    if (gesture === "idle" || gesture === "vertical") return;
    const dx = event.touches[0].clientX - startX;
    const dy = event.touches[0].clientY - startY;
    if (gesture === "pending") {
      if (Math.abs(dx) < 10 && Math.abs(dy) < 10) return;
      gesture = Math.abs(dx) > Math.abs(dy) * 1.4 && el.scrollWidth > el.clientWidth + 1 ? "swipe" : "vertical";
      if (gesture === "vertical") return;
    }
    event.preventDefault();
    lastX = event.touches[0].clientX;
    el.scrollLeft = startLeft - (lastX - startX);
  }, { passive: false });
  const settle = () => {
    if (gesture !== "swipe") {
      gesture = "idle";
      return;
    }
    const dx = lastX - startX;
    const elapsed = Date.now() - startedAt;
    const width = el.clientWidth || 1;
    const pageIndex = Math.round(startLeft / width);
    const maxIndex = Math.max(0, Math.round(el.scrollWidth / width) - 1);
    let index = pageIndex;
    if (Math.abs(dx) >= Math.max(56, width * 0.25) || (Math.abs(dx) >= 28 && elapsed < 220)) {
      index += dx < 0 ? 1 : -1;
    }
    index = Math.min(maxIndex, Math.max(0, index));
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollTo({ left: index * width, behavior: reduce ? "auto" : "smooth" });
    if (options.onPage) options.onPage(index);
    gesture = "idle";
  };
  el.addEventListener("touchend", settle);
  el.addEventListener("touchcancel", settle);
}

function applyWorkspacePagerMode() {
  workspaceElement.classList.toggle("pager-mode", workspacePagerQuery.matches);
  ensureWorkspaceDots();
  switchTab(state.tab);
}
workspacePagerQuery.addEventListener("change", applyWorkspacePagerMode);
applyWorkspacePagerMode();
attachSwipeNav(workspaceElement, { enabled: () => workspaceElement.classList.contains("pager-mode") });
attachSwipeNav($("todo-board"));
window.addEventListener("resize", () => {
  if (!workspacePagerQuery.matches) return;
  requestAnimationFrame(() => {
    if (!workspaceElement.classList.contains("pager-mode") || !workspaceElement.clientWidth) return;
    const panels = [...workspaceElement.querySelectorAll(".tab-panel")];
    const index = Math.min(panels.length - 1, Math.max(0, Math.round(workspaceElement.scrollLeft / workspaceElement.clientWidth)));
    workspaceElement.tabPagerIndex = index;
    syncWorkspacePager(index);
  });
});
if (typeof ResizeObserver === "function") {
  const pagerHeightObserver = new ResizeObserver(() => {
    if (!workspaceElement.classList.contains("pager-mode")) return;
    const panels = [...workspaceElement.querySelectorAll(".tab-panel")];
    const index = Math.min(panels.length - 1, Math.max(0, Math.round(workspaceElement.scrollLeft / (workspaceElement.clientWidth || 1))));
    const panel = panels[index];
    if (panel) workspaceElement.style.height = `${panel.offsetHeight}px`;
  });
  workspaceElement.querySelectorAll(".tab-panel").forEach((panel) => pagerHeightObserver.observe(panel));
}
workspaceElement.addEventListener("scroll", () => {
  if (workspaceElement.tabPagerRaf) return;
  workspaceElement.tabPagerRaf = requestAnimationFrame(() => {
    workspaceElement.tabPagerRaf = 0;
    if (!workspaceElement.classList.contains("pager-mode") || !workspaceElement.clientWidth) return;
    const panels = [...workspaceElement.querySelectorAll(".tab-panel")];
    const index = Math.round(workspaceElement.scrollLeft / workspaceElement.clientWidth);
    const panel = panels[index];
    if (!panel) return;
    if (workspaceElement.tabPagerIndex !== index) {
      workspaceElement.tabPagerIndex = index;
      syncWorkspacePager(index);
    }
    const name = panel.id.replace(/^tab-/, "");
    let changed = false;
    document.querySelectorAll(".tabs button").forEach(btn => {
      const active = btn.dataset.tab === name;
      if (btn.classList.contains("active") !== active) changed = true;
      btn.classList.toggle("active", active);
    });
    if (changed) centerTabStrip("smooth");
  });
}, { passive: true });
$("cancel-project").onclick = () => $("project-dialog").close();
$("close-material-preview").onclick = () => $("material-preview-dialog").close();
$("project-form").onsubmit = async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.target).entries());
  const data = await api("/api/projects", { method: "POST", body: JSON.stringify(payload) });
  $("project-dialog").close();
  state.projectId = data.id;
  localStorage.setItem("currentProjectId", String(state.projectId));
  await loadState();
  toast("项目已创建");
};
$("page-corner").onclick = () => switchAppMode(state.mode === "todos" ? "reports" : "todos");
document.querySelectorAll("[data-mode-tab]").forEach((btn) => btn.onclick = () => {
  const target = btn.dataset.modeTab;
  if (target === "settings") {
    toggleSettingsView();
    return;
  }
  switchAppMode(target);
});
$("open-global-settings").onclick = () => toggleSettingsView(true);
$("page-corner").onkeydown = (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    switchAppMode(state.mode === "todos" ? "reports" : "todos");
  }
};
$("cancel-report-generation").onclick = () => {
  state.pendingReportProjectId = null;
  $("report-confirm-dialog").close();
};
$("report-confirm-form").onsubmit = async (event) => {
  event.preventDefault();
  $("report-confirm-dialog").close();
  await runConfirmedProjectGeneration();
};
$("report-confirm-dialog").oncancel = () => {
  state.pendingReportProjectId = null;
};
$("cancel-close-todo").onclick = () => $("close-todo-dialog").close();
$("cancel-todo-delete").onclick = () => {
  state.pendingDeleteTodoId = null;
  $("todo-delete-dialog").close();
};
$("todo-delete-form").onsubmit = async (event) => {
  event.preventDefault();
  $("todo-delete-dialog").close();
  await runTodoDelete();
};
$("todo-delete-dialog").oncancel = () => {
  state.pendingDeleteTodoId = null;
};
$("close-todo-form").onsubmit = async (event) => {
  event.preventDefault();
  const payload = Object.fromEntries(new FormData(event.target).entries());
  const id = Number(payload.todo_id);
  delete payload.todo_id;
  updateTodos(await api(`/api/todos/${id}/close`, { method: "POST", body: JSON.stringify(payload) }));
  $("close-todo-dialog").close();
  toast(payload.project_id ? "TODO 已关闭并添加到项目资料" : "TODO 已关闭");
};
document.querySelectorAll(".tabs button").forEach(btn => btn.onclick = () => switchTab(btn.dataset.tab));

loadState().catch(err => toast(err.message));

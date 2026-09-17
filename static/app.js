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
  wand: {
    viewBox: "0 0 576 512",
    path: "M234.7 42.7L197 56.8c-3 1.1-5 4-5 7.2s2 6.1 5 7.2l37.7 14.1L248.8 123c1.1 3 4 5 7.2 5s6.1-2 7.2-5l14.1-37.7L315 71.2c3-1.1 5-4 5-7.2s-2-6.1-5-7.2L277.3 42.7 263.2 5c-1.1-3-4-5-7.2-5s-6.1 2-7.2 5L234.7 42.7zM46.1 395.4c-18.7 18.7-18.7 49.1 0 67.9l34.6 34.6c18.7 18.7 49.1 18.7 67.9 0L529.9 116.5c18.7-18.7 18.7-49.1 0-67.9L495.3 14.1c-18.7-18.7-49.1-18.7-67.9 0L46.1 395.4zM484.6 82.6l-105 105-23.3-23.3 105-105 23.3 23.3zM7.5 117.2C3 118.9 0 123.2 0 128s3 9.1 7.5 10.8L64 160l21.2 56.5c1.7 4.5 6 7.5 10.8 7.5s9.1-3 10.8-7.5L128 160l56.5-21.2c4.5-1.7 7.5-6 7.5-10.8s-3-9.1-7.5-10.8L128 96 106.8 39.5C105.1 35 100.8 32 96 32s-9.1 3-10.8 7.5L64 96 7.5 117.2zm352 256c-4.5 1.7-7.5 6-7.5 10.8s3 9.1 7.5 10.8L416 416l21.2 56.5c1.7 4.5 6 7.5 10.8 7.5s9.1-3 10.8-7.5L480 416l56.5-21.2c4.5-1.7 7.5-6 7.5-10.8s-3-9.1-7.5-10.8L480 352l-21.2-56.5c-1.7-4.5-6-7.5-10.8-7.5s-9.1 3-10.8 7.5L416 352l-56.5 21.2z",
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
  pendingDeleteUserId: null,
  mode: localStorage.getItem("workspaceMode") === "todos" ? "todos" : "reports",
  settingsView: false,
  currentUser: null,
  isAdmin: false,
  asrEndpoint: "",
  asrModel: "whisper",
  asrLanguage: "zh",
  llmProvider: "openai",
  llmBaseUrl: "",
  llmModel: "",
  llmApiKeySet: false,
  queueCapacity: 5,
  queueParallelism: 2,
  theme: "blue",
  appearance: "light",
  branchOptions: {},
  tab: "overview",
  sourceTab: "manual",
  planSubTab: "plan",
  settingsSubTab: "project",
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
  if (persist) {
    localStorage.setItem("appTheme", themeId);
    syncUiPreferencesToServer();
  }
  updateThemeColorSurface();
}

function applyAppearance(mode, persist = true) {
  const normalized = mode === "dark" ? "dark" : "light";
  state.appearance = normalized;
  const root = document.documentElement;
  if (root) root.dataset.mode = normalized;
  document.querySelectorAll(".mode-option").forEach((btn) => btn.classList.toggle("active", btn.dataset.modeOption === normalized));
  if (persist) {
    localStorage.setItem("appAppearance", normalized);
    syncUiPreferencesToServer();
  }
  updateThemeColorSurface();
}

applyTheme(localStorage.getItem("appTheme") || "blue", false);
applyAppearance(localStorage.getItem("appAppearance") || "light", false);

let uiPreferencesSyncInFlight = false;

async function syncUiPreferencesToServer() {
  if (uiPreferencesSyncInFlight) return;
  uiPreferencesSyncInFlight = true;
  try {
    await api("/api/settings", {
      method: "PUT",
      body: JSON.stringify({ ui_theme: state.theme, ui_mode: state.appearance }),
    });
  } catch {
    // 主题留在本机，下次修改时再同步
  }
  uiPreferencesSyncInFlight = false;
}

function renderAppearanceSettings() {
  const swatches = $("appearance-swatches");
  if (!swatches) return;
  swatches.innerHTML = THEMES.map((theme) =>
    `<button type="button" class="theme-swatch${theme.id === state.theme ? " active" : ""}" data-theme-id="${theme.id}" onclick="applyTheme('${theme.id}')"><span class="theme-swatch-dot" style="background:${theme.color}"></span>${theme.label}</button>`).join("");
}
renderAppearanceSettings();

async function api(path, options = {}) {
  let res;
  try {
    res = await fetch(path, {
      cache: "no-store",
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
  } catch {
    throw new Error("网络请求失败，请检查网络连接后重试");
  }
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    // Chrome's JSON parse error embeds the raw body head (e.g. "<html>…");
    // surface a clear message with the status and body head instead.
    throw new Error(`服务响应异常（HTTP ${res.status}）: ${text.slice(0, 100) || "空响应"}`);
  }
  if (res.status === 401) {
    showLoginView();
    throw new Error(data.error || "登录已过期，请重新登录");
  }
  if (!res.ok) throw new Error(data.error || `请求失败（HTTP ${res.status}）`);
  return data;
}

function showLoginView() {
  state.currentUser = null;
  state.isAdmin = false;
  $("login-view").classList.remove("hidden");
  document.body.classList.add("logged-out");
  const password = $("login-password");
  if (password) password.value = "";
}

function hideLoginView() {
  $("login-view").classList.add("hidden");
  document.body.classList.remove("logged-out");
}

async function login(event) {
  event.preventDefault();
  const button = $("login-submit");
  const error = $("login-error");
  error.classList.add("hidden");
  button.disabled = true;
  try {
    await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({
        username: $("login-username").value.trim(),
        password: $("login-password").value,
      }),
    });
    hideLoginView();
    await loadState();
    toast("已登录");
  } catch (err) {
    error.textContent = err.message;
    error.classList.remove("hidden");
  } finally {
    button.disabled = false;
  }
}

async function logout() {
  try {
    await api("/api/auth/logout", { method: "POST", body: "{}" });
  } catch {
    // the session may already be gone; the login view shows regardless
  }
  showLoginView();
  toast("已退出登录");
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

// —— 失焦自动保存：输入过程不打扰，焦点离开字段后立即落盘，状态提示取代保存按钮 ——
const autoSaveRegistry = new Map(); // key -> { run, schedule, timer }

function serializeAutoSaveFields(root) {
  return Array.from(root.querySelectorAll("input, textarea, select"))
    .map((el) => `${el.id || el.name}|${el.type === "checkbox" ? (el.checked ? "1" : "0") : el.value}`)
    .join("\n");
}

function setAutoSaveStatus(root, stateName, message = "") {
  const status = root.querySelector(".autosave-status");
  if (!status) return;
  status.classList.toggle("is-saving", stateName === "saving");
  status.classList.toggle("is-saved", stateName === "saved");
  status.classList.toggle("is-error", stateName === "error");
  const time = new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" });
  status.textContent = stateName === "saving" ? "保存中…"
    : stateName === "saved" ? `已自动保存 ${time}`
    : stateName === "error" ? `保存失败：${message}`
    : message;
}

function setupAutoSave(key, root, save) {
  if (!root) return;
  const previous = autoSaveRegistry.get(key);
  if (previous?.timer) clearTimeout(previous.timer);
  const entry = { run: null, schedule: null, timer: 0, root, state: null };
  autoSaveRegistry.set(key, entry);
  const state = { snapshot: serializeAutoSaveFields(root), running: false, rerun: false };
  entry.state = state;
  const run = async () => {
    entry.timer = 0;
    if (state.running) {
      state.rerun = true;
      return;
    }
    if (serializeAutoSaveFields(root) === state.snapshot) return;
    state.running = true;
    setAutoSaveStatus(root, "saving");
    try {
      await save();
      state.snapshot = serializeAutoSaveFields(root);
      setAutoSaveStatus(root, "saved");
    } catch (error) {
      setAutoSaveStatus(root, "error", error.message);
      toast(error.message);
    } finally {
      state.running = false;
      if (state.rerun) {
        state.rerun = false;
        run();
      }
    }
  };
  const schedule = () => {
    clearTimeout(entry.timer);
    entry.timer = setTimeout(run, 0);
  };
  entry.run = run;
  entry.schedule = schedule;
  // 文本输入的 change 在失焦时触发，勾选/下拉在选择完成时触发
  root.addEventListener("change", schedule);
  // 焦点离开整个表单或页面隐藏时兜底落盘；快照守卫保证无改动时不发请求
  root.addEventListener("focusout", () => setTimeout(() => {
    if (!root.contains(document.activeElement)) schedule();
  }, 0));
}

function touchAutoSave(key) {
  autoSaveRegistry.get(key)?.schedule();
}

// 程序化改写表单值后（如启动时渲染设置）重置快照，避免无编辑时的误保存
function refreshAutoSaveSnapshot(key) {
  const entry = autoSaveRegistry.get(key);
  if (entry?.root) entry.state.snapshot = serializeAutoSaveFields(entry.root);
}

function flushAllAutoSaves() {
  for (const entry of autoSaveRegistry.values()) {
    if (entry.timer) {
      clearTimeout(entry.timer);
      entry.timer = 0;
      entry.run();
    }
  }
}

document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden") flushAllAutoSaves();
});
window.addEventListener("pagehide", flushAllAutoSaves);

async function loadState() {
  const data = await api("/api/state");
  state.projects = data.projects;
  renderVersion(data.version);
  state.currentUser = data.current_user || null;
  state.isAdmin = !!(data.current_user && data.current_user.is_admin);
  $("sidebar-user").textContent = state.currentUser
    ? `${state.currentUser.username}${state.isAdmin ? " · 管理员" : ""}`
    : "";
  document.querySelectorAll(".admin-only").forEach((el) => el.classList.toggle("hidden", !state.isAdmin));
  state.githubEnabled = data.github_enabled !== false;
  state.gitlabEnabled = data.gitlab_enabled !== false;
  state.githubTokenSet = !!data.github_token_set;
  state.githubTokens = data.github_tokens || [];
  state.gitlabTokenSet = !!data.gitlab_token_set;
  state.gitlabUrl = data.gitlab_url || "";
  state.gitlabSkipVerify = !!data.gitlab_skip_verify;
  state.asrEndpoint = data.asr_endpoint || "";
  state.asrModel = data.asr_model || "";
  state.asrLanguage = data.asr_language || "zh";
  state.llmProvider = data.llm_provider || "openai";
  state.llmBaseUrl = data.llm_base_url || "";
  state.llmModel = data.llm_model || "";
  state.llmApiKeySet = !!data.llm_api_key_set;
  state.queueCapacity = data.queue_capacity || 5;
  state.queueParallelism = data.queue_parallelism || 2;
  if (data.ui_theme && THEMES.some((theme) => theme.id === data.ui_theme)) applyTheme(data.ui_theme, false);
  if (data.ui_mode) applyAppearance(data.ui_mode, false);
  renderVoiceSettings();
  renderLlmSettings();
  renderQueueSettings();
  renderGitSettings();
  if (state.isAdmin) {
    loadUsers().catch(() => {});
  }
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

async function loadWorkspaceBusy(title) {
  // Only surface the overlay when the load actually takes a while, so
  // quick switches stay snappy.
  let shown = false;
  const timer = setTimeout(() => {
    shown = true;
    setBusy(true, title, "正在加载项目数据…");
  }, 150);
  try {
    await loadWorkspace();
  } finally {
    clearTimeout(timer);
    if (shown) setBusy(false);
  }
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
  if (todoDrag.active || todoDrag.armed) return; // 拖拽进行中不重绘，落盘后由接口回包刷新
  const columns = [
    { status: "todo", title: "待办" },
    { status: "doing", title: "进行中" },
    { status: "closed", title: "已关闭" },
  ];
  const savedScrollLeft = board.scrollLeft;
  board.innerHTML = columns.map((column) => {
    const items = state.todos.filter((todo) => todo.status === column.status);
    return `
      <section class="todo-column todo-column-${column.status}" data-lane="${column.status}">
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
    const pageWidth = board.clientWidth || 1;
    board.scrollLeft = Math.round(savedScrollLeft / pageWidth) * pageWidth;
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
    board._pageSnapPending = undefined;
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

// —— 看板拖拽：卡片支持同列上下排序与跨列移动；触屏长按抬起，桌面按住即拖 ——
const todoDrag = {
  active: false, armed: false, fromLane: "", card: null, pointerId: -1,
  touch: false, startX: 0, startY: 0, grabX: 0, grabY: 0, lastX: 0, lastY: 0,
  ghost: null, origin: null, longPressTimer: 0, raf: 0,
};

function setupTodoBoardDrag() {
  const board = $("todo-board");
  if (!board || board._dragBound) return;
  board._dragBound = true;
  board.addEventListener("pointerdown", (event) => {
    if (todoDrag.active || todoDrag.armed) return;
    if (event.pointerType === "mouse" && event.button !== 0) return;
    const card = event.target.closest(".todo-card[data-todo-id]");
    if (!card || event.target.closest("button, a, input, textarea, [data-todo-editor]")) return;
    todoDrag.armed = true;
    todoDrag.card = card;
    todoDrag.pointerId = event.pointerId;
    todoDrag.touch = event.pointerType === "touch";
    todoDrag.fromLane = card.closest(".todo-column")?.dataset.lane || "todo";
    todoDrag.startX = todoDrag.lastX = event.clientX;
    todoDrag.startY = todoDrag.lastY = event.clientY;
    window.addEventListener("pointermove", onTodoDragMove);
    window.addEventListener("pointerup", onTodoDragEnd);
    window.addEventListener("pointercancel", onTodoDragCancel);
    if (todoDrag.touch) {
      card.classList.add("todo-card-armed");
      todoDrag.longPressTimer = setTimeout(() => beginTodoDrag(), 240);
    }
  });
  // 拖拽中压掉原生滚动，否则触屏上手势会被页面滚动/翻页抢占
  board.addEventListener("touchmove", (event) => {
    if (todoDrag.active) event.preventDefault();
  }, { passive: false });
  board.addEventListener("touchend", (event) => {
    if (todoDrag.active) event.preventDefault();
  }, { passive: false });
  board.addEventListener("contextmenu", (event) => {
    if (todoDrag.active || (todoDrag.armed && todoDrag.touch)) event.preventDefault();
  });
}

function beginTodoDrag() {
  const card = todoDrag.card;
  if (!card || !todoDrag.armed) return;
  todoDrag.armed = false;
  todoDrag.active = true;
  card.classList.remove("todo-card-armed");
  const rect = card.getBoundingClientRect();
  todoDrag.grabX = todoDrag.touch ? rect.width / 2 : todoDrag.lastX - rect.left;
  todoDrag.grabY = todoDrag.touch ? rect.height / 2 : todoDrag.lastY - rect.top;
  const ghost = card.cloneNode(true);
  ghost.removeAttribute("data-todo-id");
  ghost.classList.remove("todo-card-armed", "todo-card-lifted");
  ghost.classList.add("todo-card-ghost");
  ghost.style.width = `${rect.width}px`;
  document.body.appendChild(ghost);
  todoDrag.ghost = ghost;
  todoDrag.origin = { parent: card.parentNode, next: card.nextSibling };
  card.classList.add("todo-card-lifted");
  document.body.classList.add("todo-drag-in-progress");
  $("todo-board")._todoDragActive = true; // 让看板滑动翻页给拖拽让位
  if (todoDrag.touch && navigator.vibrate) navigator.vibrate(10);
  suppressTodoCardClick();
  window.addEventListener("keydown", onTodoDragKey);
  positionTodoGhost();
  todoDrag.raf = requestAnimationFrame(todoDragFrame);
}

function positionTodoGhost() {
  if (!todoDrag.ghost) return;
  const liftY = todoDrag.touch ? -16 : 0;
  todoDrag.ghost.style.transform =
    `translate(${todoDrag.lastX - todoDrag.grabX}px, ${todoDrag.lastY - todoDrag.grabY + liftY}px) rotate(1.5deg) scale(1.02)`;
}

function onTodoDragMove(event) {
  if (event.pointerId !== todoDrag.pointerId) return;
  if (todoDrag.armed) {
    const dx = event.clientX - todoDrag.startX;
    const dy = event.clientY - todoDrag.startY;
    if (todoDrag.touch) {
      // 移动明显即视为滚动/翻页手势，放弃本次长按
      if (Math.hypot(dx, dy) > 10) cancelTodoDragArm();
    } else if (Math.hypot(dx, dy) > 4) {
      beginTodoDrag();
    }
  }
  if (!todoDrag.active) return;
  todoDrag.lastX = event.clientX;
  todoDrag.lastY = event.clientY;
  positionTodoGhost();
}

function todoDragFrame() {
  if (!todoDrag.active) return;
  autoScrollTodoBoard();
  updateTodoInsertion(todoDrag.lastX, todoDrag.lastY);
  todoDrag.raf = requestAnimationFrame(todoDragFrame);
}

function autoScrollTodoBoard() {
  const EDGE = 32;
  const SPEED = 12;
  const board = $("todo-board");
  // 横向：手机分页模式下把卡片拖到屏幕边缘可翻到相邻列
  if (board.scrollWidth > board.clientWidth + 1) {
    const rect = board.getBoundingClientRect();
    if (todoDrag.lastX < rect.left + EDGE) board.scrollLeft -= SPEED;
    else if (todoDrag.lastX > rect.right - EDGE) board.scrollLeft += SPEED;
  }
  // 纵向：滚动页面本身，方便长列拖到视口外
  const scroller = document.scrollingElement;
  if (scroller) {
    if (todoDrag.lastY < EDGE) scroller.scrollTop -= SPEED;
    else if (todoDrag.lastY > window.innerHeight - EDGE) scroller.scrollTop += SPEED;
  }
}

function updateTodoInsertion(x, y) {
  const card = todoDrag.card;
  if (!card) return;
  const board = $("todo-board");
  const acceptLanes = todoDrag.fromLane === "closed" ? ["closed"] : ["todo", "doing"];
  let targetColumn = null;
  for (const column of board.querySelectorAll(".todo-column")) {
    if (!acceptLanes.includes(column.dataset.lane)) continue;
    const rect = column.getBoundingClientRect();
    if (x >= rect.left && x <= rect.right && y >= rect.top - 12 && y <= rect.bottom + 12) {
      targetColumn = column;
      break;
    }
  }
  if (!targetColumn) return; // 悬停在无关区域时保持上一个落点
  const list = targetColumn.querySelector(".todo-card-list");
  const cards = [...list.querySelectorAll(".todo-card[data-todo-id]")].filter((el) => el !== card);
  let before = null;
  for (const el of cards) {
    const rect = el.getBoundingClientRect();
    if (y < rect.top + rect.height / 2) {
      before = el;
      break;
    }
  }
  const ref = before || list.querySelector(".todo-draft, .todo-empty");
  if (card.parentNode === ref?.parentNode && card.nextElementSibling === ref) return;
  (ref?.parentNode || list).insertBefore(card, ref);
}

function onTodoDragEnd(event) {
  if (event.pointerId !== todoDrag.pointerId) return;
  if (todoDrag.active) commitTodoDragDrop();
  else if (todoDrag.armed) cancelTodoDragArm();
}

function onTodoDragCancel() {
  if (todoDrag.active) cancelTodoDrag();
  else if (todoDrag.armed) cancelTodoDragArm();
}

function onTodoDragKey(event) {
  if (event.key === "Escape") {
    event.preventDefault();
    cancelTodoDrag();
  }
}

function cancelTodoDragArm() {
  if (todoDrag.longPressTimer) {
    clearTimeout(todoDrag.longPressTimer);
    todoDrag.longPressTimer = 0;
  }
  if (todoDrag.card) todoDrag.card.classList.remove("todo-card-armed");
  stopTodoDragListeners();
  todoDrag.armed = false;
  todoDrag.card = null;
}

function commitTodoDragDrop() {
  const card = todoDrag.card;
  const board = $("todo-board");
  const laneOrder = [...board.querySelectorAll(".todo-column")].map((column) => column.dataset.lane);
  const targetLane = card.closest(".todo-column")?.dataset.lane;
  cleanupTodoDrag();
  card.classList.remove("todo-card-lifted");
  const lanes = {};
  board.querySelectorAll(".todo-column").forEach((column) => {
    lanes[column.dataset.lane] = [...column.querySelectorAll(".todo-card[data-todo-id]")]
      .map((el) => Number(el.dataset.todoId));
  });
  const byId = new Map(state.todos.map((todo) => [todo.id, todo]));
  const seen = new Set();
  const next = [];
  for (const [lane, ids] of Object.entries(lanes)) {
    for (const id of ids) {
      const todo = byId.get(id);
      if (!todo || seen.has(id)) continue;
      todo.status = lane;
      seen.add(id);
      next.push(todo);
    }
  }
  // 拖拽期间后台新出现的卡片（如语音 TODO）兜底保留
  for (const todo of state.todos) {
    if (!seen.has(todo.id)) next.push(todo);
  }
  state.todos = next;
  renderTodoBoard();
  // 手机分页模式：落点列可能不在当前页，吸附过去
  if (board.scrollWidth > board.clientWidth + 1) {
    const laneIndex = laneOrder.indexOf(targetLane);
    if (laneIndex >= 0) board.scrollLeft = laneIndex * board.clientWidth;
  }
  api("/api/todos/reorder", { method: "POST", body: JSON.stringify({ lanes }) })
    .then((data) => updateTodos(data))
    .catch((error) => {
      toast(error.message);
      loadTodos();
    });
}

function cancelTodoDrag() {
  const { card, origin } = todoDrag;
  cleanupTodoDrag();
  if (card && origin) {
    card.classList.remove("todo-card-lifted");
    origin.parent.insertBefore(card, origin.next);
  }
}

function cleanupTodoDrag() {
  if (todoDrag.raf) cancelAnimationFrame(todoDrag.raf);
  todoDrag.raf = 0;
  if (todoDrag.longPressTimer) {
    clearTimeout(todoDrag.longPressTimer);
    todoDrag.longPressTimer = 0;
  }
  stopTodoDragListeners();
  todoDrag.ghost?.remove();
  todoDrag.ghost = null;
  document.body.classList.remove("todo-drag-in-progress");
  $("todo-board")._todoDragActive = false;
  if (todoDrag.card) todoDrag.card.classList.remove("todo-card-armed");
  todoDrag.active = false;
  todoDrag.armed = false;
  todoDrag.card = null;
}

function stopTodoDragListeners() {
  window.removeEventListener("pointermove", onTodoDragMove);
  window.removeEventListener("pointerup", onTodoDragEnd);
  window.removeEventListener("pointercancel", onTodoDragCancel);
  window.removeEventListener("keydown", onTodoDragKey);
}

function suppressTodoCardClick() {
  const stop = (event) => {
    event.stopPropagation();
    event.preventDefault();
  };
  document.addEventListener("click", stop, { capture: true, once: true });
  setTimeout(() => document.removeEventListener("click", stop, true), 600);
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
    <article class="todo-card ${editable ? "todo-card-editable" : "todo-card-closed"}" data-todo-id="${todo.id}" ondragstart="return false" ${editable ? `onclick="if (!event.target.closest('a')) beginTodoEdit(${todo.id})" tabindex="0" onkeydown="if (event.key === 'Enter' && !event.target.closest('a')) beginTodoEdit(${todo.id})"` : ""}>
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
  if (todo && todo.title === title && (todo.description || "") === description) {
    // 无改动直接收起编辑卡片：不发请求，也不更新时间戳
    state.todoEditorId = null;
    renderTodoBoard();
    return;
  }
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

const voiceCapture = {
  recorder: null,
  stream: null,
  chunks: [],
  holding: false,
  pressActive: false,
  startedAt: 0,
  timerId: 0,
};

function voiceRecordingSupported() {
  return typeof window !== "undefined"
    && typeof MediaRecorder !== "undefined"
    && !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
}

function setupVoiceTodoFab() {
  const fab = $("voice-todo-fab");
  if (!fab) return;
  if (!voiceRecordingSupported()) {
    fab.classList.add("is-unsupported");
    const httpsHint = `https://${location.hostname}:8443`;
    const message = window.isSecureContext
      ? "当前浏览器不支持录音，请使用 Safari 或 Chrome"
      : `浏览器要求 HTTPS 才能使用麦克风。请改用 ${httpsHint} 访问，并接受自签名证书警告`;
    fab.title = message;
    fab.addEventListener("click", () => toast(message));
    return;
  }
  fab.addEventListener("pointerdown", startVoiceHold);
  fab.addEventListener("pointerup", endVoiceHold);
  fab.addEventListener("pointercancel", cancelVoiceHold);
  fab.addEventListener("contextmenu", (event) => event.preventDefault());
  fab.addEventListener("click", () => {
    if (Date.now() < voiceFabSuppressClickUntil) return;
    if (activeVoiceJobId() !== null) cancelActiveVoiceJob();
  });
}

function voicePermissionErrorMessage(error) {
  if (error && (error.name === "NotAllowedError" || error.name === "SecurityError")) {
    return "麦克风权限被拒绝，请在浏览器设置中允许后重试";
  }
  if (error && error.name === "NotFoundError") return "未检测到麦克风设备";
  return `无法启动录音（${(error && error.name) || "unknown"}）`;
}

async function startVoiceHold(event) {
  if (voiceCapture.holding) return;
  if (activeVoiceJobId() !== null) return;
  event.preventDefault();
  const fab = $("voice-todo-fab");
  try { fab.setPointerCapture(event.pointerId); } catch { /* pointer already gone */ }
  voiceCapture.pressActive = true;
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (error) {
    toast(voicePermissionErrorMessage(error));
    return;
  }
  if (!voiceCapture.pressActive) {
    stream.getTracks().forEach((track) => track.stop());
    return;
  }
  Object.assign(voiceCapture, {
    recorder: null,
    stream,
    chunks: [],
    holding: true,
    startedAt: Date.now(),
    timerId: 0,
  });
  const mimeType = ["audio/webm;codecs=opus", "audio/mp4", "audio/webm", ""]
    .find((type) => !type || MediaRecorder.isTypeSupported(type));
  try {
    voiceCapture.recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
  } catch {
    voiceCapture.recorder = new MediaRecorder(stream);
  }
  voiceCapture.recorder.ondataavailable = (recordEvent) => {
    if (recordEvent.data && recordEvent.data.size) voiceCapture.chunks.push(recordEvent.data);
  };
  voiceCapture.recorder.onstop = () => finishVoiceRecording();
  fab.classList.add("is-recording");
  renderVoiceLiveText();
  voiceCapture.timerId = setInterval(renderVoiceLiveText, 500);
  voiceCapture.recorder.start(250);
}

function stopVoiceRecordingUi() {
  const fab = $("voice-todo-fab");
  if (fab) fab.classList.remove("is-recording");
  $("voice-todo-live").classList.add("hidden");
  if (voiceCapture.timerId) {
    clearInterval(voiceCapture.timerId);
    voiceCapture.timerId = 0;
  }
}

function releaseVoiceStream() {
  if (voiceCapture.stream) {
    voiceCapture.stream.getTracks().forEach((track) => track.stop());
    voiceCapture.stream = null;
  }
}

function endVoiceHold() {
  voiceCapture.pressActive = false;
  if (!voiceCapture.holding) return;
  voiceCapture.holding = false;
  // the browser still fires a click after this release; it must not be
  // mistaken for a stop-button press on the job this release submits
  voiceFabSuppressClickUntil = Date.now() + 600;
  stopVoiceRecordingUi();
  const recorder = voiceCapture.recorder;
  if (!recorder || recorder.state === "inactive") {
    releaseVoiceStream();
    toast("未识别到语音内容");
    return;
  }
  recorder.stop();
}

function cancelVoiceHold() {
  voiceCapture.pressActive = false;
  if (!voiceCapture.holding) return;
  voiceCapture.holding = false;
  voiceFabSuppressClickUntil = Date.now() + 600;
  stopVoiceRecordingUi();
  const recorder = voiceCapture.recorder;
  voiceCapture.recorder = null;
  voiceCapture.chunks = [];
  if (recorder && recorder.state !== "inactive") {
    recorder.onstop = null;
    try { recorder.stop(); } catch { /* already stopped */ }
  }
  releaseVoiceStream();
}

function finishVoiceRecording() {
  releaseVoiceStream();
  const chunks = voiceCapture.chunks;
  voiceCapture.chunks = [];
  voiceCapture.recorder = null;
  if (!chunks.length) {
    toast("未识别到语音内容");
    return;
  }
  const blob = new Blob(chunks, { type: chunks[0].type || "audio/webm" });
  submitVoiceTodo(blob);
}

function renderVoiceLiveText() {
  const bubble = $("voice-todo-live");
  if (!bubble || !voiceCapture.holding) return;
  const seconds = Math.floor((Date.now() - voiceCapture.startedAt) / 1000);
  bubble.classList.remove("hidden");
  bubble.innerHTML = `<small>正在聆听… ${seconds}s · 松开转为 TODO</small><span class='voice-live-empty'>语音由本地识别服务转写，浏览器内不联网</span>`;
}

function audioBufferToWav16kMono(audioBuffer) {
  const targetRate = 16000;
  const channels = audioBuffer.numberOfChannels;
  const length = audioBuffer.length;
  const mono = new Float32Array(length);
  for (let c = 0; c < channels; c += 1) {
    const data = audioBuffer.getChannelData(c);
    for (let i = 0; i < length; i += 1) mono[i] += data[i] / channels;
  }
  const ratio = audioBuffer.sampleRate / targetRate;
  const outLength = Math.max(1, Math.floor(length / ratio));
  const samples = new Int16Array(outLength);
  for (let i = 0; i < outLength; i += 1) {
    const position = i * ratio;
    const index = Math.floor(position);
    const fraction = position - index;
    const current = mono[index] || 0;
    const next = mono[Math.min(index + 1, length - 1)] || 0;
    samples[i] = Math.max(-1, Math.min(1, current + (next - current) * fraction)) * 32767;
  }
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);
  const writeString = (offset, text) => {
    for (let i = 0; i < text.length; i += 1) view.setUint8(offset + i, text.charCodeAt(i));
  };
  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, targetRate, true);
  view.setUint32(28, targetRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);
  let offset = 44;
  for (let i = 0; i < samples.length; i += 1, offset += 2) view.setInt16(offset, samples[i], true);
  return new Blob([view], { type: "audio/wav" });
}

async function recordingBlobToWav(blob) {
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const context = new AudioCtx();
  try {
    const audioBuffer = await context.decodeAudioData(await blob.arrayBuffer());
    return { wav: audioBufferToWav16kMono(audioBuffer), duration: audioBuffer.duration };
  } finally {
    context.close();
  }
}

const voiceJobs = new Map();

const VOICE_FAB_MIC_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3.5a2.8 2.8 0 0 1 2.8 2.8v5.7a2.8 2.8 0 0 1-5.6 0V6.3A2.8 2.8 0 0 1 12 3.5z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"></path><path d="M5.8 11.5a6.2 6.2 0 0 0 12.4 0M12 17.7v2.8M8.8 20.5h6.4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"></path></svg>';
const VOICE_FAB_STOP_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="7" y="7" width="10" height="10" rx="2" fill="currentColor"></rect></svg>';

function activeVoiceJobId() {
  for (const [id, job] of voiceJobs) {
    if (job.status === "transcribing" || job.status === "structuring") return id;
  }
  return null;
}

function updateVoiceFabMode() {
  const fab = $("voice-todo-fab");
  if (!fab || !voiceRecordingSupported()) return;
  const stopping = activeVoiceJobId() !== null;
  fab.classList.toggle("is-stopping", stopping);
  fab.setAttribute("aria-label", stopping ? "停止当前语音任务" : "按住说话，创建语音 TODO");
  fab.title = stopping ? "点击停止当前语音任务" : "按住说话，创建语音 TODO";
  fab.innerHTML = stopping ? VOICE_FAB_STOP_SVG : VOICE_FAB_MIC_SVG;
}

let voiceCancelInFlight = false;
let voiceFabSuppressClickUntil = 0;

async function cancelActiveVoiceJob() {
  if (voiceCancelInFlight) return;
  const id = activeVoiceJobId();
  if (id === null) return;
  voiceCancelInFlight = true;
  try {
    await api(`/api/voice-jobs/${id}/cancel`, { method: "POST", body: "{}" });
    voiceJobs.delete(id);
    toast("已取消语音任务");
  } catch {
    // the job finished before the cancel landed; sync its final state instead
    pollVoiceJobs();
    return;
  } finally {
    voiceCancelInFlight = false;
  }
  renderVoiceJobProgress();
  updateVoiceFabMode();
}

async function restoreQueues() {
  try {
    const data = await api("/api/task-queue");
    const tasks = data.tasks || [];
    for (const task of tasks) {
      if (task.kind === "voice") {
        voiceJobs.set(task.id, { status: task.status, transcript: "" });
      } else if (task.kind === "report") {
        reportJobs.set(task.id, { projectId: task.project_id, status: task.status });
      } else if (task.kind === "template") {
        reportJobs.set(task.id, { projectId: task.project_id, kind: "template", status: task.status });
      }
    }
    if (voiceJobs.size) {
      renderVoiceJobProgress();
      startVoiceJobPolling();
    }
    if (reportJobs.size) {
      renderQueueProgress(data);
      startQueuePolling();
    }
  } catch {
    // transient error on load; polling can be restarted by the next submission
  }
  updateVoiceFabMode();
}

function truncateVoiceTranscript(text) {
  const cleaned = String(text || "").trim().replace(/\s+/g, " ");
  return cleaned.length > 64 ? `${cleaned.slice(0, 64)}…` : cleaned;
}

async function submitVoiceTodo(blob) {
  let payload;
  try {
    const { wav, duration } = await recordingBlobToWav(blob);
    if (duration < 0.4) {
      toast("未识别到语音内容");
      return;
    }
    payload = { audio_base64: await fileToBase64(wav), content_type: "audio/wav" };
  } catch (error) {
    toast(`录音转换失败：${error.message}`);
    return;
  }
  try {
    const data = await api("/api/todos/voice", { method: "POST", body: JSON.stringify(payload) });
    voiceJobs.set(data.id, { status: data.status || "queued", transcript: "" });
    renderVoiceJobProgress();
    startVoiceJobPolling();
    updateVoiceFabMode();
    toast("语音已提交，后台转写整理中");
  } catch (error) {
    toast(error.message.startsWith("task queue is full")
      ? `任务队列已满（并行 ${state.queueParallelism}，容量 ${state.queueCapacity}），请稍后再试`
      : error.message);
  }
}

function startVoiceJobPolling() {
  if (voiceJobs.timer) return;
  voiceJobs.timer = setInterval(pollVoiceJobs, 1500);
  pollVoiceJobs();
}

async function pollVoiceJobs() {
  for (const [id, job] of Array.from(voiceJobs.entries())) {
    let data;
    try {
      data = await api(`/api/voice-jobs/${id}`);
    } catch {
      continue;
    }
    job.status = data.status;
    job.transcript = data.transcript || "";
    if (data.status === "completed") {
      voiceJobs.delete(id);
      await loadTodos().catch(() => {});
      toast(data.fallback
        ? `语音整理失败，已按原始转写创建 TODO：${data.error || "未知错误"}`
        : `语音 TODO 已创建（${(data.todo_ids || []).length} 条）`);
    } else if (data.status === "failed") {
      voiceJobs.delete(id);
      toast(`语音处理失败：${data.error || "未知错误"}`);
    }
  }
  if (!voiceJobs.size && voiceJobs.timer) {
    clearInterval(voiceJobs.timer);
    voiceJobs.timer = 0;
  }
  renderVoiceJobProgress();
  updateVoiceFabMode();
}

function renderVoiceJobProgress() {
  const bubble = $("voice-todo-progress");
  if (!bubble) return;
  const jobs = Array.from(voiceJobs.values());
  if (!jobs.length) {
    bubble.classList.add("hidden");
    return;
  }
  const job = jobs[jobs.length - 1];
  bubble.classList.remove("hidden");
  const stage = job.status === "structuring"
    ? "转写完成，正在整理 TODO…"
    : job.status === "queued"
      ? "排队等待中…"
      : "正在转写语音…";
  const transcript = truncateVoiceTranscript(job.transcript);
  bubble.innerHTML = `<small>${escapeHtml(stage)}</small>${
    transcript ? `<span class="voice-job-transcript">${escapeHtml(transcript)}</span>` : "<span class='voice-live-empty'>等待识别结果…</span>"
  }`;
}

function renderVoiceSettings() {
  const endpoint = $("asr-endpoint-input");
  if (endpoint) endpoint.value = state.asrEndpoint || "";
  const model = $("asr-model-input");
  if (model) model.value = state.asrModel || "";
  const language = $("asr-language-select");
  if (language) language.value = ["zh", "en", "auto"].includes(state.asrLanguage) ? state.asrLanguage : "zh";
  refreshAutoSaveSnapshot("voice-settings");
}

async function saveVoiceSettings() {
  const data = await api("/api/settings", {
    method: "PUT",
    body: JSON.stringify({
      asr_endpoint: $("asr-endpoint-input")?.value || "",
      asr_model: $("asr-model-input")?.value || "",
      asr_language: $("asr-language-select")?.value || "",
    }),
  });
  state.asrEndpoint = data.asr_endpoint;
  state.asrModel = data.asr_model;
  state.asrLanguage = data.asr_language;
}

function renderLlmSettings() {
  const select = $("llm-provider-select");
  if (!select) return;
  select.value = state.llmProvider === "anthropic" ? "anthropic" : "openai";
  const baseUrl = $("llm-base-url-input");
  if (baseUrl) baseUrl.value = state.llmBaseUrl || "";
  const model = $("llm-model-input");
  if (model) model.value = state.llmModel || "";
  const key = $("llm-api-key-input");
  if (key) {
    key.value = "";
    key.placeholder = state.llmApiKeySet ? "已配置，留空保持不变" : "sk-...";
  }
  refreshAutoSaveSnapshot("llm-settings");
}

async function saveLlmSettings() {
  const select = $("llm-provider-select");
  if (!select) return;
  const payload = {
    llm_provider: select.value,
    llm_base_url: $("llm-base-url-input")?.value || "",
    llm_model: $("llm-model-input")?.value || "",
  };
  const keyInput = $("llm-api-key-input");
  if (keyInput && keyInput.value.trim()) payload.llm_api_key = keyInput.value.trim();
  const data = await api("/api/settings", { method: "PUT", body: JSON.stringify(payload) });
  state.llmProvider = data.llm_provider;
  state.llmBaseUrl = data.llm_base_url;
  state.llmModel = data.llm_model;
  state.llmApiKeySet = !!data.llm_api_key_set;
  // 自动保存中不能整块重绘（会打断输入），只刷新 Key 占位提示
  if (keyInput) {
    keyInput.placeholder = state.llmApiKeySet ? "已配置，留空保持不变" : "sk-...";
  }
}

function renderQueueSettings() {
  const capacity = $("queue-capacity-input");
  if (!capacity) return;
  capacity.value = state.queueCapacity || 5;
  const parallel = $("queue-parallelism-input");
  if (parallel) parallel.value = state.queueParallelism || 2;
  refreshAutoSaveSnapshot("queue-settings");
}

async function saveQueueSettings() {
  const capacity = Number($("queue-capacity-input")?.value);
  const parallelism = Number($("queue-parallelism-input")?.value);
  if (!Number.isInteger(capacity) || capacity < 1 || !Number.isInteger(parallelism) || parallelism < 1) {
    throw new Error("队列容量和并行执行数需为正整数");
  }
  const data = await api("/api/settings", {
    method: "PUT",
    body: JSON.stringify({
      queue_capacity: capacity,
      queue_parallelism: parallelism,
    }),
  });
  state.queueCapacity = data.queue_capacity;
  state.queueParallelism = data.queue_parallelism;
}

const GITHUB_TOKEN_KIND_LABELS = { classic: "经典", "fine-grained": "细粒度" };

function renderGithubTokenList() {
  const list = $("github-token-list");
  if (!list) return;
  const rows = state.githubTokens.map((entry) => ({ label: entry.label || "", owner: entry.owner || "", hint: entry.hint || "", kind: entry.kind || "" }));
  if (!rows.length) rows.push({ label: "", owner: "", hint: "", kind: "" });
  list.innerHTML = rows.map((entry) => {
    const kindLabel = GITHUB_TOKEN_KIND_LABELS[entry.kind] || "";
    return `
    <div class="github-token-row" data-github-token-row>
      <input data-github-token-label placeholder="名称（可选）" value="${escapeAttr(entry.label)}">
      <input data-github-token-owner placeholder="组织名，留空=个人/通用" value="${escapeAttr(entry.owner)}">
      <input data-github-token-value type="password" autocomplete="off" placeholder="${entry.hint ? `已配置 ${entry.hint}，留空保持不变` : "ghp_... / github_pat_..."}">
      ${kindLabel ? `<span class="status connected" title="按 token 前缀自动识别">${kindLabel}</span>` : "<span></span>"}
      <button type="button" class="danger" onclick="removeGithubTokenRow(this)">删除</button>
    </div>
  `;}).join("");
}

function collectGithubTokenRows() {
  return Array.from(document.querySelectorAll("[data-github-token-row]")).map((row) => ({
    label: row.querySelector("[data-github-token-label]")?.value.trim() || "",
    owner: row.querySelector("[data-github-token-owner]")?.value.trim() || "",
    token: row.querySelector("[data-github-token-value]")?.value.trim() || "",
  }));
}

function addGithubTokenRow() {
  state.githubTokens = collectGithubTokenRows();
  state.githubTokens.push({ label: "", owner: "", hint: "" });
  renderGithubTokenList();
  refreshAutoSaveSnapshot("git-settings");
  const rows = document.querySelectorAll("[data-github-token-row]");
  rows[rows.length - 1]?.querySelector("[data-github-token-label]")?.focus();
}

function removeGithubTokenRow(button) {
  button.closest("[data-github-token-row]")?.remove();
}

function renderGitSettings() {
  renderGithubTokenList();
  const gitlabUrl = $("gitlab-url-input");
  if (gitlabUrl) gitlabUrl.value = state.gitlabUrl || "";
  const gitlabToken = $("gitlab-token-input");
  gitlabToken.value = "";
  gitlabToken.placeholder = state.gitlabTokenSet ? "已配置，留空保持不变" : "glpat-...";
  const gitlabSkipVerify = $("gitlab-skip-verify-input");
  if (gitlabSkipVerify) gitlabSkipVerify.checked = !!state.gitlabSkipVerify;
  const githubEnabled = $("github-enabled-input");
  if (githubEnabled) githubEnabled.checked = state.githubEnabled !== false;
  const gitlabEnabled = $("gitlab-enabled-input");
  if (gitlabEnabled) gitlabEnabled.checked = state.gitlabEnabled !== false;
  refreshAutoSaveSnapshot("git-settings");
}

async function saveGitSettings() {
  const payload = {};
  const githubTokenRows = collectGithubTokenRows().filter((row) => row.label || row.owner || row.token);
  if (githubTokenRows.length) payload.github_tokens = githubTokenRows;
  payload.gitlab_url = $("gitlab-url-input")?.value.trim() || "";
  const gitlabToken = $("gitlab-token-input")?.value.trim();
  if (gitlabToken) payload.gitlab_token = gitlabToken;
  payload.gitlab_skip_verify = !!($("gitlab-skip-verify-input")?.checked);
  if (state.isAdmin) {
    payload.github_enabled = !!($("github-enabled-input")?.checked);
    payload.gitlab_enabled = !!($("gitlab-enabled-input")?.checked);
  }
  const data = await api("/api/settings", { method: "PUT", body: JSON.stringify(payload) });
  state.githubEnabled = data.github_enabled !== false;
  state.gitlabEnabled = data.gitlab_enabled !== false;
  state.githubTokenSet = !!data.github_token_set;
  state.githubTokens = data.github_tokens || [];
  state.gitlabTokenSet = !!data.gitlab_token_set;
  state.gitlabUrl = data.gitlab_url || "";
  state.gitlabSkipVerify = !!data.gitlab_skip_verify;
  // 自动保存中不能重绘正在编辑的输入框，只刷新令牌占位提示
  const list = $("github-token-list");
  if (list && !list.contains(document.activeElement)) renderGithubTokenList();
  const gitlabTokenInput = $("gitlab-token-input");
  if (gitlabTokenInput) {
    gitlabTokenInput.placeholder = state.gitlabTokenSet ? "已配置，留空保持不变" : "glpat-...";
  }
}

async function loadUsers() {
  const data = await api("/api/users");
  state.users = data.users || [];
  renderUsers();
}

function renderUsers() {
  const body = $("user-table-body");
  if (!body) return;
  body.innerHTML = (state.users || []).map((user) => `
    <tr>
      <td data-label="用户名"><strong>${escapeHtml(user.username)}</strong>${user.id === state.currentUser?.id ? '<small>（当前账号）</small>' : ""}</td>
      <td data-label="角色">${user.is_admin ? '<span class="status connected">管理员</span>' : "成员"}</td>
      <td data-label="状态">${user.enabled ? '<span class="status active">启用</span>' : '<span class="status disabled">停用</span>'}</td>
      <td data-label="操作"><div class="table-actions">
        <button type="button" onclick="resetUserPassword(${user.id})">重置密码</button>
        <button type="button" onclick="setUserAdmin(${user.id}, ${user.is_admin ? "false" : "true"})">${user.is_admin ? "收回管理员" : "设为管理员"}</button>
        ${user.enabled
          ? `<button type="button" onclick="setUserEnabled(${user.id}, false)">停用</button>`
          : `<button type="button" onclick="setUserEnabled(${user.id}, true)">启用</button>`}
        <button type="button" class="danger" onclick="deleteUserAccount(${user.id})">删除</button>
      </div></td>
    </tr>
  `).join("") || "<tr><td colspan='4'>暂无用户。</td></tr>";
}

async function createUser() {
  const username = $("new-user-username").value.trim();
  const password = $("new-user-password").value;
  if (!username || !password) return toast("请填写用户名和密码");
  try {
    await api("/api/users", {
      method: "POST",
      body: JSON.stringify({ username, password, is_admin: $("new-user-admin").checked }),
    });
    $("new-user-username").value = "";
    $("new-user-password").value = "";
    $("new-user-admin").checked = false;
    await loadUsers();
    toast("用户已创建");
  } catch (error) {
    toast(error.message);
  }
}

function resetUserPassword(id) {
  const user = (state.users || []).find((item) => item.id === id);
  $("reset-password-user-id").value = String(id);
  $("reset-password-title").textContent = user ? `为「${user.username}」设置新密码` : `为用户 ${id} 设置新密码`;
  $("reset-password-input").value = "";
  $("reset-password-dialog").showModal();
}

async function setUserAdmin(id, isAdmin) {
  try {
    await api(`/api/users/${id}`, { method: "PUT", body: JSON.stringify({ is_admin: isAdmin }) });
    await loadUsers();
    toast(isAdmin ? "已设为管理员" : "已收回管理员");
  } catch (error) {
    toast(error.message);
  }
}

async function setUserEnabled(id, enabled) {
  try {
    await api(`/api/users/${id}`, { method: "PUT", body: JSON.stringify({ enabled }) });
    await loadUsers();
    toast(enabled ? "已启用该账号" : "已停用该账号");
  } catch (error) {
    toast(error.message);
  }
}

function deleteUserAccount(id) {
  const user = (state.users || []).find((item) => item.id === id);
  state.pendingDeleteUserId = id;
  $("user-delete-title").textContent = user ? user.username : `用户 ${id}`;
  $("user-delete-dialog").showModal();
}

async function runUserDelete() {
  const id = state.pendingDeleteUserId;
  state.pendingDeleteUserId = null;
  if (!id) return;
  try {
    await api(`/api/users/${id}`, { method: "DELETE" });
    await loadUsers();
    toast("用户已删除");
  } catch (error) {
    toast(error.message);
  }
}

async function changeOwnPassword() {
  const oldPassword = $("password-old-input")?.value || "";
  const newPassword = $("password-new-input")?.value || "";
  try {
    await api("/api/auth/password", {
      method: "PUT",
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    });
    $("password-old-input").value = "";
    $("password-new-input").value = "";
    toast("密码已更新");
  } catch (error) {
    toast(error.message);
  }
}

function projectPaused(p) {
  return p.status === "paused";
}

function projectRowHtml(p) {
  const paused = projectPaused(p);
  return `
    <div class="project-row${p.id === state.projectId ? " active" : ""}${paused ? " paused" : ""}">
      <button class="project-item" data-project="${p.id}" aria-label="${escapeAttr(`${p.name}，${projectDisplayStatus(p)}`)}">
        ${statusDot(projectDisplayStatus(p), "project-item-status")}
        <strong>${escapeHtml(p.name)}</strong>
        ${paused ? '<small class="project-item-flag">已停用</small>' : ""}
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
      renderProjects();
      await loadWorkspaceBusy("切换项目");
    };
  });
  document.querySelectorAll("[data-project-settings]").forEach(btn => {
    btn.onclick = async () => {
      closeProjectSheet();
      const projectId = Number(btn.dataset.projectSettings);
      if (state.projectId !== projectId) {
        state.projectId = projectId;
        localStorage.setItem("currentProjectId", String(state.projectId));
        renderProjects();
        await loadWorkspaceBusy("切换项目");
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
  const displayStatus = ws.project.status === "paused" ? "paused" : ws.progress_status;
  const projectBarDot = $("project-bar-dot");
  projectBarDot.className = `status-dot ${statusTone(displayStatus)}`;
  projectBarDot.title = statusLabel(displayStatus);
  $("project-meta").textContent = ws.week_key;
  const projectStatusDot = $("project-status-dot");
  projectStatusDot.className = `status-dot ${statusTone(displayStatus)}`;
  projectStatusDot.title = statusLabel(displayStatus);
  projectStatusDot.setAttribute("aria-label", `项目状态：${statusLabel(displayStatus)}`);
  renderProjects();
  renderOverview(ws);
  renderSettings(ws);
  renderPlan(ws);
  renderUpdates(ws);
  renderSources(ws);
  renderReport(ws);
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
    <div class="source-tabs" role="tablist" aria-label="设置分类">
      <button type="button" data-subtab="project" role="tab" onclick="switchSettingsSubTab('project')">项目设置</button>
      <button type="button" data-subtab="git" role="tab" onclick="switchSettingsSubTab('git')">Git 仓库</button>
      <button type="button" data-subtab="diagnostics" role="tab" onclick="switchSettingsSubTab('diagnostics')">系统诊断</button>
    </div>
    <section id="settings-sub-project" class="source-view" role="tabpanel">
      <form id="settings-form" class="panel form-grid">
        <div class="panel-head wide">
          <div class="panel-title"><h2>项目设置</h2><span>项目与报告配置 · 修改后自动保存</span><span class="autosave-status" aria-live="polite"></span></div>
        </div>
        ${input("name", "名称", p.name)}
        ${projectRunToggle(p)}
        ${input("start_date", "开始日期", p.start_date, "date")}
        ${input("end_date", "结束日期", p.end_date || "", "date")}
        ${timezoneSelect("timezone", "时区", p.timezone)}
        ${textarea("description", "描述", p.description, "wide")}
        ${templateField(p)}
        <div class="wide panel">
          <div class="panel-head"><h3>更新时间点</h3><span>同一项目周内覆盖当前周报</span></div>
          <div id="schedule-list">${renderSchedules(ws.schedules, p.timezone)}</div>
          <button type="button" onclick="addSchedule()">+ 添加时间点</button>
        </div>
      </form>
    </section>
    <section id="settings-sub-git" class="source-view hidden" role="tabpanel">
      <div class="panel">
        <div class="panel-head"><h2>Git 仓库</h2><span>GitHub / GitLab，本周 commits 会进入生成上下文</span></div>
        <div class="row">
          <select id="repo-mode-input" onchange="onRepoModeChange()" aria-label="Git 模式">${state.githubEnabled !== false ? '<option value="github">GitHub</option>' : ""}${state.gitlabEnabled !== false ? '<option value="gitlab">GitLab</option>' : ""}</select>
          <input id="repo-input" placeholder="owner/repo">
          <input id="repo-notes-input" placeholder="补充说明，例如正式名称、模块边界">
          <button type="button" onclick="addRepo()">添加仓库</button>
        </div>
        <table class="table"><thead><tr><th>仓库</th><th>跟踪分支</th><th>补充说明</th><th>状态</th><th>操作</th></tr></thead><tbody>${ws.repos.map(renderRepoRow).join("") || "<tr><td colspan='5'>暂无仓库。</td></tr>"}</tbody></table>
      </div>
    </section>
    <section id="settings-sub-diagnostics" class="source-view hidden" role="tabpanel">
      <div class="panel">
        <div class="panel-head"><h2>系统诊断</h2><span>资料源与生成状态</span></div>
        <table class="table"><thead><tr><th>类型</th><th>严重度</th><th>标题</th><th>更新时间</th></tr></thead><tbody>${(ws.source_diagnostics || []).map(d => `<tr><td>${escapeHtml(d.kind)}</td><td><span class="status ${d.severity}">${escapeHtml(statusLabel(d.severity))}</span></td><td>${escapeHtml(d.title)}<br>${escapeHtml(d.details || "")}</td><td>${escapeHtml(formatChinaTime(d.updated_at))}</td></tr>`).join("") || "<tr><td colspan='4'>暂无诊断信息。</td></tr>"}</tbody></table>
      </div>
    </section>
  `;
  $("settings-form").onsubmit = saveSettings;
  setupAutoSave("project-settings", $("settings-form"), saveSettings);
  // 仓库行的补充说明与分支勾选也是填写即保存（分支 change 事件会冒泡到行上）
  document.querySelectorAll("textarea[id^='repo-notes-']").forEach((el) => {
    const id = Number(el.id.replace("repo-notes-", ""));
    setupAutoSave(`repo-notes-${id}`, el.closest("tr"), () => saveRepoNotes(id));
  });
  onRepoModeChange();
  switchSettingsSubTab(state.settingsSubTab);
}

function switchSettingsSubTab(tab) {
  state.settingsSubTab = tab;
  const root = $("tab-settings");
  root.querySelectorAll("[data-subtab]").forEach((button) => {
    const active = button.dataset.subtab === tab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  ["project", "git", "diagnostics"].forEach((name) => {
    const view = root.querySelector(`#settings-sub-${name}`);
    if (view) view.classList.toggle("hidden", name !== tab);
  });
}

function templateJobPending() {
  for (const job of reportJobs.values()) {
    if (job.kind === "template" && job.projectId === state.projectId) return true;
  }
  return false;
}

function templateField(p) {
  const pending = templateJobPending();
  return `
    <div class="wide template-field">
      <div class="template-field-head">
        <span>项目周报模板</span>
        <button type="button" id="template-wand-btn" class="template-wand" title="AI 生成周报模板" aria-label="AI 生成周报模板" onclick="suggestReportTemplate()" ${pending ? "disabled" : ""}>${faIcon("wand")}</button>
      </div>
      <textarea name="report_template">${escapeHtml(p.report_template || "")}</textarea>
      <small id="template-field-hint">${pending ? "模板生成中，完成后自动保存并刷新…" : "魔棒按当前填写内容、项目数据来源与最近一期周报生成模板，生成后自动保存"}</small>
    </div>
  `;
}

async function suggestReportTemplate() {
  const field = document.querySelector("#settings-form textarea[name='report_template']");
  if (!field) return;
  try {
    const data = await api(`/api/projects/${state.projectId}/suggest-template`, {
      method: "POST",
      body: JSON.stringify({ requirements: field.value }),
    });
    reportJobs.set(data.id, { projectId: state.projectId, kind: "template", status: data.status || "queued" });
    const hint = document.querySelector("#template-field-hint");
    if (hint) hint.textContent = "模板生成中，完成后自动保存并刷新…";
    const wand = document.querySelector("#template-wand-btn");
    if (wand) wand.disabled = true;
    toast("模板生成任务已提交，完成后自动保存");
    startQueuePolling();
  } catch (error) {
    toast(`模板生成任务提交失败：${error.message}`);
  }
}

async function templateJobFinished(jobId, job) {
  let finished = null;
  try {
    finished = await api(`/api/projects/${job.projectId}/workspace`);
  } catch {
    toast("模板任务已结束");
    return;
  }
  if (job.projectId === state.projectId) updateWorkspace(finished);
  const record = finished.template_job;
  const name = (finished.project && finished.project.name) || "项目";
  if (record && record.id === jobId && record.status === "success") toast(`「${name}」周报模板已生成并保存`);
  else toast(`「${name}」模板生成失败：${(record && record.failure_reason) || "未知错误"}`);
}

function projectRunToggle(p) {
  const running = p.status !== "paused";
  return `
    <div class="wide project-toggle-row">
      <label class="switch" title="${running ? "已启用 · 按计划自动生成周报" : "已停用 · 不再自动生成周报"}">
        <input id="project-enabled-input" type="checkbox" aria-label="项目启停" ${running ? "checked" : ""} onchange="syncProjectToggleState(this)">
        <span class="switch-slider"></span>
      </label>
      <div class="project-toggle-copy">
        <span class="project-toggle-state">${running ? "已启用 · 按计划自动生成周报" : "已停用 · 不再自动生成周报"}</span>
        <small>停止后项目在菜单中置灰，可随时重新开启</small>
      </div>
    </div>
  `;
}

function syncProjectToggleState(input) {
  const state = input.closest(".project-toggle-row")?.querySelector(".project-toggle-state");
  if (!state) return;
  state.textContent = input.checked ? "已启用 · 按计划自动生成周报" : "已停用 · 不再自动生成周报";
}

function onRepoModeChange() {
  const gitlab = $("repo-mode-input") && $("repo-mode-input").value === "gitlab";
  if (!$("repo-input")) return;
  $("repo-input").placeholder = gitlab ? "group/project 或 group/sub-group/project" : "owner/repo";
}

function renderRepoRow(r) {
  const enabled = Number(r.enabled) !== 0;
  const modeLabel = r.git_mode === "gitlab" ? "GitLab" : "GitHub";
  return `
    <tr class="${enabled ? "" : "repo-row-disabled"}">
      <td data-label="仓库"><span class="status">${modeLabel}</span><br>${escapeHtml(r.repo)}</td>
      <td data-label="跟踪分支">${renderBranchPicker(r)}</td>
      <td data-label="补充说明"><textarea id="repo-notes-${r.id}" class="table-textarea">${escapeHtml(r.notes || "")}</textarea></td>
      <td data-label="启用">${enabled
        ? `<span class="status ${r.status}">${escapeHtml(r.status)}</span><br>${escapeHtml(r.status_message || "")}`
        : `<span class="status disabled">已停用</span><br>不参与周报生成`}</td>
      <td data-label="操作"><div class="table-actions"><label class="switch" title="${enabled ? "已启用 · 参与周报生成" : "已停用 · 不参与周报生成"}"><input type="checkbox" aria-label="启用或停用该仓库" ${enabled ? "checked" : ""} onchange="toggleRepo(${r.id}, this.checked)"><span class="switch-slider"></span></label><button type="button" onclick="refreshRepo(${r.id})">刷新</button><button type="button" class="danger" onclick="deleteRepo(${r.id})">删除</button></div></td>
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
      <button type="button" class="danger" onclick="this.closest('.schedule-row').remove(); touchAutoSave('project-settings')">移除</button>
      <small class="schedule-last-fire">${s.last_checked_at ? `上次触发 ${escapeHtml(formatChinaTime(s.last_checked_at))}` : "尚未触发"}</small>
    </div>
  `;}).join("");
}

function addSchedule() {
  $("schedule-list").insertAdjacentHTML("beforeend", renderSchedules([{ weekday: 5, local_time: "18:00", timezone: CHINA_TIMEZONE }], CHINA_TIMEZONE));
  touchAutoSave("project-settings");
}

async function saveSettings(event) {
  event?.preventDefault();
  const form = $("settings-form");
  if (!form) return;
  const fd = new FormData(form);
  const schedules = Array.from(document.querySelectorAll("#schedule-list .schedule-row"))
    .map(row => ({
      enabled: row.querySelector("input[data-schedule-enabled]").checked,
      weekday: Number(row.querySelector("input[name='schedule_weekday']").value),
      local_time: row.querySelector("input[name='schedule_time']").value,
      timezone: row.querySelector("select[name='schedule_timezone']").value,
    }))
    .filter(s => s.local_time);
  const payload = Object.fromEntries(fd.entries());
  payload.status = $("project-enabled-input")?.checked ? "active" : "paused";
  payload.schedules = schedules;
  await api(`/api/projects/${state.projectId}/settings`, { method: "PUT", body: JSON.stringify(payload) });
  // 自动保存不整板刷新（会打断输入），只同步内存里的项目摘要并刷新侧栏
  if (state.workspace?.project) {
    Object.assign(state.workspace.project, {
      name: payload.name,
      description: payload.description,
      start_date: payload.start_date,
      end_date: payload.end_date,
      timezone: payload.timezone,
      report_template: payload.report_template,
      status: payload.status,
    });
    state.workspace.schedules = schedules;
  }
  const name = payload.name || "";
  $("project-title").textContent = name;
  $("project-bar-name").textContent = name;
  renderProjects();
}

function renderPlan(ws) {
  $("tab-plan").innerHTML = `
    <div class="source-tabs" role="tablist" aria-label="计划和风险">
      <button type="button" data-subtab="plan" role="tab" onclick="switchPlanSubTab('plan')">项目计划</button>
      <button type="button" data-subtab="risk" role="tab" onclick="switchPlanSubTab('risk')">进度风险</button>
    </div>
    <section id="plan-sub-plan" class="source-view" role="tabpanel">
      <form id="plan-form" class="panel">
        <div class="panel-head"><h2>项目计划</h2><span>里程碑与交付物 · 修改后自动保存</span><span class="autosave-status" aria-live="polite"></span></div>
        ${textarea("objectives", "目标", ws.plan.objectives)}
        <h3>里程碑</h3>
        <div id="milestones">${renderPlanItems(ws.plan.milestones)}</div>
        <button type="button" onclick="addPlanItem('milestones')">+ 添加里程碑</button>
        <h3>交付物</h3>
        <div id="deliverables">${renderPlanItems(ws.plan.deliverables)}</div>
        <button type="button" onclick="addPlanItem('deliverables')">+ 添加交付物</button>
      </form>
    </section>
    <section id="plan-sub-risk" class="source-view hidden" role="tabpanel">
      <div class="panel">
        <div class="panel-head"><h2>进度和风险</h2><span>仅项目相关风险</span></div>
        <p>进度状态：<span class="status ${ws.progress_status.replace(" ", "-")}">${escapeHtml(statusLabel(ws.progress_status))}</span></p>
        <table class="table"><thead><tr><th>严重度</th><th>规则</th><th>标题</th><th>状态</th></tr></thead><tbody>${ws.risks.map(r => `<tr><td data-label="严重度"><span class="status ${r.severity}">${statusLabel(r.severity)}</span></td><td data-label="规则">${escapeHtml(r.rule)}</td><td data-label="标题">${escapeHtml(r.title)}<br>${escapeHtml(r.details || "")}</td><td data-label="状态">${escapeHtml(statusLabel(r.status))}</td></tr>`).join("") || "<tr><td colspan='4'>暂无风险。</td></tr>"}</tbody></table>
      </div>
    </section>
  `;
  $("plan-form").onsubmit = savePlan;
  setupAutoSave("plan", $("plan-form"), savePlan);
  switchPlanSubTab(state.planSubTab);
}

function switchPlanSubTab(tab) {
  state.planSubTab = tab;
  const root = $("tab-plan");
  root.querySelectorAll("[data-subtab]").forEach((button) => {
    const active = button.dataset.subtab === tab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  ["plan", "risk"].forEach((name) => {
    const view = root.querySelector(`#plan-sub-${name}`);
    if (view) view.classList.toggle("hidden", name !== tab);
  });
}

function renderPlanItems(items) {
  return (items.length ? items : [{ title: "", status: "planned", owner_label: "", target_date: "" }]).map(item => `
    <div class="row plan-item">
      <input name="title" placeholder="标题" value="${escapeAttr(item.title || "")}">
      <input name="owner_label" placeholder="负责人" value="${escapeAttr(item.owner_label || "")}">
      <input name="target_date" type="date" value="${escapeAttr(item.target_date || "")}">
      <select name="status">${statusOptions(item.status)}</select>
      <button type="button" class="danger" onclick="this.closest('.plan-item').remove(); touchAutoSave('plan')">移除</button>
    </div>
  `).join("");
}

function addPlanItem(id) {
  $(id).insertAdjacentHTML("beforeend", renderPlanItems([{ title: "", status: "planned" }]));
}

async function savePlan(event) {
  event?.preventDefault();
  const form = $("plan-form");
  if (!form) return;
  const groups = (id) => Array.from($(id).querySelectorAll(".plan-item")).map(row => itemPayload(row)).filter(i => i.title);
  await api(`/api/projects/${state.projectId}/plan`, { method: "PUT", body: JSON.stringify({ objectives: form.objectives.value, milestones: groups("milestones"), deliverables: groups("deliverables") }) });
  if (state.workspace?.plan) {
    state.workspace.plan.objectives = form.objectives.value;
    state.workspace.plan.milestones = groups("milestones");
    state.workspace.plan.deliverables = groups("deliverables");
  }
}

const SUPPLEMENT_FIELDS = [
  ["completed", "已完成"],
  ["in_progress", "进行中"],
  ["blockers", "阻塞事项"],
  ["risks", "风险"],
  ["next_steps", "下一步计划"],
];

function supplementFieldsHtml(item) {
  return SUPPLEMENT_FIELDS.map(([key, label]) => {
    const value = (item[key] || "").trim();
    return value ? `<p><strong>${label}</strong><br>${escapeHtml(value)}</p>` : "";
  }).join("");
}

function renderUpdates(ws) {
  const u = ws.weekly_update || {};
  $("tab-updates").innerHTML = `
    <form id="update-form" class="panel form-grid">
      <div class="panel-head wide"><h2>本周补充</h2><span>${escapeHtml(ws.week_key)} · 修改后自动保存</span><span class="autosave-status" aria-live="polite"></span></div>
      ${textarea("completed", "已完成", u.completed || "", "wide")}
      ${textarea("in_progress", "进行中", u.in_progress || "", "wide")}
      ${textarea("blockers", "阻塞事项", u.blockers || "", "wide")}
      ${textarea("risks", "风险", u.risks || "", "wide")}
      ${textarea("next_steps", "下一步计划", u.next_steps || "", "wide")}
    </form>
    <div id="supplement-history" class="panel">
      <div class="panel-head"><h2>补充历史</h2><span>生成周报时同步留档</span></div>
      ${(ws.update_history || []).map(item => `
        <details class="history-report" data-history-week="${escapeAttr(item.week_key)}">
          <summary>${escapeHtml(item.week_key)}<small>更新于 ${escapeHtml(formatChinaTime(item.updated_at))}</small></summary>
          <div class="history-report-body">${supplementFieldsHtml(item) || "<p>该周没有填写内容。</p>"}</div>
        </details>
      `).join("") || "<p>还没有历史补充。</p>"}
    </div>
  `;
  $("update-form").onsubmit = saveWeeklyUpdate;
  setupAutoSave("weekly-update", $("update-form"), saveWeeklyUpdate);
}

async function saveWeeklyUpdate(event) {
  event?.preventDefault();
  const form = $("update-form");
  if (!form) return;
  const payload = Object.fromEntries(new FormData(form).entries());
  await api(`/api/projects/${state.projectId}/weekly-update`, { method: "PUT", body: JSON.stringify(payload) });
  if (state.workspace) state.workspace.weekly_update = payload;
}

function renderSources(ws) {
  $("tab-sources").innerHTML = `
    <div class="source-tabs" role="tablist" aria-label="资料类型">
      <button type="button" data-source-tab="manual" role="tab" onclick="switchSourceTab('manual')">手工资料</button>
      <button type="button" data-source-tab="files" role="tab" onclick="switchSourceTab('files')">文件资料</button>
    </div>
    <section id="source-files" class="source-view" role="tabpanel">
      <div class="panel source-panel">
        <div class="panel-head"><h2>文件资料</h2><span>本周新增资料会进入生成上下文</span></div>
        <label id="material-dropzone" class="upload-dropzone" for="material-file" role="button" tabindex="0">
          <input id="material-file" class="visually-hidden" type="file" accept=".md,.markdown,.txt,.html,.htm,.pdf" multiple>
          <span class="upload-icon" aria-hidden="true">↑</span>
          <strong>拖入文件，或点击选择</strong>
          <span id="material-selection">支持 Markdown、纯文本、HTML 和 PDF，可多选</span>
        </label>
        <div class="upload-actions">
          <button class="primary" type="button" onclick="uploadMaterial()">上传所选文件</button>
        </div>
        <table class="table material-table"><thead><tr><th>文件</th><th>提取</th><th>摘要</th><th>更新时间</th><th>操作</th></tr></thead><tbody>${ws.materials.filter(m => m.source_type !== "manual").map(renderUploadedMaterialRow).join("") || "<tr><td colspan='5'>暂无上传资料。</td></tr>"}</tbody></table>
      </div>
    </section>
    <section id="source-manual" class="source-view hidden" role="tabpanel">
      <div class="panel source-panel">
        <div class="panel-head"><h2>手工资料</h2><span>仅本周录入的资料可以修改 · 修改后自动保存</span><span class="autosave-status" aria-live="polite"></span></div>
        <div class="manual-material-form" id="manual-material-form">
          <input id="manual-material-title" placeholder="资料标题" onkeydown="if (event.key === 'Enter') addManualMaterial()">
          <textarea id="manual-material-content" placeholder="输入本周新增的背景、决策、会议记录或补充资料"></textarea>
          <div class="manual-material-actions"><button class="primary" type="button" onclick="addManualMaterial()">添加资料</button></div>
        </div>
        <table class="table"><thead><tr><th>标题</th><th>内容</th><th>创建时间</th><th>更新时间</th><th>操作</th></tr></thead><tbody>${ws.materials.filter(m => m.source_type === "manual").map(renderManualMaterialRow).join("") || "<tr><td colspan='5'>暂无手工资料。</td></tr>"}</tbody></table>
      </div>
    </section>
  `;
  switchSourceTab(state.sourceTab);
  setupMaterialDropzone();
  $("tab-sources").querySelectorAll("textarea[id^='material-summary-']").forEach((el) => {
    const id = Number(el.id.replace("material-summary-", ""));
    setupAutoSave(`material-summary-${id}`, el.closest("tr"), () => updateMaterialSummary(id));
  });
  $("tab-sources").querySelectorAll("input[id^='manual-title-']").forEach((el) => {
    const id = Number(el.id.replace("manual-title-", ""));
    setupAutoSave(`manual-material-${id}`, el.closest("tr"), () => updateManualMaterial(id));
  });
}

function switchSourceTab(tab) {
  state.sourceTab = tab;
  document.querySelectorAll("[data-source-tab]").forEach((button) => {
    const active = button.dataset.sourceTab === tab;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
  });
  ["manual", "files"].forEach((name) => {
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
    : "支持 Markdown、纯文本、HTML 和 PDF，可多选";
}

function renderUploadedMaterialRow(m) {
  const extractionMessage = m.extraction_error ? `<div class="material-message">${escapeHtml(m.extraction_error)}</div>` : "";
  const summaryMessage = m.summary_error ? `<div class="material-message">AI 摘要失败，当前显示回退摘要：${escapeHtml(m.summary_error)}</div>` : "";
  return `<tr>
    <td data-label="文件"><strong>${escapeHtml(m.filename)}</strong><small>${formatBytes(m.size_bytes)}</small></td>
    <td data-label="提取"><span class="status ${m.extraction_status}">${escapeHtml(m.extraction_status)}</span>${extractionMessage}</td>
    <td data-label="摘要"><textarea id="material-summary-${m.id}" class="table-textarea summary-editor">${escapeHtml(m.summary || "")}</textarea>${summaryMessage}</td>
    <td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}<small><span class="status ${m.summary_status}">${escapeHtml(m.summary_status)}</span></small></td>
    <td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button>${m.deletable ? `<button class="danger" onclick="deleteMaterial(${m.id})">删除</button>` : ""}</div></td>
  </tr>`;
}

function renderManualMaterialRow(m) {
  const content = escapeHtml(m.content || "");
  if (m.editable) {
    return `<tr><td data-label="标题"><input id="manual-title-${m.id}" value="${escapeAttr(m.filename)}"></td><td data-label="内容"><textarea id="manual-content-${m.id}" class="table-textarea material-editor">${content}</textarea></td><td data-label="创建时间">${escapeHtml(formatChinaTime(m.created_at))}</td><td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}</td><td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button><button class="danger" onclick="deleteMaterial(${m.id})">删除</button></div></td></tr>`;
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
    } else if (material.preview_kind === "html") {
      // srcdoc keeps the server's X-Frame-Options: DENY out of the way, and the
      // empty sandbox blocks scripts, forms, and navigation inside the frame
      const frame = $("material-preview-pdf");
      frame.srcdoc = material.content_html || "";
      frame.setAttribute("sandbox", "");
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
  pdf.removeAttribute("srcdoc");
  pdf.removeAttribute("sandbox");
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
}

async function addManualMaterial() {
  const title = $("manual-material-title")?.value.trim() || "";
  const content = $("manual-material-content")?.value || "";
  if (!title) {
    toast("请填写资料标题");
    $("manual-material-title")?.focus();
    return;
  }
  await api(`/api/projects/${state.projectId}/materials`, {
    method: "POST",
    body: JSON.stringify({ source_type: "manual", title, content }),
  });
  $("manual-material-title").value = "";
  $("manual-material-content").value = "";
  toast("资料已添加");
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
}

async function deleteMaterial(id) {
  if (!window.confirm("确定删除这条资料？删除后无法恢复。")) return;
  const workspace = await api(`/api/projects/${state.projectId}/materials/${id}`, { method: "DELETE" });
  updateWorkspace(workspace);
  toast("资料已删除");
}

async function addRepo() {
  const payload = { repo: $("repo-input").value, notes: $("repo-notes-input").value, git_mode: $("repo-mode-input").value };
  await api(`/api/projects/${state.projectId}/repos`, { method: "POST", body: JSON.stringify(payload) });
  toast("仓库已保存");
  await loadWorkspace();
}

async function saveRepoNotes(id) {
  const branches = selectedRepoBranches(id);
  if (!branches.length) throw new Error("请至少选择一个跟踪分支");
  const repo = (state.workspace.repos || []).find((item) => item.id === id);
  const payload = { notes: $(`repo-notes-${id}`).value, branches, git_mode: repo && repo.git_mode === "gitlab" ? "gitlab" : "github" };
  await api(`/api/projects/${state.projectId}/repos/${id}`, { method: "PUT", body: JSON.stringify(payload) });
  if (repo) Object.assign(repo, payload);
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
  const via = repo && repo.git_mode === "gitlab" ? "GitLab" : "GitHub";
  const data = await withBusy("正在读取分支", `正在通过 ${via} API 获取仓库分支列表...`, async () => (
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
    <details class="history-report" data-history-week="${escapeAttr(report.week_key)}" ontoggle="onHistoryReportToggle(this)">
      <summary><strong>${escapeHtml(report.week_key)}</strong><span>${escapeHtml(formatChinaTime(report.updated_at))}</span><span class="status">read-only</span></summary>
      <div class="row"><button type="button" onclick="exportReportPdf('${escapeAttr(report.week_key)}')">导出 PDF</button></div>
      <article class="report history-report-body"><p>展开时加载正文…</p></article>
    </details>
  `;
}

async function onHistoryReportToggle(details) {
  if (!details.open) return;
  const body = details.querySelector(".history-report-body");
  if (!body || body.dataset.loaded === "1") return;
  body.dataset.loaded = "1";
  const weekKey = details.dataset.historyWeek;
  try {
    const data = await api(`/api/projects/${state.projectId}/reports/${encodeURIComponent(weekKey)}`);
    const supplement = data.supplement
      ? `<div class="panel"><div class="panel-head"><h3>该周补充</h3><span>生成周报时留档</span></div>${supplementFieldsHtml(data.supplement) || "<p>该周没有填写内容。</p>"}</div>`
      : "";
    body.innerHTML = data.content_html + supplement;
  } catch (error) {
    body.dataset.loaded = "";
    body.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
  }
}

function exportReportPdf(weekKey) {
  window.location.href = `/api/projects/${state.projectId}/reports/${encodeURIComponent(weekKey)}/pdf`;
}

const reportJobs = new Map();
let queuePollTimer = 0;

async function generateReport() {
  const data = await api(`/api/projects/${state.projectId}/generate`, {
    method: "POST",
    body: JSON.stringify({ force: true }),
  });
  reportJobs.set(data.id, { projectId: state.projectId, status: data.status || "queued" });
  toast("已加入生成队列，完成后自动刷新");
  startQueuePolling();
}

function startQueuePolling() {
  if (queuePollTimer) return;
  queuePollTimer = setInterval(pollTaskQueue, 1500);
}

function stopQueuePolling() {
  if (queuePollTimer) {
    clearInterval(queuePollTimer);
    queuePollTimer = 0;
  }
}

async function pollTaskQueue() {
  let data;
  try {
    data = await api("/api/task-queue");
  } catch {
    // transient network error; the next tick retries
    return;
  }
  const tasks = data.tasks || [];
  for (const [id, job] of Array.from(reportJobs.entries())) {
    const kind = job.kind || "report";
    const task = tasks.find((item) => item.kind === kind && item.id === id);
    if (task) {
      job.status = task.status;
      continue;
    }
    // the job left the active set: it finished, failed, or was skipped
    reportJobs.delete(id);
    if (kind === "template") await templateJobFinished(id, job);
    else await reportJobFinished(id, job);
  }
  renderQueueProgress(data);
  if (!reportJobs.size) stopQueuePolling();
}

async function reportJobFinished(jobId, job) {
  let finished = null;
  try {
    finished = await api(`/api/projects/${job.projectId}/workspace`);
  } catch {
    toast("周报任务已结束");
    return;
  }
  if (job.projectId === state.projectId) updateWorkspace(finished);
  const record = (finished.jobs || []).find((item) => item.id === jobId);
  const name = (finished.project && finished.project.name) || "项目";
  if (!record || record.status === "success") toast(`「${name}」周报生成完成`);
  else if (record.status === "skipped") toast(`「${name}」本轮没有输入变化，已跳过生成`);
  else toast(`「${name}」周报生成失败：${(record && record.failure_reason) || "未知错误"}`);
}

function renderQueueProgress(data) {
  const bubble = $("task-queue-progress");
  if (!bubble) return;
  const tasks = ((data && data.tasks) || []).filter((task) => task.kind === "report" || task.kind === "template");
  if (!tasks.length) {
    bubble.classList.add("hidden");
    return;
  }
  const running = tasks.filter((task) => task.status === "running").length;
  const queued = tasks.length - running;
  const limits = data.parallelism && data.capacity ? `（并行 ${data.parallelism} · 上限 ${data.capacity}）` : "";
  bubble.classList.remove("hidden");
  bubble.innerHTML = `<small>任务队列：${running} 生成中 · ${queued} 排队${limits}</small>${tasks.map((task) =>
    `<span class="queue-task-line">${task.kind === "template" ? "模板 · " : ""}${escapeHtml(statusLabel(task.status))} · ${escapeHtml(task.project_name || "")} ${escapeHtml(task.week_key || "")}</span>`).join("")}`;
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
      workspace._pageSnapPending = undefined;
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
    workspaceElement._pageSnapPending = undefined;
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
  paused: "已停用",
  archived: "已归档",
  resolved: "已解决",
  "on track": "进展顺利",
  "at risk": "有风险",
  "off track": "已偏离",
  done: "已完成",
  unknown: "未知",
  pending: "等待中",
  queued: "排队中",
  running: "生成中",
  succeeded: "已成功",
  failed: "已失败",
  skipped: "已跳过",
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
  if (project.status === "paused" || project.status === "archived") return project.status;
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
    if (el._todoDragActive) { gesture = "idle"; return; }
    if (typeof el._pageSnapPending === "number") {
      // finish a smooth snap that a previous gesture or re-render interrupted
      el.scrollLeft = el._pageSnapPending;
      el._pageSnapPending = undefined;
    }
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
    if (el._todoDragActive) { gesture = "idle"; return; }
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
  let watchdogLast = -1;
  let watchdogRetries = 0;
  const watchSnap = (target, deadline) => {
    if (el._pageSnapPending !== target) return;
    if (Math.abs(el.scrollLeft - target) <= 2) {
      el._pageSnapPending = undefined;
      return;
    }
    if (el.scrollLeft !== watchdogLast && Date.now() < deadline) {
      watchdogLast = el.scrollLeft;
      setTimeout(() => watchSnap(target, deadline), 100);
      return;
    }
    // The smooth snap was canceled or overridden by native momentum (iOS
    // ignores scroll writes mid-momentum); realign once scrolling is idle.
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (watchdogRetries < 2 && Math.abs(el.scrollLeft - target) > 40) {
      watchdogRetries += 1;
      watchdogLast = -1;
      el.scrollTo({ left: target, behavior: reduce ? "auto" : "smooth" });
      setTimeout(() => watchSnap(target, Date.now() + 700), 100);
      return;
    }
    el.scrollLeft = target;
    el._pageSnapPending = undefined;
    watchdogRetries = 0;
  };
  const settle = () => {
    if (el._todoDragActive) return;
    const width = el.clientWidth || 1;
    const dx = lastX - startX;
    const elapsed = Date.now() - startedAt;
    const maxIndex = Math.max(0, Math.round(el.scrollWidth / width) - 1);
    let index = Math.round(el.scrollLeft / width);
    if (gesture === "swipe") {
      const pageIndex = Math.round(startLeft / width);
      index = pageIndex;
      if (Math.abs(dx) >= Math.max(56, width * 0.25) || (Math.abs(dx) >= 28 && elapsed < 220)) {
        index += dx < 0 ? 1 : -1;
      }
    }
    index = Math.min(maxIndex, Math.max(0, index));
    const target = index * width;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el._pageSnapPending = target;
    watchdogRetries = 0;
    watchdogLast = -1;
    el.scrollTo({ left: target, behavior: reduce ? "auto" : "smooth" });
    setTimeout(() => watchSnap(target, Date.now() + 2000), 100);
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
setupTodoBoardDrag();
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
    if (state.tab !== name) state.tab = name;
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
setupAutoSave("voice-settings", $("voice-settings-panel"), saveVoiceSettings);
setupAutoSave("llm-settings", $("llm-settings-panel"), saveLlmSettings);
setupAutoSave("queue-settings", $("queue-settings-panel"), saveQueueSettings);
setupAutoSave("git-settings", $("git-settings-panel"), saveGitSettings);
$("save-password").onclick = () => changeOwnPassword().catch((error) => toast(error.message));
$("login-form").onsubmit = login;
$("logout-button").onclick = logout;
$("cancel-reset-password").onclick = () => $("reset-password-dialog").close();
$("reset-password-form").onsubmit = async (event) => {
  event.preventDefault();
  const id = Number($("reset-password-user-id").value);
  const password = $("reset-password-input").value;
  try {
    await api(`/api/users/${id}`, { method: "PUT", body: JSON.stringify({ password }) });
    $("reset-password-dialog").close();
    toast("密码已重置");
  } catch (error) {
    toast(error.message);
  }
};
$("cancel-user-delete").onclick = () => {
  state.pendingDeleteUserId = null;
  $("user-delete-dialog").close();
};
$("user-delete-dialog").oncancel = () => {
  state.pendingDeleteUserId = null;
};
$("user-delete-form").onsubmit = async (event) => {
  event.preventDefault();
  $("user-delete-dialog").close();
  await runUserDelete();
};
setupVoiceTodoFab();
restoreQueues();
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

function renderVersion(version) {
  if (!version) return;
  const text = `v${version}`;
  for (const id of ["login-version", "sidebar-version"]) {
    const el = $(id);
    if (el) el.textContent = text;
  }
}

(async () => {
  try {
    const authState = await api("/api/auth/state");
    renderVersion(authState.version);
    if (authState.authenticated) {
      hideLoginView();
      await loadState();
    } else {
      showLoginView();
    }
  } catch (err) {
    showLoginView();
    toast(err.message);
  }
})();

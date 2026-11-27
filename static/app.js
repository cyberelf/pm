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
  star: {
    viewBox: "0 0 576 512",
    path: "M316.9 18C311.6 7 300.4 0 288.1 0s-23.4 7-28.8 18L195 150.3 51.4 171.5c-12 1.8-22 10.2-25.7 21.7s-.7 24.2 7.9 32.7L137.8 329 113.2 474.7c-2 12 3 24.2 12.9 31.3s23 8 33.8 2.3l128.3-68.5 128.3 68.5c10.8 5.7 23.9 4.9 33.8-2.3s14.9-19.3 12.9-31.3L438.5 329 542.7 225.9c8.6-8.5 11.7-21.2 7.9-32.7s-13.7-19.9-25.7-21.7L381.2 150.3 316.9 18z",
  },
  starOutline: {
    viewBox: "0 0 576 512",
    path: "M287.9 0c9.2 0 17.6 5.2 21.6 13.5l68.6 141.3 153.2 22.6c9 1.3 16.5 7.6 19.3 16.3s.5 18.1-5.9 24.5L433.6 328.4l26.2 155.6c1.5 9-2.2 18.1-9.6 23.5s-17.3 6-25.3 1.7l-137-73.2L151 509.1c-8 4.3-17.9 3.7-25.3-1.7s-11.2-14.5-9.6-23.5l26.2-155.6L31.1 218.2c-6.5-6.4-8.7-15.9-5.9-24.5s10.3-15 19.3-16.3l153.2-22.6L266.3 13.5C270.4 5.2 278.8 0 287.9 0zm0 79L235.4 184.2c-3.5 7.1-10.2 12.1-18.1 13.3l-116.3 17.2 84.9 81.9c5.9 5.7 8.6 13.9 7.1 21.9L171.4 433l103-55.1c7.1-3.8 15.6-3.8 22.6 0l103 55.1-21.8-114.5c-1.5-8 .9-16.2 7.1-21.9l84.9-81.9-116.3-17.2c-7.9-1.2-14.6-6.2-18.1-13.3L287.9 79z",
  },
};
const state = {
  projects: [],
  projectId: Number(localStorage.getItem("currentProjectId")) || null,
  workspace: null,
  todos: [],
  todoEditorId: null,
  todoClosedExpanded: false,
  pendingReportProjectId: null,
  pendingDeleteTodoId: null,
  pendingDeleteUserId: null,
  mode: localStorage.getItem("workspaceMode") === "todos" ? "todos" : "reports",
  settingsView: false,
  globalSettingsTab: "appearance",
  currentUser: null,
  isAdmin: false,
  asrEndpoint: "",
  asrModel: "whisper",
  asrLanguage: "zh",
  llmProvider: "openai",
  llmBaseUrl: "",
  llmModel: "",
  llmEmbeddingModel: "",
  llmEmbeddingBaseUrl: "",
  llmApiKeySet: false,
  queueCapacity: 5,
  queueParallelism: 2,
  theme: "blue",
  appearance: "light",
  branchOptions: {},
  tab: "overview",
  sourceTab: "manual",
  sourceWorkstreamFilter: "all",
  workstreamId: null,
  workstreamDetail: null,
  workstreamAssign: null,
  workstreamView: readWorkstreamView(),
  workstreamItemEditing: null,
  todoWorkstreamOptions: [],
  workstreamCollapsed: readWorkstreamCollapsed(),
  workstreamMilestoneEditing: null,
  settingsSubTab: "project",
  projectShares: [],
  shareCandidates: [],
  assistantOpen: localStorage.getItem("assistantOpen") === "1",
  assistant: { projectId: null, weekKey: "", hasReport: false, messages: [], loading: false, sending: false, run: null, error: "" },
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
  closeAssistantStream();
  state.assistant = { ...state.assistant, projectId: null, messages: [], run: null, error: "" };
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
  // data-autosave-ignore 的控件（抓取开关、启用开关）自带即时保存，不进
  // 自动保存表单：否则它们的 change 会冒泡触发行级保存，与即时 PUT 竞态互踩
  return Array.from(root.querySelectorAll("input:not([data-autosave-ignore]), textarea, select"))
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
    if (serializeAutoSaveFields(root) === state.snapshot) {
      // 改动完全回退时无需保存；若此前失败提示仍在，一并清除避免误导
      const status = root.querySelector(".autosave-status");
      if (status && status.classList.contains("is-error")) setAutoSaveStatus(root, "idle");
      return;
    }
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
  switchGlobalSettingsTab(state.globalSettingsTab);
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
  state.llmEmbeddingModel = data.llm_embedding_model || "";
  state.llmEmbeddingBaseUrl = data.llm_embedding_base_url || "";
  state.llmVisionModel = data.llm_vision_model || "";
  state.llmVisionBaseUrl = data.llm_vision_base_url || "";
  state.llmApiKeySet = !!data.llm_api_key_set;
  state.queueCapacity = data.queue_capacity || 5;
  state.queueParallelism = data.queue_parallelism || 2;
  state.backupEnabled = !!data.backup_enabled;
  state.backupTargetDir = data.backup_target_dir || "";
  state.backupScheduleType = data.backup_schedule_type === "interval" ? "interval" : "daily";
  state.backupScheduleTime = data.backup_schedule_time || "03:00";
  state.backupIntervalHours = data.backup_interval_hours || 24;
  state.backupKeep = data.backup_keep || 14;
  if (data.ui_theme && THEMES.some((theme) => theme.id === data.ui_theme)) applyTheme(data.ui_theme, false);
  if (data.ui_mode) applyAppearance(data.ui_mode, false);
  renderVoiceSettings();
  renderLlmSettings();
  renderQueueSettings();
  renderBackupSettings();
  renderColdStorageSettings(data);
  renderGitSettings();
  if (state.isAdmin) {
    loadUsers().catch(() => {});
    loadBackupRuns().catch(() => {});
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
  state.todoWorkstreamOptions = data.workstream_options || [];
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
  syncAssistantPanel();
}

function switchGlobalSettingsTab(tab) {
  const buttons = [...document.querySelectorAll("[data-global-settings-tab]")];
  const available = buttons.filter((button) => state.isAdmin || !button.classList.contains("admin-only"));
  const selected = available.find((button) => button.dataset.globalSettingsTab === tab) || available[0];
  if (!selected) return;
  state.globalSettingsTab = selected.dataset.globalSettingsTab;
  buttons.forEach((button) => {
    const active = button === selected;
    button.classList.toggle("hidden", !available.includes(button));
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  });
  document.querySelectorAll("[data-global-settings-panel]").forEach((panel) => {
    panel.classList.toggle("hidden", panel.dataset.globalSettingsPanel !== state.globalSettingsTab);
  });
}

function toggleSettingsView(force) {
  state.settingsView = typeof force === "boolean" ? force : !state.settingsView;
  if (state.settingsView) switchGlobalSettingsTab(state.globalSettingsTab);
  const showingTodos = state.mode === "todos" && !state.settingsView;
  document.body.classList.toggle("todo-mode", showingTodos);
  $("project-sidebar").classList.toggle("hidden", showingTodos);
  syncWorkspaceView();
  updateThemeColorSurface();
}

async function switchAppMode(mode, persist = true, animate = persist) {
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
  $("page-planet").classList.toggle("is-todo", showingTodos);
  $("page-planet").setAttribute("aria-label", `当前页面：${showingTodos ? "TODO" : "周报"}；切换到${showingTodos ? "周报" : "TODO"}`);
  if (animate) playViewEnter();
  if (showingTodos) {
    await loadTodos();
  } else if (state.projectId) {
    await loadWorkspace();
  }
}

function playViewEnter() {
  const entering = document.querySelectorAll(state.mode === "todos" ? "#todo-view" : "#report-view, #project-sidebar");
  entering.forEach((el) => {
    el.classList.remove("view-enter");
    void el.offsetWidth;
    el.classList.add("view-enter");
    setTimeout(() => el.classList.remove("view-enter"), 320);
  });
}

// 左上角星球切换：当前页面旋转着被吸入星球，目标页面再从星球中旋转展开
const PLANET_SWALLOW_MS = 260;
const PLANET_EMIT_MS = 400;
let planetWarping = false;

function aimAtPlanet(el) {
  const planet = $("page-planet").getBoundingClientRect();
  const rect = el.getBoundingClientRect();
  el.style.setProperty("--planet-x", `${planet.left + planet.width / 2 - rect.left}px`);
  el.style.setProperty("--planet-y", `${planet.top + planet.height / 2 - rect.top}px`);
}

async function warpAppMode() {
  if (planetWarping) return;
  const target = state.mode === "todos" ? "reports" : "todos";
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    await switchAppMode(target);
    return;
  }
  planetWarping = true;
  const shell = document.querySelector(".app-shell");
  const planet = $("page-planet");
  planet.classList.add("warping");
  document.body.classList.add("planet-warping");
  aimAtPlanet(shell);
  shell.classList.add("planet-out");
  await new Promise((resolve) => setTimeout(resolve, PLANET_SWALLOW_MS));
  const pending = switchAppMode(target, true, false);
  aimAtPlanet(shell);
  shell.classList.replace("planet-out", "planet-in");
  setTimeout(() => {
    shell.classList.remove("planet-in");
    planet.classList.remove("warping");
    document.body.classList.remove("planet-warping");
    planetWarping = false;
  }, PLANET_EMIT_MS + 40);
  await pending;
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
          ${renderTodoColumnItems(column.status, column.title, items)}
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

// —— 已关闭列折叠：当天完成的保持展示，更早完成的默认隐藏，点击列尾折叠条展开/收起 ——

function renderTodoColumnItems(status, title, items) {
  if (status !== "closed") {
    return `${items.map(renderTodoCard).join("")}${status === "todo" ? renderTodoDraft() : (!items.length ? `<p class="todo-empty">暂无${title}事项</p>` : "")}`;
  }
  if (!items.length) return `<p class="todo-empty">暂无${title}事项</p>`;
  const todayItems = [];
  const olderItems = [];
  for (const todo of items) (isClosedToday(todo) ? todayItems : olderItems).push(todo);
  // 折叠条固定在列尾：滚动不展开，只有点击才动，更早完成的保持折叠
  return `
    ${todayItems.map(renderTodoCard).join("")}
    ${state.todoClosedExpanded ? olderItems.map(renderTodoCard).join("") : ""}
    ${!olderItems.length ? "" : `<button class="todo-fold-bar" type="button" aria-expanded="${state.todoClosedExpanded}" onclick="toggleTodoClosedExpand()">${state.todoClosedExpanded ? "收起更早完成" : `折叠了 ${olderItems.length} 条更早完成`}</button>`}
  `;
}

function chinaDayKey(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: CHINA_TIMEZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

function isClosedToday(todo) {
  if (!todo.closed_at) return true; // 历史数据缺关闭时间，保持可见不折叠
  return chinaDayKey(todo.closed_at) === chinaDayKey(new Date());
}

function toggleTodoClosedExpand() {
  state.todoClosedExpanded = !state.todoClosedExpanded;
  renderTodoBoard();
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
  const starred = !!todo.starred;
  const starLabel = `${starred ? "取消星标" : "星标置顶"}：${escapeAttr(todo.title)}`;
  const star = `
      <button class="todo-card-star${starred ? " starred" : ""}" type="button" title="${starred ? "取消星标" : "星标置顶"}" aria-label="${starLabel}" aria-pressed="${starred}" onclick="event.stopPropagation(); toggleTodoStar(${todo.id})">${faIcon(starred ? "star" : "starOutline")}</button>`;
  return `
    <article class="todo-card ${editable ? "todo-card-editable" : "todo-card-closed"}" data-todo-id="${todo.id}" ondragstart="return false" ${editable ? `onclick="if (!event.target.closest('a, button')) beginTodoEdit(${todo.id})" tabindex="0" onkeydown="if (event.key === 'Enter' && !event.target.closest('a, button')) beginTodoEdit(${todo.id})"` : ""}>${star}
      <h3>${escapeHtml(todo.title)}</h3>
      ${todo.description ? `<div class="todo-markdown">${todo.description_html}</div>` : ""}
      ${todo.status === "closed" ? `
        <div class="todo-close-reason"><span>关闭原因</span><div class="todo-markdown">${todo.close_reason_html}</div></div>
        ${todo.project_name ? `<span class="todo-project">${escapeHtml(todo.project_name)}</span>` : ""}
      ` : ""}
      <div class="todo-card-meta"><span>更新于 ${escapeHtml(formatChinaTime(todo.updated_at))}</span>${todoWorkstreamTag(todo)}</div>
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

async function toggleTodoStar(id) {
  updateTodos(await api(`/api/todos/${id}/star`, { method: "POST" }));
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
    ${state.projects.filter(projectCanUpload).map((project) => `<option value="${project.id}">${escapeHtml(project.name)}</option>`).join("")}
  `;
  const linked = todo.workstreams && todo.workstreams.primary;
  if (linked && state.projects.some((project) => project.id === linked.project_id && projectCanUpload(project))) {
    $("close-todo-project").value = String(linked.project_id);
  }
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
      } else if (task.kind === "template" || task.kind === "workstreams") {
        reportJobs.set(task.id, { projectId: task.project_id, kind: task.kind, status: task.status });
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
  const visionModel = $("llm-vision-model-input");
  if (visionModel) visionModel.value = state.llmVisionModel || "";
  const visionBaseUrl = $("llm-vision-base-url-input");
  if (visionBaseUrl) visionBaseUrl.value = state.llmVisionBaseUrl || "";
  const embeddingModel = $("llm-embedding-model-input");
  if (embeddingModel) embeddingModel.value = state.llmEmbeddingModel || "";
  const embeddingBaseUrl = $("llm-embedding-base-url-input");
  if (embeddingBaseUrl) embeddingBaseUrl.value = state.llmEmbeddingBaseUrl || "";
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
    llm_vision_model: $("llm-vision-model-input")?.value || "",
    llm_vision_base_url: $("llm-vision-base-url-input")?.value || "",
    llm_embedding_model: $("llm-embedding-model-input")?.value || "",
    llm_embedding_base_url: $("llm-embedding-base-url-input")?.value || "",
  };
  const keyInput = $("llm-api-key-input");
  if (keyInput && keyInput.value.trim()) payload.llm_api_key = keyInput.value.trim();
  const data = await api("/api/settings", { method: "PUT", body: JSON.stringify(payload) });
  state.llmProvider = data.llm_provider;
  state.llmBaseUrl = data.llm_base_url;
  state.llmModel = data.llm_model;
  state.llmEmbeddingModel = data.llm_embedding_model || "";
  state.llmVisionModel = data.llm_vision_model || "";
  state.llmVisionBaseUrl = data.llm_vision_base_url || "";
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

function renderBackupSettings() {
  const enabled = $("backup-enabled-input");
  if (!enabled) return;
  enabled.checked = !!state.backupEnabled;
  $("backup-target-dir-input").value = state.backupTargetDir || "";
  const type = $("backup-schedule-type-select");
  type.value = state.backupScheduleType === "interval" ? "interval" : "daily";
  $("backup-schedule-time-input").value = state.backupScheduleTime || "03:00";
  $("backup-interval-hours-input").value = state.backupIntervalHours || 24;
  $("backup-keep-input").value = state.backupKeep || 14;
  syncBackupScheduleFields();
  refreshAutoSaveSnapshot("backup-settings");
}

function syncBackupScheduleFields() {
  const isInterval = $("backup-schedule-type-select")?.value === "interval";
  $("backup-time-field")?.classList.toggle("hidden", isInterval);
  $("backup-interval-field")?.classList.toggle("hidden", !isInterval);
}

async function saveBackupSettings() {
  const time = $("backup-schedule-time-input")?.value || "";
  const intervalHours = Number($("backup-interval-hours-input")?.value);
  const keep = Number($("backup-keep-input")?.value);
  if (!time) throw new Error("请选择备份时间");
  if (!Number.isInteger(intervalHours) || intervalHours < 1 || intervalHours > 168) {
    throw new Error("间隔小时数需为 1-168 的整数");
  }
  if (!Number.isInteger(keep) || keep < 1 || keep > 100) {
    throw new Error("保留份数需为 1-100 的整数");
  }
  const data = await api("/api/settings", {
    method: "PUT",
    body: JSON.stringify({
      backup_enabled: $("backup-enabled-input")?.checked,
      backup_target_dir: $("backup-target-dir-input")?.value.trim(),
      backup_schedule_type: $("backup-schedule-type-select")?.value,
      backup_schedule_time: time,
      backup_interval_hours: intervalHours,
      backup_keep: keep,
    }),
  });
  state.backupEnabled = !!data.backup_enabled;
  state.backupTargetDir = data.backup_target_dir || "";
  state.backupScheduleType = data.backup_schedule_type || "daily";
  state.backupScheduleTime = data.backup_schedule_time || "03:00";
  state.backupIntervalHours = data.backup_interval_hours || 24;
  state.backupKeep = data.backup_keep || 14;
  syncBackupScheduleFields();
}

const BACKUP_TRIGGER_LABELS = { scheduled: "定时", manual: "手动" };

function formatBackupSize(bytes) {
  if (!bytes || bytes <= 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`;
}

async function loadBackupRuns() {
  const data = await api("/api/backup");
  renderBackupRuns(data.runs || []);
}

function renderBackupRuns(runs) {
  const body = $("backup-runs-body");
  if (!body) return;
  body.innerHTML =
    runs
      .map(
        (run) => `<tr><td data-label="时间">${escapeHtml(formatChinaTime(run.started_at))}</td><td data-label="触发">${escapeHtml(BACKUP_TRIGGER_LABELS[run.trigger_type] || run.trigger_type)}</td><td data-label="状态"><span class="status ${run.status === "success" ? "success" : "failed"}">${run.status === "success" ? "成功" : "失败"}</span></td><td data-label="大小">${formatBackupSize(run.size_bytes)}</td><td data-label="说明">${escapeHtml(run.message || "")}</td></tr>`
      )
      .join("") || "<tr><td colspan='5'>暂无备份记录。</td></tr>";
}

async function runBackupNow() {
  const button = $("backup-run-now");
  if (!button || button.disabled) return;
  button.disabled = true;
  button.textContent = "备份中…";
  try {
    const data = await api("/api/backup/run", { method: "POST" });
    const run = data.run || {};
    if (run.status === "success") {
      toast(`备份完成：${run.message || run.backup_path}`);
    } else {
      toast(run.message || "备份失败");
    }
    await loadBackupRuns();
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "立即备份";
  }
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

// —— 项目共享：owner > manage > write > upload > read，前端据此隐藏对应操作入口 ——
// upload 只能上传/编辑资料并设置资料归属工作线；write 另可调整周报、计划与工作线（含 AI 整理）
const SHARE_ROLES = ["read", "upload", "write", "manage"];
const SHARE_ROLE_LABELS = { owner: "所有者", read: "只读", upload: "上传资料", write: "读写", manage: "管理" };
const SHARE_ROLE_RANK = { read: 0, upload: 1, write: 2, manage: 3, owner: 4 };

function roleAtLeast(role, need) {
  return (SHARE_ROLE_RANK[role] ?? -1) >= SHARE_ROLE_RANK[need];
}

function projectRoleOf(p) {
  return p && SHARE_ROLES.includes(p.role) ? p.role : "owner";
}

function projectCanUpload(p) {
  return roleAtLeast(projectRoleOf(p), "upload");
}

function projectCanWrite(p) {
  return roleAtLeast(projectRoleOf(p), "write");
}

function projectCanManage(p) {
  return projectRoleOf(p) === "owner" || projectRoleOf(p) === "manage";
}

function currentProjectRole() {
  if (state.workspace && state.workspace.project && state.workspace.project.id === state.projectId) {
    return SHARE_ROLES.includes(state.workspace.role) ? state.workspace.role : "owner";
  }
  return projectRoleOf(state.projects.find((item) => item.id === state.projectId));
}

function canUploadWorkspace() {
  return roleAtLeast(currentProjectRole(), "upload");
}

function canWriteWorkspace() {
  return roleAtLeast(currentProjectRole(), "write");
}

function canManageWorkspace() {
  return projectCanManage({ role: currentProjectRole() });
}

function isProjectOwner() {
  return currentProjectRole() === "owner";
}

function projectRowHtml(p) {
  const paused = projectPaused(p);
  const shared = projectRoleOf(p) !== "owner";
  return `
    <div class="project-row${p.id === state.projectId ? " active" : ""}${paused ? " paused" : ""}">
      <button class="project-item" data-project="${p.id}" aria-label="${escapeAttr(`${p.name}，${projectDisplayStatus(p)}`)}">
        ${statusDot(projectDisplayStatus(p), "project-item-status")}
        <strong>${escapeHtml(p.name)}</strong>
        ${paused ? '<small class="project-item-flag">已停用</small>' : ""}
        ${shared ? `<small class="project-item-flag">共享 · ${SHARE_ROLE_LABELS[projectRoleOf(p)]}</small>` : ""}
      </button>
      ${projectCanWrite(p) ? `
      <button class="project-generate" data-project-generate="${p.id}" aria-label="为 ${escapeAttr(p.name)} 生成周报" title="生成周报">
        ${faIcon("report")}
      </button>` : ""}
      ${projectCanManage(p) ? `
      <button class="project-settings ${p.id === state.projectId && state.tab === "settings" ? "active" : ""}" data-project-settings="${p.id}" aria-label="打开 ${escapeAttr(p.name)} 的设置" title="项目设置">
        ${faIcon("gear")}
      </button>` : ""}
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
  const wsRole = SHARE_ROLES.includes(ws.role) ? ws.role : "owner";
  $("project-meta").textContent = wsRole === "owner"
    ? ws.week_key
    : `${ws.week_key} · ${ws.project.owner} 共享 · ${SHARE_ROLE_LABELS[wsRole]}权限`;
  renderProjects();
  renderOverview(ws);
  renderWorkstreams(ws);
  renderPlan(ws);
  renderSettings(ws);
  renderMemberDatalist(ws);
  renderUpdates(ws);
  renderSources(ws);
  renderReport(ws);
  ensureTableScrollContainers();
  switchTab(state.tab);
  syncAssistantPanel();
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
    ${renderOverviewWorkstreams(ws)}
  `;
}

// ---------------------------------------------------------------- 工作线

function readWorkstreamView() {
  try {
    return localStorage.getItem("workstreamView") === "matrix" ? "matrix" : "progress";
  } catch {
    return "progress";
  }
}

function setWorkstreamView(view) {
  state.workstreamView = view === "matrix" ? "matrix" : "progress";
  try {
    localStorage.setItem("workstreamView", state.workstreamView);
  } catch {
    // per-viewer convenience only
  }
  renderWorkstreams(state.workspace);
}

function readWorkstreamCollapsed() {
  try {
    const ids = JSON.parse(localStorage.getItem("workstreamCollapsed") || "[]");
    return new Set(Array.isArray(ids) ? ids.map(Number) : []);
  } catch {
    return new Set();
  }
}

function toggleWorkstreamCollapse(event, id) {
  event.stopPropagation();
  const collapsed = state.workstreamCollapsed;
  if (collapsed.has(id)) collapsed.delete(id);
  else collapsed.add(id);
  try {
    localStorage.setItem("workstreamCollapsed", JSON.stringify([...collapsed]));
  } catch {
    // per-viewer convenience only
  }
  renderWorkstreams(state.workspace);
}

// children of a collapsed parent are hidden; the parent's health already rolls them up
function wsVisible(items) {
  return items.filter((item) => !item.parent_id || !state.workstreamCollapsed.has(item.parent_id));
}

// reserve: some line has children, so top-level lines keep the fold column aligned
function wsNameLine(item, reserve = false) {
  const kids = (item.children || []).length;
  const collapsed = state.workstreamCollapsed.has(item.id);
  const fold = kids
    ? `<button type="button" class="ws-fold" aria-expanded="${!collapsed}" aria-label="${collapsed ? "展开" : "收起"} ${kids} 条子工作线" onclick="toggleWorkstreamCollapse(event, ${item.id})" onkeydown="event.stopPropagation()"><span class="ws-chevron${collapsed ? " is-collapsed" : ""}"></span></button>`
    : "";
  const more = kids && collapsed ? `<small class="ws-kids">+${kids}</small>` : "";
  const lead = fold || (item.parent_id ? `<span class="ws-branch" aria-hidden="true">└</span>` : reserve ? `<span class="ws-fold-space" aria-hidden="true"></span>` : "");
  return `<span class="ws-name-line">${lead}${wsHealthDot(item.health)}<strong>${escapeHtml(item.name)}</strong>${more}</span>`;
}

function wsRowClass(item) {
  return `${item.parent_id ? " is-child" : ""}${(item.children || []).length ? " is-parent" : ""}`;
}

function wsDay(value) {
  const [y, m, d] = String(value || "").split("-").map(Number);
  return y ? Date.UTC(y, m - 1, d) / 86400000 : null;
}

function wsItemsSide(item) {
  const total = (item.items_open || 0) + (item.items_done || 0);
  if (!total) return `<span class="ws-progress-none">—</span>`;
  const pct = Math.round(((item.items_done || 0) / total) * 100);
  return `
    <span class="ws-items-bar" role="img" aria-label="待跟踪项完成 ${item.items_done}/${total}"><span style="width:${pct}%"></span></span>
    <small>${item.items_open} 待跟踪${item.items_overdue ? ` · <b class="is-overdue">${item.items_overdue} 逾期</b>` : ""}</small>`;
}

function renderWorkstreamProgress(data, items) {
  const timeline = data.timeline || [];
  if (!timeline.length) return "";
  const start = wsDay(timeline[0].start);
  const span = timeline.length * 7;
  const pos = (value) => {
    const day = wsDay(value);
    if (day === null) return null;
    const pct = ((day - start) / span) * 100;
    return pct < 0 || pct > 100 ? null : pct;
  };
  const today = data.today;
  const todayPos = pos(today);
  const todayLine = todayPos === null ? "" : `<span class="ws-today" style="left:${todayPos.toFixed(2)}%" aria-hidden="true"></span>`;
  const labelEvery = timeline.length > 16 ? 2 : 1;
  const scale = timeline.map((week, index) => {
    const current = week.week_key === data.current_week;
    const show = current || index % labelEvery === 0;
    return `<span class="ws-scale-week${current ? " is-current" : ""}" title="${escapeAttr(`${week.week_key}（${week.start} 起）`)}">${show ? escapeHtml(wsShortWeek(week.week_key)) : ""}</span>`;
  }).join("");
  const reserve = items.some((item) => (item.children || []).length);
  const rows = wsVisible(items).map((item) => {
    const cells = Object.fromEntries((item.cells || []).map((cell) => [cell.week_key, cell]));
    const segments = timeline.map((week) => {
      const cell = cells[week.week_key];
      if (!cell) {
        const future = week.week_key > data.current_week;
        return `<span class="ws-seg ${future ? "is-future" : "is-empty"}"></span>`;
      }
      const snap = cell.snapshot;
      const active = cell.materials || cell.git;
      const status = snap ? snap.status : active ? "pending" : "empty";
      const label = snap ? (WS_SNAPSHOT_LABELS[snap.status] || snap.status) : active ? "有资料、尚无快照" : "无记录";
      const title = `${week.week_key} · ${label}${snap ? `：${snap.summary}` : ""}${cell.materials ? `\n${cell.materials} 份关联资料` : ""}${cell.git ? `\n${cell.git} 条 PR/Issue` : ""}`;
      return `<span class="ws-seg is-${status}${week.week_key === data.current_week ? " is-current" : ""}" title="${escapeAttr(title)}"></span>`;
    }).join("");
    const markers = [];
    (item.milestones || []).forEach((m) => {
      const at = pos(m.target_date);
      if (at === null) return;
      const done = m.status === "complete";
      const late = !done && m.target_date < today;
      markers.push(`<span class="ws-marker ws-milestone${done ? " is-done" : late ? " is-late" : ""}" style="left:${at.toFixed(2)}%" title="${escapeAttr(`里程碑：${m.title || ""}（${m.target_date}${done ? "，已完成" : late ? "，已逾期" : ""}）`)}"></span>`);
    });
    const target = pos(item.target_date);
    if (target !== null) {
      markers.push(`<span class="ws-marker ws-target${item.target_date < today && item.status === "active" ? " is-late" : ""}" style="left:${target.toFixed(2)}%" title="${escapeAttr(`目标日期 ${item.target_date}`)}"></span>`);
    }
    const meta = [item.owner_label, item.status !== "active" ? WS_STATUS_LABELS[item.status] : "", item.target_date ? `截止 ${item.target_date}` : ""]
      .filter(Boolean).map(escapeHtml).join(" · ");
    return `
      <div class="ws-progress-row${wsRowClass(item)}${state.workstreamId === item.id ? " is-selected" : ""}${item.status !== "active" ? " is-inactive" : ""}" data-workstream-id="${item.id}" tabindex="0" role="button"
           onclick="selectWorkstream(${item.id})" onkeydown="if (event.key === 'Enter') selectWorkstream(${item.id})">
        <div class="ws-progress-name">
          ${wsNameLine(item, reserve)}
          <small>${meta || `${item.material_total} 份资料`}</small>
        </div>
        <div class="ws-progress-track">${segments}${markers.join("")}${todayLine}</div>
        <div class="ws-progress-side">${wsItemsSide(item)}</div>
      </div>`;
  }).join("");
  return `
    <div class="ws-progress" style="--ws-weeks:${timeline.length}">
      <div class="ws-progress-inner">
        <div class="ws-progress-row ws-progress-head">
          <div class="ws-progress-name">工作线</div>
          <div class="ws-progress-track ws-progress-scale">${scale}${todayLine}</div>
          <div class="ws-progress-side">待跟踪项</div>
        </div>
        ${rows}
      </div>
    </div>`;
}

function renderWorkstreamSummary(data, items) {
  const active = items.filter((item) => item.status === "active");
  // every line counts once by its own health, so a parent does not repeat its children
  const count = (health) => active.filter((item) => (item.own_health || item.health) === health).length;
  const advanced = active.filter((item) => {
    const cell = (item.cells || []).find((c) => c.week_key === data.current_week);
    return cell && cell.snapshot && cell.snapshot.status === "advanced";
  }).length;
  const open = items.reduce((sum, item) => sum + (item.items_open || 0), 0);
  const overdue = items.reduce((sum, item) => sum + (item.items_overdue || 0), 0);
  const risks = (state.workspace?.risks || []).filter((risk) => risk.status === "active").length;
  const stat = (value, label, tone = "") => `<div class="ws-stat${tone ? ` ${tone}` : ""}"><strong>${value}</strong><span>${label}</span></div>`;
  return `
    <div class="ws-summary">
      ${stat(count("on track"), "进展顺利")}
      ${stat(count("at risk"), "有风险", count("at risk") ? "is-warning" : "")}
      ${stat(count("blocked"), "受阻", count("blocked") ? "is-error" : "")}
      ${stat(`${advanced}/${active.length}`, "本周有进展")}
      ${stat(open, overdue ? `待跟踪 · ${overdue} 逾期` : "待跟踪", overdue ? "is-error" : "")}
      ${stat(risks, "风险提醒", risks ? "is-warning" : "")}
    </div>`;
}

const WS_SNAPSHOT_LABELS = { advanced: "有进展", steady: "无明显进展", blocked: "受阻" };
const WS_STATUS_LABELS = { active: "进行中", paused: "暂停", done: "已完成" };
const WS_HEALTH_LABELS = { "on track": "进展顺利", "at risk": "有风险", blocked: "受阻", paused: "暂停", complete: "已完成" };

function workstreamList() {
  return state.workspace?.workstreams?.workstreams || [];
}

function workstreamById(id) {
  return workstreamList().find((item) => item.id === Number(id)) || null;
}

function wsShortWeek(key) {
  return String(key || "").replace(/^\d{4}-/, "");
}

function wsSnapshotTone(status) {
  if (status === "advanced") return "is-success";
  if (status === "blocked") return "is-error";
  return "is-neutral";
}

function wsHealthDot(health) {
  return statusDot(WS_HEALTH_LABELS[health] || health, "", statusTone(health));
}

function wsCell(cell, currentWeek) {
  const snap = cell.snapshot;
  const current = cell.week_key === currentWeek ? " is-current" : "";
  const weekAttr = `data-label="${escapeAttr(wsShortWeek(cell.week_key))}"`;
  if (snap) {
    const label = WS_SNAPSHOT_LABELS[snap.status] || snap.status;
    const title = `${cell.week_key} · ${label}：${snap.summary}${snap.next_step ? `\n下一步：${snap.next_step}` : ""}`;
    return `<td class="ws-cell is-${escapeAttr(snap.status)}${current}" ${weekAttr} title="${escapeAttr(title)}"><span class="ws-cell-line"><span class="status-dot ${wsSnapshotTone(snap.status)}" aria-label="${escapeAttr(label)}"></span><span class="ws-cell-text">${escapeHtml(snap.summary)}</span></span></td>`;
  }
  if (cell.materials || cell.git) {
    const parts = [cell.materials ? `${cell.materials} 份资料` : "", cell.git ? `${cell.git} 条 PR/Issue` : ""].filter(Boolean).join(" · ");
    return `<td class="ws-cell is-pending${current}" ${weekAttr} title="${escapeAttr(`${cell.week_key} · ${parts}，尚无快照`)}"><span class="ws-cell-text">${parts}</span></td>`;
  }
  return `<td class="ws-cell is-empty${current}" ${weekAttr}><span aria-label="无记录">—</span></td>`;
}

// board, detail and risks render into their own slots so one re-render never resets the others
function workstreamLayout() {
  const root = $("tab-workstreams");
  if (!root) return false;
  if (!$("ws-board")) {
    root.innerHTML = `<div id="ws-board"></div><div id="workstream-detail"></div><div id="ws-risks"></div>`;
  }
  return true;
}

function renderWorkstreams(ws) {
  if (!workstreamLayout()) return;
  const board = $("ws-board");
  if (state.workstreamDetail && state.workstreamDetail.projectId !== ws.project.id) {
    state.workstreamId = null;
    state.workstreamDetail = null;
  }
  const data = ws.workstreams || { workstreams: [], weeks: [], unassigned_materials: 0 };
  const items = data.workstreams || [];
  const writable = canWriteWorkspace();
  const job = ws.workstream_job;
  const organizing = !!(job && ["queued", "running"].includes(job.status));
  const hasActive = items.some((item) => item.status === "active");
  const note = job && job.status === "success" && job.output_md
    ? `<span class="workstream-job-note">上次整理：${escapeHtml(job.output_md)} · ${escapeHtml(formatChinaTime(job.completed_at))}</span>`
    : job && job.status === "failed"
      ? `<span class="workstream-job-note is-error">上次整理失败：${escapeHtml(job.failure_reason || "")}</span>`
      : "";
  const toolbar = writable ? `
    <div class="row workstream-toolbar">
      <button class="primary" type="button" onclick="openWorkstreamDialog()">＋ 新建工作线</button>
      <button type="button" onclick="seedWorkstreams()" title="把「项目计划」页签中项目目标的编号行各生成一条工作线，缩进行或 1.1 编号生成子工作线；已有同名工作线跳过">按项目目标生成</button>
      <button type="button" id="workstream-organize-btn" onclick="organizeWorkstreams()" ${hasActive && !organizing ? "" : "disabled"} title="${data.organized_at ? "同步本周 PR/Issue，AI 归类本周未归类资料和 PR/Issue，更新本周快照和待跟踪项；过去的周已锁定" : "首次整理：同步本周 PR/Issue，AI 归类全部未归类资料、用历史周报补齐近 8 周快照，并整理本周"}">${organizing ? "整理中…" : "AI 整理"}</button>
      ${note}
    </div>` : "";
  if (!items.length) {
    board.innerHTML = `
      <div class="panel">
        <div class="panel-head"><h2>工作线</h2><span>项目内并行的长线任务</span></div>
        ${toolbar}
        <p class="workstream-empty">还没有工作线。${writable ? "可以新建，或在「项目计划」页签写好编号的项目目标后“按项目目标生成”。" : ""}</p>
      </div>`;
    renderWorkstreamDetail();
    renderWorkstreamRisks(ws);
    return;
  }
  const head = (data.weeks || []).map((week) =>
    `<th class="ws-week${week === data.current_week ? " is-current" : ""}" scope="col" title="${escapeAttr(week)}">${escapeHtml(wsShortWeek(week))}</th>`).join("");
  const reserve = items.some((item) => (item.children || []).length);
  const rows = wsVisible(items).map((item) => {
    const meta = [item.owner_label, item.status !== "active" ? WS_STATUS_LABELS[item.status] : "", item.target_date ? `截止 ${item.target_date}` : ""]
      .filter(Boolean).map(escapeHtml).join(" · ");
    return `
      <tr class="ws-row${wsRowClass(item)}${state.workstreamId === item.id ? " is-selected" : ""}" data-workstream-id="${item.id}" tabindex="0"
          onclick="selectWorkstream(${item.id})" onkeydown="if (event.key === 'Enter') selectWorkstream(${item.id})">
        <th scope="row" class="ws-name">
          ${wsNameLine(item, reserve)}
          <small>${meta || `${item.material_total} 份资料`}</small>
        </th>
        ${(item.cells || []).map((cell) => wsCell(cell, data.current_week)).join("")}
      </tr>`;
  }).join("");
  const progress = state.workstreamView !== "matrix";
  const viewSwitch = `
    <div class="source-tabs ws-view-switch" role="tablist" aria-label="工作线视图">
      <button type="button" role="tab" class="${progress ? "active" : ""}" aria-selected="${progress}" onclick="setWorkstreamView('progress')">进展</button>
      <button type="button" role="tab" class="${progress ? "" : "active"}" aria-selected="${!progress}" onclick="setWorkstreamView('matrix')">周矩阵</button>
    </div>`;
  const body = progress
    ? renderWorkstreamProgress(data, items)
    : `<table class="table ws-matrix">
        <thead><tr><th scope="col" class="ws-name">工作线</th>${head}</tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  const legend = progress
    ? `<span class="workstream-legend"><span class="ws-seg-key is-advanced"></span>有进展<span class="ws-seg-key is-steady"></span>无明显进展<span class="ws-seg-key is-blocked"></span>受阻<span class="ws-seg-key is-pending"></span>有资料未整理<span class="ws-key-milestone"></span>里程碑<span class="ws-key-target"></span>目标日期<span class="ws-key-today"></span>今天</span>`
    : `<span class="workstream-legend"><span class="status-dot is-success"></span>有进展<span class="status-dot is-neutral"></span>无明显进展<span class="status-dot is-error"></span>受阻</span>`;
  board.innerHTML = `
    <div class="panel">
      <div class="panel-head"><h2>工作线</h2><span>${progress ? "过去 8 周进展与后续节点" : `近 ${(data.weeks || []).length} 周`} · 点击一行查看详情</span></div>
      ${toolbar}
      <div class="row ws-view-row">${viewSwitch}</div>
      ${renderWorkstreamSummary(data, items)}
      ${body}
      <div class="row workstream-footer">
        <button type="button" onclick="showWorkstreamMaterials('none')">未归类资料 ${data.unassigned_materials}</button>
        ${legend}
      </div>
      ${renderUnassignedGit(data, writable)}
    </div>`;
  ensureTableScrollContainers();
  renderWorkstreamDetail();
  renderWorkstreamRisks(ws);
}

const RISK_RULE_LABELS = {
  missing_update: "缺少本周更新",
  overdue_milestone: "项目里程碑逾期",
  workstream_overdue: "工作线逾期",
  workstream_stale: "工作线停滞",
  workstream_item_overdue: "待跟踪项逾期",
};

function riskWorkstreamId(risk) {
  const match = /^workstream:(\d+)$/.exec(String(risk.source_ref || ""));
  return match ? Number(match[1]) : null;
}

function renderWorkstreamRisks(ws) {
  const el = $("ws-risks");
  if (!el) return;
  const risks = ws.risks || [];
  const active = risks.filter((risk) => risk.status === "active").length;
  const rows = risks.map((risk) => {
    const id = riskWorkstreamId(risk);
    const title = id && workstreamById(id)
      ? `<button type="button" class="link-button" onclick="focusWorkstream(${id})">${escapeHtml(risk.title)}</button>`
      : escapeHtml(risk.title);
    return `<tr class="${risk.status === "active" ? "" : "is-resolved"}">
      <td data-label="严重度"><span class="status ${risk.severity}">${escapeHtml(statusLabel(risk.severity))}</span></td>
      <td data-label="规则">${escapeHtml(RISK_RULE_LABELS[risk.rule] || risk.rule)}</td>
      <td data-label="内容">${title}${risk.details ? `<br><small>${escapeHtml(risk.details)}</small>` : ""}</td>
      <td data-label="状态">${escapeHtml(statusLabel(risk.status))}</td>
    </tr>`;
  }).join("");
  el.innerHTML = `
    <div class="panel ws-risks">
      <div class="panel-head"><h2>风险提醒</h2><span>确定性规则 · 本周 ${active} 条活跃 · 项目进度 <span class="status ${String(ws.progress_status || "").replace(" ", "-")}">${escapeHtml(statusLabel(ws.progress_status))}</span></span></div>
      <table class="table"><thead><tr><th>严重度</th><th>规则</th><th>内容</th><th>状态</th></tr></thead><tbody>${rows || "<tr><td colspan='4'>暂无风险。</td></tr>"}</tbody></table>
    </div>`;
  ensureTableScrollContainers();
}

async function focusWorkstream(id) {
  if (state.workstreamId !== id) await selectWorkstream(id);
  $("workstream-detail")?.scrollIntoView?.({ behavior: "smooth", block: "start" });
}

async function selectWorkstream(id) {
  if (state.workstreamId === id) {
    state.workstreamId = null;
    state.workstreamDetail = null;
    renderWorkstreams(state.workspace);
    return;
  }
  state.workstreamId = id;
  document.querySelectorAll(".ws-row, .ws-progress-row[data-workstream-id]").forEach((row) => row.classList.toggle("is-selected", Number(row.dataset.workstreamId) === id));
  await loadWorkstreamDetail(id);
}

async function loadWorkstreamDetail(id) {
  const projectId = state.projectId;
  const detail = await api(`/api/projects/${projectId}/workstreams/${id}`);
  if (state.projectId !== projectId || state.workstreamId !== id) return;
  state.workstreamDetail = { ...detail, projectId };
  renderWorkstreamDetail();
}

function renderWorkstreamDetail() {
  const el = $("workstream-detail");
  if (!el) return;
  const d = state.workstreamDetail;
  if (!d || d.id !== state.workstreamId) {
    el.innerHTML = "";
    return;
  }
  const writable = canWriteWorkspace();
  const currentWeek = d.current_week || state.workspace?.workstreams?.current_week || "";
  const order = wsSiblings(d.id);
  const index = order.indexOf(d.id);
  const meta = [WS_HEALTH_LABELS[d.health] || d.health, d.owner_label, d.target_date ? `截止 ${d.target_date}` : ""]
    .filter(Boolean).map(escapeHtml).join(" · ");
  const parentLink = d.parent
    ? `<span class="ws-parent-link">上级工作线 <button type="button" class="link-button" onclick="selectWorkstream(${d.parent.id})">${escapeHtml(d.parent.name)}</button></span>`
    : "";
  const alerts = [...(d.overdue_reasons || []), ...(d.child_alerts || [])];
  const timeline = (d.snapshots || []).map((snap) => `
    <li>
      <span class="ws-timeline-week">${escapeHtml(snap.week_key)}</span>
      <span class="status ${snap.status === "advanced" ? "success" : snap.status === "blocked" ? "blocked" : ""}">${escapeHtml(WS_SNAPSHOT_LABELS[snap.status] || snap.status)}</span>
      <div class="ws-timeline-body">
        <p>${escapeHtml(snap.summary)}</p>
        ${snap.next_step ? `<small>下一步：${escapeHtml(snap.next_step)}</small>` : ""}
      </div>
    </li>`).join("") || "<li class=\"workstream-empty\">还没有周快照。生成周报或运行 AI 整理后出现。</li>";
  const snapshotForm = writable ? `
    <div class="workstream-snapshot-form">
      <span class="ws-snap-week">本周 ${escapeHtml(wsShortWeek(currentWeek))}</span>
      <select id="ws-snap-status" aria-label="状态">${Object.entries(WS_SNAPSHOT_LABELS).map(([value, label]) => `<option value="${value}">${label}</option>`).join("")}</select>
      <input id="ws-snap-summary" maxlength="300" placeholder="本周进展（一句话）">
      <input id="ws-snap-next" maxlength="300" placeholder="下一步（可选）">
      <button type="button" onclick="saveWorkstreamSnapshot(${d.id})">记录</button>
    </div>` : "";
  const todos = (d.todos || []).map((t) => `<li><span class="status ${t.status === "doing" ? "running" : ""}">${t.status === "doing" ? "进行中" : "待办"}</span> ${escapeHtml(t.title)}</li>`).join("");
  el.innerHTML = `
    <div class="panel workstream-detail">
      <div class="panel-head"><h2>${escapeHtml(d.name)}</h2><span>${meta}${parentLink ? ` · ${parentLink}` : ""}</span></div>
      ${d.goal ? `<p class="workstream-goal">${escapeHtml(d.goal)}</p>` : ""}
      ${alerts.length ? `<p class="workstream-alert">${escapeHtml(alerts.join("；"))}</p>` : ""}
      <div class="row">
        ${writable ? `
          <button type="button" onclick="openWorkstreamDialog(${d.id})">编辑</button>
          <button type="button" onclick="moveWorkstream(${d.id}, -1)" ${index <= 0 ? "disabled" : ""}>上移</button>
          <button type="button" onclick="moveWorkstream(${d.id}, 1)" ${index < 0 || index >= order.length - 1 ? "disabled" : ""}>下移</button>
          ${d.parent ? "" : `<button type="button" onclick="openWorkstreamDialog(null, ${d.id})">＋ 子工作线</button>`}` : ""}
        <button type="button" onclick="showWorkstreamMaterials(${d.id})">在过程资料中查看</button>
        ${writable ? `<button type="button" class="danger" onclick="deleteWorkstream(${d.id})">删除</button>` : ""}
      </div>
      <div class="grid-2 workstream-detail-grid">
        <section>
          ${renderWorkstreamItems(d, writable)}
          <h3>周进展 <small>过去的周已锁定</small></h3>
          ${snapshotForm}
          <ol class="workstream-timeline">${timeline}</ol>
        </section>
        <section>
          ${renderWorkstreamChildren(d, writable)}
          ${renderWorkstreamMilestones(d, writable)}
          ${renderWorkstreamEvidence(d, writable)}
          <h3>我的 TODO</h3>
          ${todos ? `<ul class="workstream-list">${todos}</ul>` : `<p class="workstream-empty">暂无关联的未关闭 TODO。</p>`}
        </section>
      </div>
    </div>`;
  ensureTableScrollContainers();
}

// 关联资料与 PR / Issue as icon chips: the shape is the type, the color the
// status; hovering (or tapping on touch screens) shows the details card
const GIT_STATE_LABELS = { merged: "已合并", open: "进行中", closed: "已关闭", draft: "草稿" };
const GIT_LINK_LABELS = { repo: "仓库默认归属", auto: "AI 归类", manual: "手动归属" };
const WS_CHIP_ICONS = {
  file: `<path d="M4 1.75h5.25L12.5 5v9.25H4z"/><path d="M9.25 1.75V5h3.25"/>`,
  note: `<rect x="2.5" y="2.5" width="11" height="11" rx="2"/><path d="M5.25 6h5.5M5.25 8.5h5.5M5.25 11h3"/>`,
  pr: `<circle cx="4.25" cy="3.75" r="1.75"/><circle cx="4.25" cy="12.25" r="1.75"/><circle cx="11.75" cy="12.25" r="1.75"/><path d="M4.25 5.5v5M11.75 10.5V7a2 2 0 0 0-2-2H7.5"/><path d="M9 3.5 7.5 5 9 6.5"/>`,
  issue: `<circle cx="8" cy="8" r="6"/><circle cx="8" cy="8" r="1.5" fill="currentColor" stroke="none"/>`,
};

function wsChipIcon(shape) {
  return `<svg class="ws-chip-icon" viewBox="0 0 16 16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${WS_CHIP_ICONS[shape]}</svg>`;
}

function wsChip({ shape, tone, label, head, title, meta, body = "", actions = "", primary = "" }) {
  return `
    <span class="ws-chip-wrap" onmouseenter="wsPopPlace(this)" onfocusin="wsPopPlace(this)">
      <button type="button" class="ws-chip is-${shape} is-${tone}" aria-label="${escapeAttr(label)}" onclick="wsChipClick(event, this)" data-primary="${escapeAttr(primary)}">${wsChipIcon(shape)}</button>
      <span class="ws-pop">
        <span class="ws-pop-head">${head}</span>
        <span class="ws-pop-title">${escapeHtml(title)}</span>
        ${meta ? `<span class="ws-pop-meta">${meta}</span>` : ""}
        ${body ? `<span class="ws-pop-body">${escapeHtml(body)}</span>` : ""}
        ${actions ? `<span class="ws-pop-actions">${actions}</span>` : ""}
      </span>
    </span>`;
}

function gitChip(g, writable, assignLabel = "改归属") {
  const tone = g.state === "merged" ? "success" : g.state === "open" ? "active" : g.state === "draft" ? "draft" : "muted";
  const kind = g.kind === "pr" ? "PR" : "Issue";
  const state = GIT_STATE_LABELS[g.state] || g.state || "";
  const ref = `${g.repo.split("/").pop()}#${g.number}`;
  return wsChip({
    shape: g.kind === "pr" ? "pr" : "issue",
    tone,
    label: `${kind} ${ref} ${state}：${g.title}`,
    head: `<b>${kind} · ${escapeHtml(state)}</b><small>${escapeHtml(g.repo)}#${g.number}</small>`,
    title: g.title,
    meta: [g.author, g.week_key, GIT_LINK_LABELS[g.link_source] || ""].filter(Boolean).map(escapeHtml).join(" · "),
    primary: g.url ? `git:${g.url}` : "",
    actions: `${g.url ? `<a class="link-button" href="${escapeAttr(g.url)}" target="_blank" rel="noopener">打开 ↗</a>` : ""}${writable ? `<button type="button" class="link-button" onclick="openWorkstreamAssign('git', ${g.id})">${assignLabel}</button>` : ""}`,
  });
}

function materialChip(m, currentWeek, writable) {
  const failed = m.extraction_status === "failed";
  const fresh = m.week_key && m.week_key === currentWeek;
  const tone = failed ? "error" : fresh ? "active" : "muted";
  const type = m.source_type === "manual" ? "手工资料" : "文件";
  const state = failed ? "提取失败" : fresh ? "本周新增" : "往期";
  return wsChip({
    shape: m.source_type === "manual" ? "note" : "file",
    tone,
    label: `${type} ${state}：${m.filename}`,
    head: `<b>${type} · ${state}</b><small>${escapeHtml(formatChinaTime(m.created_at))}</small>`,
    title: m.filename,
    meta: [m.is_primary ? "主归属" : "关联", m.link_source === "auto" ? "AI 归类" : "手动归属"].map(escapeHtml).join(" · "),
    body: (m.summary || "").slice(0, 160),
    primary: `material:${m.id}`,
    actions: `<button type="button" class="link-button" onclick="previewMaterial(${m.id})">预览</button>${canUploadWorkspace() ? `<button type="button" class="link-button" onclick="openWorkstreamAssign('material', ${m.id})">改归属</button>` : ""}`,
  });
}

const WS_CHIP_LIMIT = 60;

function renderWorkstreamEvidence(d, writable) {
  const git = d.git_items || [];
  const materials = d.materials || [];
  state.workstreamGitItems = Object.fromEntries(git.map((g) => [g.id, g]));
  const currentWeek = d.current_week || "";
  const time = (value) => Date.parse(value || "") || 0;
  const entries = [
    ...git.map((g) => ({ at: time(g.updated_at), html: () => gitChip(g, writable) })),
    ...materials.map((m) => ({ at: time(m.created_at), html: () => materialChip(m, currentWeek, writable) })),
  ].sort((a, b) => b.at - a.at);
  const counts = [materials.length ? `${materials.length} 份资料` : "", git.length ? `${git.length} 条 PR/Issue` : ""].filter(Boolean).join(" · ");
  if (!entries.length) return `<h3>关联资料</h3><p class="workstream-empty">暂无关联资料或 PR/Issue。</p>`;
  const more = entries.length > WS_CHIP_LIMIT
    ? `<button type="button" class="ws-chip-more" onclick="showWorkstreamMaterials(${d.id})">+${entries.length - WS_CHIP_LIMIT}</button>` : "";
  return `
    <h3>关联资料 <small>${counts}</small></h3>
    <div class="ws-chips">${entries.slice(0, WS_CHIP_LIMIT).map((entry) => entry.html()).join("")}${more}</div>
    ${wsChipLegend()}`;
}

function wsChipLegend() {
  const key = (shape, label) => `<span class="ws-legend-key">${wsChipIcon(shape)}${label}</span>`;
  const dot = (tone, label) => `<span class="ws-legend-key"><span class="ws-legend-dot is-${tone}"></span>${label}</span>`;
  return `<div class="ws-chip-legend">${key("file", "文件")}${key("note", "手工")}${key("pr", "PR")}${key("issue", "Issue")}
    <span class="ws-legend-sep"></span>${dot("active", "本周 / 进行中")}${dot("success", "已合并")}${dot("muted", "往期 / 已关闭")}${dot("error", "提取失败")}</div>`;
}

function renderUnassignedGit(data, writable) {
  const items = data.unassigned_git || [];
  if (!items.length) return "";
  state.workstreamUnassignedGit = Object.fromEntries(items.map((g) => [g.id, g]));
  return `
    <div class="ws-git-unassigned">
      <span>本周未归类 PR/Issue ${items.length}</span>
      <div class="ws-chips">${items.map((g) => gitChip(g, writable, "归到工作线")).join("")}</div>
    </div>`;
}

// a tap outside closes a card opened by touch
document.addEventListener("click", (event) => {
  if (event.target?.closest?.(".ws-chip-wrap")) return;
  document.querySelectorAll(".ws-chip-wrap.is-open").forEach((item) => item.classList.remove("is-open"));
});

// keep the card inside the viewport: clamp it horizontally, open below near the top
function wsPopPlace(wrap) {
  const pop = wrap.querySelector(".ws-pop");
  if (!pop) return;
  const rect = wrap.getBoundingClientRect();
  const gutter = 16;
  const width = Math.min(280, window.innerWidth - gutter * 2);
  let shift = 0;
  if (rect.left + width > window.innerWidth - gutter) shift = window.innerWidth - gutter - width - rect.left;
  if (rect.left + shift < gutter) shift = gutter - rect.left;
  pop.style.width = `${width}px`;
  pop.style.left = `${Math.round(shift)}px`;
  wrap.classList.toggle("is-below", rect.top < 220);
}

function wsChipClick(event, button) {
  const wrap = button.closest(".ws-chip-wrap");
  const touch = window.matchMedia && window.matchMedia("(hover: none)").matches;
  if (touch) {
    // first tap shows the card; its buttons carry the actions
    const open = wrap.classList.contains("is-open");
    document.querySelectorAll(".ws-chip-wrap.is-open").forEach((item) => item.classList.remove("is-open"));
    if (!open) {
      wsPopPlace(wrap);
      wrap.classList.add("is-open");
    }
    return;
  }
  const [kind, ...rest] = String(button.dataset.primary || "").split(":");
  const value = rest.join(":");
  if (kind === "material") previewMaterial(Number(value));
  else if (kind === "git" && value) window.open(value, "_blank", "noopener");
}

function renderWorkstreamChildren(d, writable) {
  if (d.parent) return "";
  const kids = d.child_items || [];
  if (!kids.length) return "";
  const rows = kids.map((kid) => `
    <li class="ws-child">
      ${wsHealthDot(kid.health)}
      <button type="button" class="link-button" onclick="selectWorkstream(${kid.id})">${escapeHtml(kid.name)}</button>
      <small>${[kid.status !== "active" ? WS_STATUS_LABELS[kid.status] : "", kid.owner_label, kid.items_open ? `${kid.items_open} 待跟踪` : "", kid.items_overdue ? `${kid.items_overdue} 逾期` : ""]
        .filter(Boolean).map(escapeHtml).join(" · ")}</small>
    </li>`).join("");
  return `<h3>子工作线 <small>${kids.length}</small></h3><ul class="workstream-list ws-children">${rows}</ul>`;
}

const MILESTONE_ORDER = (a, b) => (a.target_date || "9999").localeCompare(b.target_date || "9999");

function milestoneMoveSelect(current) {
  const options = workstreamList().map((item) =>
    `<option value="${item.id}" ${item.id === current ? "selected" : ""}>${item.parent_id ? "　└ " : ""}${escapeHtml(item.name)}</option>`).join("");
  return `<select name="workstream_id" aria-label="所属工作线"><option value="">项目级（不属于工作线）</option>${options}</select>`;
}

function renderWorkstreamMilestone(d, m, writable, today) {
  if (writable && state.workstreamMilestoneEditing === m.id) {
    return `
      <li class="ws-item is-editing">
        <form class="ws-item-form ws-milestone-form" onsubmit="saveWorkstreamMilestone(event, ${d.id}, ${m.id})">
          <input name="title" maxlength="200" required value="${escapeAttr(m.title || "")}" aria-label="里程碑">
          <input name="owner_label" list="project-member-names" maxlength="60" value="${escapeAttr(m.owner_label || "")}" placeholder="负责人" aria-label="负责人">
          <input name="target_date" type="date" value="${escapeAttr(m.target_date || "")}" aria-label="目标日期">
          <select name="status" aria-label="状态">${statusOptions(m.status)}</select>
          ${milestoneMoveSelect(d.id)}
          <span class="row"><button class="primary" type="submit">保存</button><button type="button" onclick="editWorkstreamMilestone(null)">取消</button></span>
        </form>
      </li>`;
  }
  const done = m.status === "complete";
  const late = !done && m.target_date && m.target_date < today;
  const meta = [
    m.target_date ? `<span class="${late ? "is-overdue" : ""}">${late ? "已逾期 · " : ""}${escapeHtml(m.target_date)}</span>` : "",
    m.status && !["planned", "complete"].includes(m.status) ? escapeHtml(statusLabel(m.status)) : "",
    m.owner_label ? escapeHtml(m.owner_label) : "",
  ].filter(Boolean).join(" · ");
  return `
    <li class="ws-item ws-milestone-item${done ? " is-done" : ""}${late ? " is-late" : ""}">
      ${writable
        ? `<input type="checkbox" ${done ? "checked" : ""} aria-label="${done ? "重新打开" : "标记完成"}：${escapeAttr(m.title || "")}" onchange="toggleWorkstreamMilestone(${d.id}, ${m.id}, this.checked)">`
        : `<span class="ws-item-mark" aria-hidden="true">${done ? "◆" : "◇"}</span>`}
      <div class="ws-item-body">
        <span class="ws-item-title">${escapeHtml(m.title || "")}</span>
        ${meta ? `<small>${meta}</small>` : ""}
      </div>
      ${writable ? `<span class="ws-item-actions">
        <button type="button" class="link-button" onclick="editWorkstreamMilestone(${m.id})">编辑</button>
        <button type="button" class="link-button is-danger" onclick="deleteWorkstreamMilestone(${d.id}, ${m.id})">删除</button>
      </span>` : ""}
    </li>`;
}

function renderWorkstreamMilestones(d, writable) {
  const today = state.workspace?.workstreams?.today || "";
  const list = [...(d.milestones || [])].sort(MILESTONE_ORDER);
  const done = list.filter((m) => m.status === "complete").length;
  const addForm = writable ? `
    <form class="ws-item-form ws-item-add" onsubmit="addWorkstreamMilestone(event, ${d.id})">
      <input name="title" maxlength="200" required placeholder="新增里程碑" aria-label="新增里程碑">
      <input name="owner_label" list="project-member-names" maxlength="60" placeholder="负责人" aria-label="负责人">
      <input name="target_date" type="date" aria-label="目标日期">
      <button type="submit">添加</button>
    </form>` : "";
  return `
    <h3>里程碑 <small>${list.length ? `已完成 ${done}/${list.length}` : ""}</small></h3>
    ${addForm}
    ${list.length ? `<ul class="ws-items">${list.map((m) => renderWorkstreamMilestone(d, m, writable, today)).join("")}</ul>` : `<p class="workstream-empty">暂无里程碑。</p>`}`;
}

function workstreamMilestoneBody(form) {
  const body = {
    title: form.elements.title.value.trim(),
    owner_label: form.elements.owner_label.value.trim(),
    target_date: form.elements.target_date.value,
  };
  if (form.elements.status) body.status = form.elements.status.value;
  if (form.elements.workstream_id) body.workstream_id = Number(form.elements.workstream_id.value) || null;
  return body;
}

function addWorkstreamMilestone(event, workstreamId) {
  event.preventDefault();
  const body = workstreamMilestoneBody(event.target);
  if (!body.title) return;
  workstreamSubRequest(workstreamId, "milestones", "", { method: "POST", body: JSON.stringify(body) }, "已添加里程碑");
}

function editWorkstreamMilestone(id) {
  state.workstreamMilestoneEditing = id;
  renderWorkstreamDetail();
}

function saveWorkstreamMilestone(event, workstreamId, id) {
  event.preventDefault();
  const body = workstreamMilestoneBody(event.target);
  if (!body.title) return;
  const moved = body.workstream_id !== workstreamId;
  workstreamSubRequest(workstreamId, "milestones", `/${id}`, { method: "PUT", body: JSON.stringify(body) },
    moved ? (body.workstream_id ? "里程碑已移到其他工作线" : "里程碑已改为项目级") : "里程碑已更新");
}

function toggleWorkstreamMilestone(workstreamId, id, done) {
  workstreamSubRequest(workstreamId, "milestones", `/${id}`, { method: "PUT", body: JSON.stringify({ status: done ? "complete" : "in_progress" }) }, "");
}

function deleteWorkstreamMilestone(workstreamId, id) {
  if (!window.confirm("删除这个里程碑？")) return;
  workstreamSubRequest(workstreamId, "milestones", `/${id}`, { method: "DELETE" }, "里程碑已删除");
}

function wsItemMeta(item, today) {
  const late = item.status === "open" && item.due_date && item.due_date < today;
  return [
    item.owner_label ? escapeHtml(item.owner_label) : "",
    item.due_date ? `<span class="${late ? "is-overdue" : ""}">${late ? "已逾期 · " : "截止 "}${escapeHtml(item.due_date)}</span>` : "",
    item.status === "done" && item.done_at ? `完成于 ${escapeHtml(formatChinaTime(item.done_at))}` : "",
    item.source === "auto" ? "AI 提取" : "",
  ].filter(Boolean).join(" · ");
}

function renderWorkstreamItem(d, item, writable, today) {
  if (writable && state.workstreamItemEditing === item.id) {
    return `
      <li class="ws-item is-editing">
        <form class="ws-item-form" onsubmit="saveWorkstreamItem(event, ${d.id}, ${item.id})">
          <input name="title" maxlength="200" required value="${escapeAttr(item.title)}" aria-label="待跟踪项">
          <input name="owner_label" list="project-member-names" maxlength="60" value="${escapeAttr(item.owner_label || "")}" placeholder="负责人" aria-label="负责人">
          <input name="due_date" type="date" value="${escapeAttr(item.due_date || "")}" aria-label="截止日期">
          <span class="row"><button class="primary" type="submit">保存</button><button type="button" onclick="editWorkstreamItem(null)">取消</button></span>
        </form>
      </li>`;
  }
  const done = item.status === "done";
  const late = !done && item.due_date && item.due_date < today;
  const meta = wsItemMeta(item, today);
  return `
    <li class="ws-item${done ? " is-done" : ""}${late ? " is-late" : ""}">
      ${writable
        ? `<input type="checkbox" ${done ? "checked" : ""} aria-label="${done ? "重新打开" : "标记完成"}：${escapeAttr(item.title)}" onchange="toggleWorkstreamItem(${d.id}, ${item.id}, this.checked)">`
        : `<span class="ws-item-mark" aria-hidden="true">${done ? "✓" : "○"}</span>`}
      <div class="ws-item-body">
        <span class="ws-item-title">${escapeHtml(item.title)}</span>
        ${meta ? `<small>${meta}</small>` : ""}
      </div>
      ${writable ? `<span class="ws-item-actions">
        <button type="button" class="link-button" onclick="editWorkstreamItem(${item.id})">编辑</button>
        <button type="button" class="link-button is-danger" onclick="deleteWorkstreamItem(${d.id}, ${item.id})">删除</button>
      </span>` : ""}
    </li>`;
}

function renderWorkstreamItems(d, writable) {
  const today = state.workspace?.workstreams?.today || "";
  const items = d.items || [];
  const open = items.filter((item) => item.status === "open");
  const done = items.filter((item) => item.status === "done");
  const addForm = writable ? `
    <form class="ws-item-form ws-item-add" onsubmit="addWorkstreamItem(event, ${d.id})">
      <input name="title" maxlength="200" required placeholder="新增待跟踪项" aria-label="新增待跟踪项">
      <input name="owner_label" list="project-member-names" maxlength="60" placeholder="负责人" aria-label="负责人">
      <input name="due_date" type="date" aria-label="截止日期">
      <button type="submit">添加</button>
    </form>` : "";
  const pct = items.length ? Math.round((done.length / items.length) * 100) : 0;
  return `
    <h3>待跟踪项 <small>${open.length} 项待跟踪${items.length ? ` · 已完成 ${done.length}/${items.length}` : ""}</small></h3>
    ${items.length ? `<span class="ws-items-bar is-wide" role="img" aria-label="完成 ${pct}%"><span style="width:${pct}%"></span></span>` : ""}
    ${addForm}
    ${open.length ? `<ul class="ws-items">${open.map((item) => renderWorkstreamItem(d, item, writable, today)).join("")}</ul>` : `<p class="workstream-empty">没有待跟踪项。${writable ? "AI 整理也会从本周资料中提取。" : ""}</p>`}
    ${done.length ? `<details class="ws-items-done"><summary>已完成 ${done.length}</summary><ul class="ws-items">${done.map((item) => renderWorkstreamItem(d, item, writable, today)).join("")}</ul></details>` : ""}`;
}

function workstreamItemBody(form) {
  return {
    title: form.elements.title.value.trim(),
    owner_label: form.elements.owner_label.value.trim(),
    due_date: form.elements.due_date.value,
  };
}

function workstreamItemRequest(workstreamId, path, options, message) {
  return workstreamSubRequest(workstreamId, "items", path, options, message);
}

async function workstreamSubRequest(workstreamId, kind, path, options, message) {
  const projectId = state.projectId;
  try {
    const detail = await api(`/api/projects/${projectId}/workstreams/${workstreamId}/${kind}${path}`, options);
    if (state.projectId !== projectId) return;
    state.workstreamItemEditing = null;
    state.workstreamMilestoneEditing = null;
    if (state.workstreamId === workstreamId) state.workstreamDetail = { ...detail, projectId };
    await loadWorkspace();
    if (message) toast(message);
  } catch (error) {
    toast(error.message);
  }
}

function addWorkstreamItem(event, workstreamId) {
  event.preventDefault();
  const body = workstreamItemBody(event.target);
  if (!body.title) return;
  workstreamItemRequest(workstreamId, "", { method: "POST", body: JSON.stringify(body) }, "已添加待跟踪项");
}

function editWorkstreamItem(itemId) {
  state.workstreamItemEditing = itemId;
  renderWorkstreamDetail();
}

function saveWorkstreamItem(event, workstreamId, itemId) {
  event.preventDefault();
  const body = workstreamItemBody(event.target);
  if (!body.title) return;
  workstreamItemRequest(workstreamId, `/${itemId}`, { method: "PUT", body: JSON.stringify(body) }, "待跟踪项已更新");
}

function toggleWorkstreamItem(workstreamId, itemId, done) {
  workstreamItemRequest(workstreamId, `/${itemId}`, { method: "PUT", body: JSON.stringify({ status: done ? "done" : "open" }) }, "");
}

function deleteWorkstreamItem(workstreamId, itemId) {
  if (!window.confirm("删除这条待跟踪项？")) return;
  workstreamItemRequest(workstreamId, `/${itemId}`, { method: "DELETE" }, "待跟踪项已删除");
}

function openWorkstreamDialog(id, parentId = null) {
  const form = $("workstream-form");
  const item = id ? (state.workstreamDetail && state.workstreamDetail.id === id ? state.workstreamDetail : workstreamById(id)) : null;
  $("workstream-dialog-title").textContent = item ? "编辑工作线" : parentId ? "新建子工作线" : "新建工作线";
  // two levels at most: only top-level lines can be parents, and a line with children stays top-level
  const hasKids = !!(item && (item.children || []).length);
  const parents = workstreamList().filter((w) => !w.parent_id && (!item || w.id !== item.id));
  const select = $("workstream-parent-select");
  select.innerHTML = `<option value="">无（一级工作线）</option>${parents.map((w) => `<option value="${w.id}">${escapeHtml(w.name)}</option>`).join("")}`;
  select.value = String((item ? item.parent_id : parentId) || "");
  select.disabled = hasKids;
  select.title = hasKids ? "有子工作线的工作线不能再挂到其他工作线下" : "";
  form.elements.id.value = item ? String(item.id) : "";
  form.elements.name.value = item?.name || "";
  form.elements.goal.value = item?.goal || "";
  const ownerSelect = form.elements.owner_member_id;
  const members = projectMembers();
  const ownerId = item?.owner_member_id || "";
  ownerSelect.innerHTML = `<option value="">未指定</option>${members.map((m) =>
    `<option value="${m.id}">${escapeHtml(m.name)}${m.username && m.username !== m.name ? `（${escapeHtml(m.username)}）` : ""}</option>`).join("")}`;
  ownerSelect.value = String(ownerId);
  $("workstream-owner-hint").classList.toggle("hidden", members.length > 0);
  form.elements.target_date.value = item?.target_date || "";
  form.elements.status.value = item?.status || "active";
  $("workstream-dialog").showModal();
}

async function submitWorkstreamForm(event) {
  event.preventDefault();
  const form = $("workstream-form");
  const id = Number(form.elements.id.value) || null;
  const body = {
    name: form.elements.name.value.trim(),
    goal: form.elements.goal.value,
    owner_member_id: Number(form.elements.owner_member_id.value) || null,
    target_date: form.elements.target_date.value,
    status: form.elements.status.value,
  };
  if (!form.elements.parent_id.disabled) body.parent_id = Number(form.elements.parent_id.value) || null;
  if (!body.name) {
    toast("请填写工作线名称");
    return;
  }
  try {
    const data = await api(`/api/projects/${state.projectId}/workstreams${id ? `/${id}` : ""}`, {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(body),
    });
    $("workstream-dialog").close();
    if (!id && data.id) state.workstreamId = data.id;
    await loadWorkspace();
    if (state.workstreamId) await loadWorkstreamDetail(state.workstreamId);
    toast(id ? "工作线已更新" : "工作线已创建");
  } catch (error) {
    toast(error.message);
  }
}

async function seedWorkstreams() {
  try {
    // the server seeds from the saved objectives: save unsaved edits of the 项目计划 tab first
    const form = $("plan-form");
    if (form && form.objectives && form.objectives.value !== (state.workspace?.plan?.objectives || "")) await savePlan();
    const data = await api(`/api/projects/${state.projectId}/workstreams/seed`, { method: "POST", body: "{}" });
    await loadWorkspace();
    toast(data.created ? `已从项目目标生成 ${data.created} 条工作线，在「工作线」页签查看` : "目标里的工作线都已存在");
  } catch (error) {
    toast(error.message);
  }
}

async function organizeWorkstreams() {
  try {
    const data = await api(`/api/projects/${state.projectId}/workstreams/organize`, { method: "POST", body: "{}" });
    reportJobs.set(data.id, { projectId: state.projectId, kind: "workstreams", status: data.status || "queued" });
    const button = $("workstream-organize-btn");
    if (button) {
      button.disabled = true;
      button.textContent = "整理中…";
    }
    toast("工作线整理任务已提交，完成后自动刷新");
    startQueuePolling();
  } catch (error) {
    toast(`提交失败：${error.message}`);
  }
}

async function workstreamJobFinished(jobId, job) {
  let finished = null;
  try {
    finished = await api(`/api/projects/${job.projectId}/workspace`);
  } catch {
    toast("工作线整理已结束");
    return;
  }
  if (job.projectId === state.projectId) {
    updateWorkspace(finished);
    if (state.workstreamId) await loadWorkstreamDetail(state.workstreamId);
  }
  const record = finished.workstream_job;
  const name = (finished.project && finished.project.name) || "项目";
  if (record && record.id === jobId && record.status === "success") toast(`「${name}」工作线整理完成：${record.output_md || ""}`);
  else toast(`「${name}」工作线整理失败：${(record && record.failure_reason) || "未知错误"}`);
}

// ids of the lines that share this line's parent (top-level lines share none), in display order
function wsSiblings(id) {
  const items = workstreamList();
  const item = items.find((w) => w.id === id);
  if (!item) return [];
  return items.filter((w) => (w.parent_id || null) === (item.parent_id || null)).map((w) => w.id);
}

async function moveWorkstream(id, delta) {
  const items = workstreamList();
  const item = items.find((w) => w.id === id);
  const siblings = wsSiblings(id);
  const index = siblings.indexOf(id);
  const target = index + delta;
  if (!item || index < 0 || target < 0 || target >= siblings.length) return;
  [siblings[index], siblings[target]] = [siblings[target], siblings[index]];
  // a parent moves with its children; positions are rebuilt from the whole tree order
  const tops = item.parent_id ? items.filter((w) => !w.parent_id).map((w) => w.id) : siblings;
  const kids = (parentId) => (item.parent_id === parentId ? siblings : items.filter((w) => w.parent_id === parentId).map((w) => w.id));
  const ids = tops.flatMap((top) => [top, ...kids(top)]);
  items.forEach((w) => { if (!ids.includes(w.id)) ids.push(w.id); });
  await api(`/api/projects/${state.projectId}/workstreams/reorder`, { method: "POST", body: JSON.stringify({ ids }) });
  await loadWorkspace();
}

async function deleteWorkstream(id) {
  const item = workstreamById(id);
  const kids = item && (item.children || []).length ? `它的 ${item.children.length} 条子工作线会变成一级工作线。` : "";
  if (!window.confirm(`删除工作线「${item ? item.name : ""}」？关联资料和 TODO 会保留，只移除归属、周快照和待跟踪项。${kids}`)) return;
  await api(`/api/projects/${state.projectId}/workstreams/${id}`, { method: "DELETE" });
  state.workstreamId = null;
  state.workstreamDetail = null;
  await loadWorkspace();
  toast("工作线已删除");
}

async function saveWorkstreamSnapshot(id) {
  const summary = $("ws-snap-summary")?.value.trim() || "";
  if (!summary) {
    toast("请填写本周进展");
    $("ws-snap-summary")?.focus();
    return;
  }
  try {
    const detail = await api(`/api/projects/${state.projectId}/workstreams/${id}/snapshots`, {
      method: "PUT",
      body: JSON.stringify({
        status: $("ws-snap-status").value,
        summary,
        next_step: $("ws-snap-next").value.trim(),
      }),
    });
    state.workstreamDetail = { ...detail, projectId: state.projectId };
    await loadWorkspace();
    toast("周快照已记录");
  } catch (error) {
    toast(error.message);
  }
}

function showWorkstreamMaterials(filter) {
  state.sourceWorkstreamFilter = filter === "none" ? "none" : Number(filter);
  renderSources(state.workspace);
  switchTab("sources");
}

function sourceFilterActive() {
  const filter = state.sourceWorkstreamFilter;
  if (filter === "none") return "none";
  return workstreamById(filter) ? Number(filter) : "all";
}

// a parent's filter also shows the material of its 子工作线
function materialMatchesWorkstream(m, filter) {
  if (filter === "all") return true;
  const links = m.workstreams || {};
  if (filter === "none") return !links.primary;
  const ids = new Set([filter, ...((workstreamById(filter) || {}).children || [])]);
  return ids.has(links.primary) || (links.related || []).some((id) => ids.has(id));
}

function setSourceWorkstreamFilter(filter) {
  state.sourceWorkstreamFilter = filter;
  renderSources(state.workspace);
}

function renderWorkstreamFilter(ws) {
  const items = workstreamList();
  if (!items.length) return "";
  const active = sourceFilterActive();
  const unassigned = ws.materials.filter((m) => !(m.workstreams || {}).primary).length;
  const option = (value, label) => `<option value="${value}" ${active === value ? "selected" : ""}>${label}</option>`;
  return `
    <label class="workstream-filter"><span>工作线</span>
      <select aria-label="按工作线筛选" onchange="setSourceWorkstreamFilter(this.value === 'all' || this.value === 'none' ? this.value : Number(this.value))">
        ${option("all", "全部工作线")}
        ${option("none", `未归类 (${unassigned})`)}
        ${items.filter((item) => item.status !== "done" || active === item.id).map((item) => option(item.id, `${item.parent_id ? "　└ " : ""}${escapeHtml(item.name)}`)).join("")}
      </select>
    </label>`;
}

function materialWorkstreamTag(m, writable) {
  const links = m.workstreams || {};
  const primary = links.primary ? workstreamById(links.primary) : null;
  if (!primary && !workstreamList().length) return "";
  const extra = (links.related || []).length ? ` +${links.related.length}` : "";
  const label = primary ? `${escapeHtml(primary.name)}${extra}` : "＋ 工作线";
  const auto = primary && links.source === "auto" ? " · AI" : "";
  const cls = `ws-tag${primary ? "" : " is-empty"}`;
  if (!writable) return primary ? `<span class="${cls}">${label}</span>` : "";
  return `<button type="button" class="${cls}" title="设置归属工作线" onclick="openWorkstreamAssign('material', ${m.id})">${label}${auto}</button>`;
}

function todoWorkstreamTag(todo) {
  const links = todo.workstreams || {};
  const primary = links.primary;
  if (!primary && !(state.todoWorkstreamOptions || []).length) return "";
  const extra = (links.related || []).length ? ` +${links.related.length}` : "";
  const label = primary ? `${escapeHtml(primary.name)}${extra}` : "＋ 工作线";
  const title = primary ? `${primary.project_name} · ${primary.path || primary.name}` : "设置归属工作线";
  return `<button type="button" class="todo-ws-tag${primary ? "" : " is-empty"}" title="${escapeAttr(title)}" onclick="event.stopPropagation(); openWorkstreamAssign('todo', ${todo.id})">${label}</button>`;
}

function openWorkstreamAssign(kind, id) {
  let groups = [];
  let primary = null;
  let related = [];
  let context = "";
  if (kind === "git") {
    const g = (state.workstreamGitItems || {})[id] || (state.workstreamUnassignedGit || {})[id];
    if (!g) return;
    primary = g.workstream_id || null;
    groups = [{ project_name: "", workstreams: workstreamList().filter((item) => item.status !== "done" || item.id === primary) }];
    context = `${g.repo}#${g.number} ${g.title}`;
  } else if (kind === "material") {
    const m = (state.workspace?.materials || []).find((item) => item.id === id);
    if (!m) return;
    const links = m.workstreams || {};
    primary = links.primary || null;
    related = links.related || [];
    const linked = new Set([primary, ...related]);
    groups = [{ project_name: "", workstreams: workstreamList().filter((item) => item.status !== "done" || linked.has(item.id)) }];
    context = m.filename;
  } else {
    const todo = state.todos.find((item) => item.id === id);
    if (!todo) return;
    const links = todo.workstreams || {};
    primary = links.primary ? links.primary.id : null;
    related = (links.related || []).map((item) => item.id);
    groups = state.todoWorkstreamOptions || [];
    context = todo.title;
  }
  state.workstreamAssign = { kind, id };
  $("workstream-assign-context").textContent = context;
  const option = (item) => `<option value="${item.id}" ${item.id === primary ? "selected" : ""}>${item.parent_id ? "　└ " : ""}${escapeHtml(item.name)}</option>`;
  $("workstream-assign-primary").innerHTML = `<option value="">不归类</option>${groups.map((group) => group.project_name
    ? `<optgroup label="${escapeAttr(group.project_name)}">${group.workstreams.map(option).join("")}</optgroup>`
    : group.workstreams.map(option).join("")).join("")}`;
  const boxes = groups.flatMap((group) => group.workstreams.map((item) => `
    <label class="checkbox-row"><input type="checkbox" value="${item.id}" ${related.includes(item.id) ? "checked" : ""}>${group.project_name ? `${escapeHtml(group.project_name)} · ` : ""}${escapeHtml(item.path || item.name)}</label>`)).join("");
  $("workstream-assign-related").innerHTML = `<legend>同时关联</legend>${boxes || "<p class=\"workstream-empty\">暂无可选工作线。</p>"}`;
  // a PR / issue belongs to one workstream only
  $("workstream-assign-related").classList.toggle("hidden", kind === "git");
  $("workstream-assign-dialog").showModal();
}

async function submitWorkstreamAssign(event) {
  event.preventDefault();
  const target = state.workstreamAssign;
  if (!target) return;
  const primary = Number($("workstream-assign-primary").value) || null;
  const related = Array.from($("workstream-assign-related").querySelectorAll("input:checked"))
    .map((box) => Number(box.value)).filter((value) => value && value !== primary);
  if (!primary && related.length) {
    toast("关联工作线需要先选择主工作线");
    return;
  }
  try {
    if (target.kind === "git") {
      await api(`/api/projects/${state.projectId}/workstreams/git/${target.id}/link`, { method: "PUT", body: JSON.stringify({ workstream_id: primary }) });
      await loadWorkspace();
      if (state.workstreamId) await loadWorkstreamDetail(state.workstreamId);
    } else if (target.kind === "material") {
      updateWorkspace(await api(`/api/projects/${state.projectId}/materials/${target.id}/workstreams`, {
        method: "PUT",
        body: JSON.stringify({ primary, related }),
      }));
      if (state.workstreamId) await loadWorkstreamDetail(state.workstreamId);
    } else {
      updateTodos(await api(`/api/todos/${target.id}/workstreams`, { method: "PUT", body: JSON.stringify({ primary, related }) }));
    }
    $("workstream-assign-dialog").close();
    toast("归属已更新");
  } catch (error) {
    toast(error.message);
  }
}

function renderOverviewWorkstreams(ws) {
  const items = ((ws.workstreams || {}).workstreams || []).filter((item) => item.status !== "done");
  if (!items.length) return "";
  const rows = items.map((item) => {
    const latest = [...(item.cells || [])].reverse().find((cell) => cell.snapshot);
    return `<tr onclick="openWorkstreamFromOverview(${item.id})" class="ws-overview-row${item.parent_id ? " is-child" : ""}">
      <td data-label="工作线"><span class="ws-name-line">${item.parent_id ? `<span class="ws-branch" aria-hidden="true">└</span>` : ""}${wsHealthDot(item.health)}<strong>${escapeHtml(item.name)}</strong></span></td>
      <td data-label="最近进展">${latest ? `${escapeHtml(wsShortWeek(latest.week_key))} · ${escapeHtml(latest.snapshot.summary)}` : "—"}</td>
      <td data-label="待跟踪" class="ws-overview-items">${item.items_open ? `${item.items_open} 待跟踪${item.items_overdue ? ` · <b class="is-overdue">${item.items_overdue} 逾期</b>` : ""}` : "—"}</td>
    </tr>`;
  }).join("");
  return `
    <div class="panel">
      <div class="panel-head"><h2>工作线</h2><span>${items.length} 条进行中或暂停</span></div>
      <table class="table"><tbody>${rows}</tbody></table>
      <div class="row"><button onclick="switchTab('workstreams')">打开工作线</button></div>
    </div>`;
}

async function openWorkstreamFromOverview(id) {
  switchTab("workstreams");
  if (state.workstreamId !== id) await selectWorkstream(id);
}

function renderSettings(ws) {
  const p = ws.project;
  const manage = canManageWorkspace();
  const owner = isProjectOwner();
  if (state.settingsSubTab === "sharing" && !owner) state.settingsSubTab = "project";
  $("tab-settings").innerHTML = `
    <div class="source-tabs" role="tablist" aria-label="设置分类">
      <button type="button" data-subtab="project" role="tab" onclick="switchSettingsSubTab('project')">项目设置</button>
      <button type="button" data-subtab="members" role="tab" onclick="switchSettingsSubTab('members')">项目组</button>
      <button type="button" data-subtab="git" role="tab" onclick="switchSettingsSubTab('git')">Git 仓库</button>
      <button type="button" data-subtab="diagnostics" role="tab" onclick="switchSettingsSubTab('diagnostics')">系统诊断</button>
      ${owner ? `<button type="button" data-subtab="sharing" role="tab" onclick="switchSettingsSubTab('sharing')">共享</button>` : ""}
    </div>
    <section id="settings-sub-project" class="source-view" role="tabpanel">
      <form id="settings-form" class="panel form-grid">
        <div class="panel-head wide">
          <div class="panel-title"><h2>项目设置</h2><span>${manage ? "项目与报告配置 · 修改后自动保存" : "项目与报告配置 · 只读"}</span><span class="autosave-status" aria-live="polite"></span></div>
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
    <section id="settings-sub-members" class="source-view hidden" role="tabpanel">
      <div class="panel">
        <div class="panel-head"><h2>项目组成员</h2><span>工作线负责人从这里选择${manage ? "" : " · 只读"}</span></div>
        ${manage ? `
        <div class="row share-add-row member-add-row">
          <select id="member-user-select" aria-label="选择账号"><option value="">不关联账号</option></select>
          <input id="member-name-input" maxlength="60" placeholder="成员名称（选了账号可留空）" aria-label="成员名称" onkeydown="if (event.key === 'Enter') { event.preventDefault(); addProjectMember(); }">
          <button type="button" class="primary" onclick="addProjectMember()">添加成员</button>
        </div>` : ""}
        <table class="table"><thead><tr><th>成员</th><th>关联账号</th><th>负责工作线</th>${manage ? "<th>操作</th>" : ""}</tr></thead><tbody id="member-table-body">${renderMemberRows(ws.members || [], manage)}</tbody></table>
      </div>
    </section>
    <section id="settings-sub-git" class="source-view hidden" role="tabpanel">
      <div class="panel">
        <div class="panel-head"><h2>Git 仓库</h2><span>GitHub / GitLab，commits 每周进入生成上下文；抓取项决定本周 PR/MR、Issue、里程碑、仓库 Project、组织 Project 是否一并读取</span></div>
        ${manage ? `
        <div class="row">
          <select id="repo-mode-input" onchange="onRepoModeChange()" aria-label="Git 模式">${state.githubEnabled !== false ? '<option value="github">GitHub</option>' : ""}${state.gitlabEnabled !== false ? '<option value="gitlab">GitLab</option>' : ""}</select>
          <input id="repo-input" placeholder="owner/repo">
          <input id="repo-notes-input" placeholder="补充说明，例如正式名称、模块边界">
          <button type="button" onclick="addRepo()">添加仓库</button>
        </div>` : `<p class="share-readonly-hint">需要管理权限才能添加或修改 Git 仓库。</p>`}
        <table class="table"><thead><tr><th>仓库</th><th>跟踪分支</th><th>补充说明</th><th>抓取项</th><th>状态</th><th>操作</th></tr></thead><tbody>${ws.repos.map((r) => renderRepoRow(r, manage)).join("") || "<tr><td colspan='6'>暂无仓库。</td></tr>"}</tbody></table>
      </div>
    </section>
    <section id="settings-sub-diagnostics" class="source-view hidden" role="tabpanel">
      <div class="panel">
        <div class="panel-head"><h2>系统诊断</h2><span>资料源与生成状态</span></div>
        <table class="table"><thead><tr><th>类型</th><th>严重度</th><th>标题</th><th>更新时间</th></tr></thead><tbody>${(ws.source_diagnostics || []).map(d => `<tr><td>${escapeHtml(d.kind)}</td><td><span class="status ${d.severity}">${escapeHtml(statusLabel(d.severity))}</span></td><td>${escapeHtml(d.title)}<br>${escapeHtml(d.details || "")}</td><td>${escapeHtml(formatChinaTime(d.updated_at))}</td></tr>`).join("") || "<tr><td colspan='4'>暂无诊断信息。</td></tr>"}</tbody></table>
      </div>
    </section>
    ${owner ? `
    <section id="settings-sub-sharing" class="source-view hidden" role="tabpanel">
      <div class="panel">
        <div class="panel-head"><h2>共享成员</h2><span>把项目共享给其他账号并分配权限 · 仅项目所有者可操作</span></div>
        <div class="row share-add-row">
          <select id="share-user-select" aria-label="要共享到的账号">
            <option value="">加载中…</option>
          </select>
          <select id="share-role-select" aria-label="共享权限">
            ${SHARE_ROLES.map((role) => `<option value="${role}">${SHARE_ROLE_LABELS[role]}</option>`).join("")}
          </select>
          <button type="button" id="share-add-button" class="primary" onclick="addProjectShare()">添加成员</button>
        </div>
        <table class="table"><thead><tr><th>成员</th><th>权限</th><th>添加时间</th><th>上次访问</th><th>操作</th></tr></thead><tbody id="share-table-body"><tr><td colspan="5">加载中…</td></tr></tbody></table>
        <small>只读：查看周报、资料、计划与仓库状态；上传资料：上传和编辑资料、设置资料归属工作线、把 TODO 归档到项目；读写：另可填写本周补充、调整计划和当前周报、生成周报、维护工作线与 AI 整理；管理：项目设置、Git 仓库与资料删除。共享成员看不到共享管理入口，也无法把项目再共享给他人。</small>
      </div>
    </section>` : ""}
  `;
  $("settings-form").onsubmit = saveSettings;
  setupAutoSave("project-settings", $("settings-form"), saveSettings);
  // 只读/读写角色没有管理权限：整个设置表单停用，停用的控件不再触发
  // 自动保存，也不会进入提交 payload
  if (!manage) {
    $("settings-form").querySelectorAll("input, textarea, select, button").forEach((el) => { el.disabled = true; });
  }
  // 仓库行的补充说明与分支勾选也是填写即保存（分支 change 事件会冒泡到行上）
  if (manage) {
    document.querySelectorAll("textarea[id^='repo-notes-']").forEach((el) => {
      const id = Number(el.id.replace("repo-notes-", ""));
      setupAutoSave(`repo-notes-${id}`, el.closest("tr"), () => saveRepoNotes(id));
    });
  }
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
  ["project", "members", "git", "diagnostics", "sharing"].forEach((name) => {
    const view = root.querySelector(`#settings-sub-${name}`);
    if (view) view.classList.toggle("hidden", name !== tab);
  });
  if (tab === "sharing" && isProjectOwner()) {
    loadProjectShares();
    loadShareCandidates();
  }
  if (tab === "members" && canManageWorkspace()) loadMemberCandidates();
}

// —— 项目组成员：账号或手填姓名；工作线负责人从这里选择 ——

function renderMemberDatalist(ws) {
  const list = $("project-member-names");
  if (list) list.innerHTML = (ws.members || []).map((m) => `<option value="${escapeAttr(m.name)}"></option>`).join("");
}

function projectMembers() {
  return state.workspace?.members || [];
}

function renderMemberRows(members, manage) {
  return members.map((m) => `
    <tr>
      <td data-label="成员">${manage
        ? `<input value="${escapeAttr(m.name)}" maxlength="60" aria-label="成员名称" onchange="renameProjectMember(${m.id}, this)">`
        : `<strong>${escapeHtml(m.name)}</strong>`}</td>
      <td data-label="关联账号">${manage
        ? `<select class="member-account-select" data-member-id="${m.id}" aria-label="${escapeAttr(m.name)} 的关联账号" onchange="relinkProjectMember(${m.id}, this)">${memberAccountOptions(m)}</select>`
        : (m.username ? escapeHtml(m.username) : "—")}</td>
      <td data-label="负责工作线">${m.workstream_count || 0}</td>
      ${manage ? `<td data-label="操作"><div class="table-actions"><button type="button" class="danger" onclick="removeProjectMember(${m.id})">移除</button></div></td>` : ""}
    </tr>`).join("") || `<tr><td colspan="${manage ? 4 : 3}">还没有项目组成员。</td></tr>`;
}

// 每行的账号下拉：当前关联账号 + 尚未入组的账号
function memberAccountOptions(m) {
  const accounts = [...(m.user_id ? [{ id: m.user_id, username: m.username }] : []), ...(state.memberCandidates || [])];
  return `<option value="">不关联账号</option>${accounts.map((u) =>
    `<option value="${u.id}"${u.id === m.user_id ? " selected" : ""}>${escapeHtml(u.username)}</option>`).join("")}`;
}

async function loadMemberCandidates() {
  const select = $("member-user-select");
  if (!select) return;
  try {
    const data = await api(`/api/projects/${state.projectId}/members/candidates`);
    state.memberCandidates = data.candidates || [];
    select.innerHTML = `<option value="">不关联账号</option>${state.memberCandidates
      .map((u) => `<option value="${u.id}">${escapeHtml(u.username)}</option>`).join("")}`;
    document.querySelectorAll(".member-account-select").forEach((el) => {
      const member = projectMembers().find((m) => m.id === Number(el.dataset.memberId));
      if (member) el.innerHTML = memberAccountOptions(member);
    });
  } catch (error) {
    toast(error.message);
  }
}

async function relinkProjectMember(id, select) {
  const member = projectMembers().find((m) => m.id === id);
  if (!member) return;
  const userId = Number(select.value) || null;
  if (userId === (member.user_id || null)) return;
  const ok = await memberRequest(`/${id}`, { method: "PUT", body: JSON.stringify({ user_id: userId }) }, userId ? "关联账号已更新" : "已取消关联账号");
  if (!ok) select.value = String(member.user_id || "");
}

async function memberRequest(path, options, message) {
  try {
    await api(`/api/projects/${state.projectId}/members${path}`, options);
    await loadWorkspace();
    if (state.workstreamId) await loadWorkstreamDetail(state.workstreamId);
    if (canManageWorkspace()) loadMemberCandidates();
    toast(message);
    return true;
  } catch (error) {
    toast(error.message);
    return false;
  }
}

async function addProjectMember() {
  const userId = Number($("member-user-select")?.value) || null;
  const name = ($("member-name-input")?.value || "").trim();
  if (!userId && !name) {
    toast("请选择账号或填写成员名称");
    return;
  }
  await memberRequest("", { method: "POST", body: JSON.stringify({ user_id: userId, name }) }, "已添加项目组成员");
}

async function renameProjectMember(id, input) {
  const name = input.value.trim();
  const member = projectMembers().find((m) => m.id === id);
  if (!member || name === member.name) return;
  if (!name) {
    input.value = member.name;
    toast("成员名称不能为空");
    return;
  }
  if (!(await memberRequest(`/${id}`, { method: "PUT", body: JSON.stringify({ name }) }, "成员名称已更新"))) input.value = member.name;
}

async function removeProjectMember(id) {
  const member = projectMembers().find((m) => m.id === id);
  if (!member) return;
  const owned = member.workstream_count ? `，其负责的 ${member.workstream_count} 条工作线将变为未指定负责人` : "";
  if (!window.confirm(`从项目组移除「${member.name}」${owned}？`)) return;
  await memberRequest(`/${id}`, { method: "DELETE" }, "已移除项目组成员");
}

// —— 共享成员管理（仅项目所有者）：显式按钮即时保存，不走表单自动保存 ——

function renderShareRows() {
  const body = $("share-table-body");
  if (!body) return;
  body.innerHTML = (state.projectShares || []).map((share) => `
    <tr>
      <td data-label="成员"><strong>${escapeHtml(share.username)}</strong></td>
      <td data-label="权限"><select aria-label="${escapeAttr(share.username)} 的共享权限" onchange="changeShareRole(${share.user_id}, this.value)">
        ${SHARE_ROLES.map((role) => `<option value="${role}" ${share.role === role ? "selected" : ""}>${SHARE_ROLE_LABELS[role]}</option>`).join("")}
      </select></td>
      <td data-label="添加时间">${escapeHtml(formatChinaTime(share.created_at))}</td>
      <td data-label="上次访问">${share.last_accessed_at ? escapeHtml(formatChinaTime(share.last_accessed_at)) : "从未访问"}</td>
      <td data-label="操作"><div class="table-actions"><button type="button" class="danger" onclick="removeProjectShare(${share.user_id})">移除</button></div></td>
    </tr>
  `).join("") || "<tr><td colspan='5'>还没有共享成员。</td></tr>";
}

async function loadProjectShares() {
  try {
    const data = await api(`/api/projects/${state.projectId}/shares`);
    state.projectShares = data.shares || [];
    renderShareRows();
  } catch (error) {
    const body = $("share-table-body");
    if (body) body.innerHTML = `<tr><td colspan='5'>${escapeHtml(error.message)}</td></tr>`;
  }
}

// 可共享账号下拉：后端返回除所有者与现有成员外的启用账号
function renderShareUserOptions() {
  const select = $("share-user-select");
  if (!select) return;
  const candidates = state.shareCandidates || [];
  select.innerHTML = candidates.length
    ? candidates.map((user) => `<option value="${escapeAttr(user.username)}">${escapeHtml(user.username)}</option>`).join("")
    : `<option value="">没有可共享的账号</option>`;
  const add = $("share-add-button");
  if (add) add.disabled = candidates.length === 0;
}

async function loadShareCandidates() {
  try {
    const data = await api(`/api/projects/${state.projectId}/shares/candidates`);
    state.shareCandidates = data.candidates || [];
    renderShareUserOptions();
  } catch (error) {
    state.shareCandidates = [];
    renderShareUserOptions();
    toast(error.message);
  }
}

async function addProjectShare() {
  const username = $("share-user-select")?.value || "";
  const role = $("share-role-select")?.value || "read";
  if (!username) {
    toast("没有可共享的账号");
    return;
  }
  try {
    const data = await api(`/api/projects/${state.projectId}/shares`, { method: "PUT", body: JSON.stringify({ username, role }) });
    state.projectShares = data.shares || [];
    renderShareRows();
    toast(`已共享给 ${username}（${SHARE_ROLE_LABELS[role]}）`);
    loadShareCandidates();
  } catch (error) {
    toast(error.message);
  }
}

async function changeShareRole(userId, role) {
  const share = (state.projectShares || []).find((item) => item.user_id === userId);
  if (!share) return;
  try {
    const data = await api(`/api/projects/${state.projectId}/shares`, { method: "PUT", body: JSON.stringify({ username: share.username, role }) });
    state.projectShares = data.shares || [];
    renderShareRows();
    toast("共享权限已更新");
  } catch (error) {
    toast(error.message);
    loadProjectShares();
  }
}

async function removeProjectShare(userId) {
  const share = (state.projectShares || []).find((item) => item.user_id === userId);
  if (!share) return;
  if (!window.confirm(`移除「${share.username}」对此项目的访问权限？`)) return;
  try {
    const data = await api(`/api/projects/${state.projectId}/shares/${userId}`, { method: "DELETE" });
    state.projectShares = data.shares || [];
    renderShareRows();
    toast("已移除共享成员");
    loadShareCandidates();
  } catch (error) {
    toast(error.message);
  }
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

function renderRepoRow(r, manage = true) {
  const enabled = Number(r.enabled) !== 0;
  const modeLabel = r.git_mode === "gitlab" ? "GitLab" : "GitHub";
  return `
    <tr class="${enabled ? "" : "repo-row-disabled"}">
      <td data-label="仓库"><span class="status">${modeLabel}</span><br>${escapeHtml(r.repo)}</td>
      <td data-label="跟踪分支">${manage ? `${renderBranchPicker(r)}<div class="autosave-status" aria-live="polite"></div>` : `<span>${escapeHtml(trackedBranchSummary(r))}</span>`}</td>
      <td data-label="补充说明">${manage
        ? `<textarea id="repo-notes-${r.id}" class="table-textarea">${escapeHtml(r.notes || "")}</textarea>`
        : `<div class="locked-material">${escapeHtml(r.notes || "") || "—"}</div>`}</td>
      <td data-label="抓取项"><div class="repo-fetch-flags">${renderRepoFetchFlags(r, manage)}</div>${renderRepoWorkstream(r, manage)}</td>
      <td data-label="启用">${enabled
        ? `<span class="status ${r.status}">${escapeHtml(r.status)}</span><br>${escapeHtml(r.status_message || "")}`
        : `<span class="status disabled">已停用</span><br>不参与周报生成`}</td>
      <td data-label="操作">${manage ? `<div class="table-actions"><label class="switch" title="${enabled ? "已启用 · 参与周报生成" : "已停用 · 不参与周报生成"}"><input type="checkbox" data-autosave-ignore aria-label="启用或停用该仓库" ${enabled ? "checked" : ""} onchange="toggleRepo(${r.id}, this.checked)"><span class="switch-slider"></span></label><button type="button" onclick="refreshRepo(${r.id})">刷新</button><button type="button" class="danger" onclick="deleteRepo(${r.id})">删除</button></div>` : `<span class="status">仅查看</span>`}</td>
    </tr>
  `;
}

function trackedBranchSummary(r) {
  const selected = r.tracked_branches && r.tracked_branches.length ? r.tracked_branches : ["main"];
  return selected.includes(TRACK_ALL_BRANCHES) ? "All" : selected.join(", ");
}

const REPO_FETCH_FLAGS = [
  ["fetch_pull_requests", "PR", "抓取本周更新的 Pull Request / Merge Request", "both"],
  ["fetch_issues", "Issue", "抓取本周更新的 Issue", "both"],
  ["fetch_milestones", "里程碑", "抓取仓库里程碑及到期状态", "both"],
  ["fetch_repo_projects", "Project", "抓取仓库自己的 GitHub Projects 看板", "github"],
  ["fetch_org_projects", "组织Project", "读取 GitHub 组织 Projects 看板（同组织多个仓库只读取一次）", "github"],
];

function renderRepoFetchFlags(r, manage = true) {
  const gitlab = r.git_mode === "gitlab";
  return REPO_FETCH_FLAGS
    .filter(([, , , scope]) => scope === "both" || !gitlab)
    .map(([key, label, title]) => `
      <label class="repo-fetch-flag" title="${title}">
        <input type="checkbox" data-autosave-ignore aria-label="${label}抓取开关" ${Number(r[key]) ? "checked" : ""} ${manage ? "" : "disabled"} onchange="toggleRepoFetch(${r.id}, '${key}', this)">
        <span>${label}</span>
      </label>
    `).join("");
}

// PR / issue activity of the repository goes to this workstream unless the agent or a person chose another
function renderRepoWorkstream(r, manage = true) {
  const items = workstreamList();
  if (!items.length) return "";
  const current = Number(r.workstream_id) || null;
  const options = items.filter((w) => w.status !== "done" || w.id === current)
    .map((w) => `<option value="${w.id}" ${w.id === current ? "selected" : ""}>${w.parent_id ? "　└ " : ""}${escapeHtml(w.name)}</option>`).join("");
  return `<label class="repo-workstream" title="开启 PR / Issue 抓取后，这个仓库的 PR 和 Issue 默认归到所选工作线；不选则由 AI 按标题归类">PR/Issue 归属
    <select data-autosave-ignore ${manage ? "" : "disabled"} onchange="setRepoWorkstream(${r.id}, this)"><option value="">AI 按标题归类</option>${options}</select></label>`;
}

async function setRepoWorkstream(id, select) {
  const value = Number(select.value) || null;
  try {
    updateWorkspace(await api(`/api/projects/${state.projectId}/repos/${id}`, { method: "PUT", body: JSON.stringify({ workstream_id: value }) }));
    toast(value ? `该仓库的 PR/Issue 默认归到「${workstreamById(value)?.name || ""}」` : "该仓库的 PR/Issue 改由 AI 按标题归类");
  } catch (error) {
    toast(error.message);
  }
}

async function toggleRepoFetch(id, key, input) {
  const checked = input.checked;
  const payload = {};
  payload[key] = checked ? 1 : 0;
  try {
    await api(`/api/projects/${state.projectId}/repos/${id}`, { method: "PUT", body: JSON.stringify(payload) });
  } catch (error) {
    // 保存失败时回滚勾选框与本地状态，避免界面显示服务端不存在的开关值
    input.checked = !checked;
    toast(error.message || "保存失败，请重试");
    return;
  }
  const repo = (state.workspace.repos || []).find((item) => item.id === id);
  if (repo) repo[key] = checked ? 1 : 0;
  toast(checked ? "已开启：本周报告将读取该项" : "已关闭：本周报告不再读取该项");
}

function renderBranchPicker(repo) {
  const selected = repo.tracked_branches && repo.tracked_branches.length ? repo.tracked_branches : ["main"];
  const options = branchOptionsFor(repo);
  const summary = trackedBranchSummary(repo);
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

// 项目计划 tab: objectives, project-level milestones and deliverables are
// edited here; workstream milestones are edited in each workstream's detail
// panel and only listed here so the whole plan reads in one place
function projectMilestones(ws) {
  return (ws.plan.milestones || []).filter((m) => !m.workstream_id);
}

function workstreamMilestoneRows(ws) {
  const order = new Map(workstreamList().map((item, index) => [item.id, index]));
  return (ws.plan.milestones || [])
    .filter((m) => m.workstream_id && order.has(Number(m.workstream_id)))
    .sort((a, b) => order.get(Number(a.workstream_id)) - order.get(Number(b.workstream_id))
      || String(a.target_date || "9999").localeCompare(String(b.target_date || "9999")))
    .map((m) => {
      const line = workstreamById(m.workstream_id);
      return `<tr>
        <td data-label="工作线"><button type="button" class="link-button" onclick="openWorkstreamFromOverview(${line.id})">${escapeHtml(line.path || line.name)}</button></td>
        <td data-label="里程碑">${escapeHtml(m.title || "")}</td>
        <td data-label="负责人">${escapeHtml(m.owner_label || "")}</td>
        <td data-label="日期">${escapeHtml(m.target_date || "")}</td>
        <td data-label="状态">${escapeHtml(statusLabel(m.status || ""))}</td>
      </tr>`;
    }).join("");
}

function renderPlan(ws) {
  const el = $("tab-plan");
  if (!el) return;
  const writable = canWriteWorkspace();
  const linkedRows = workstreamMilestoneRows(ws);
  const linked = linkedRows ? `
    <h3>工作线里程碑 <small>在工作线详情里编辑</small></h3>
    <table class="table plan-ws-milestones"><thead><tr><th>工作线</th><th>里程碑</th><th>负责人</th><th>日期</th><th>状态</th></tr></thead><tbody>${linkedRows}</tbody></table>` : "";
  el.innerHTML = writable ? `
    <form id="plan-form" class="panel">
      <div class="panel-head"><h2>项目计划</h2><span>目标、里程碑与交付物 · 修改后自动保存</span><span class="autosave-status" aria-live="polite"></span></div>
      ${textarea("objectives", "项目目标", ws.plan.objectives)}
      <div class="row plan-seed"><button type="button" onclick="seedWorkstreams()">按目标生成工作线</button><small>每个编号行生成一条工作线，缩进行或 1.1 编号生成子工作线，已有同名的跳过</small></div>
      <h3>项目级里程碑 <small>选择工作线后移到该工作线下</small></h3>
      <div id="milestones">${renderPlanItems(projectMilestones(ws), true)}</div>
      <button type="button" onclick="addPlanItem('milestones')">+ 添加里程碑</button>
      ${linked}
      <h3>交付物</h3>
      <div id="deliverables">${renderPlanItems(ws.plan.deliverables || [])}</div>
      <button type="button" onclick="addPlanItem('deliverables')">+ 添加交付物</button>
    </form>` : `
    <div class="panel">
      <div class="panel-head"><h2>项目计划</h2><span>只读</span></div>
      <p>${escapeHtml(ws.plan.objectives || "暂无目标。")}</p>
      <h3>项目级里程碑</h3>
      <table class="table"><tbody>${projectMilestones(ws).map(rowItem).join("") || "<tr><td>暂无项目级里程碑。</td></tr>"}</tbody></table>
      ${linked}
      <h3>交付物</h3>
      <table class="table"><tbody>${(ws.plan.deliverables || []).map(rowItem).join("") || "<tr><td>暂无交付物。</td></tr>"}</tbody></table>
    </div>`;
  if (writable) {
    $("plan-form").onsubmit = savePlan;
    setupAutoSave("plan", $("plan-form"), savePlan);
  }
  ensureTableScrollContainers();
}

function milestoneWorkstreamSelect(value) {
  const items = workstreamList();
  if (!items.length) return "";
  const current = String(value || "");
  return `<select name="workstream_id" aria-label="工作线"><option value="">项目级</option>${items.map((item) =>
    `<option value="${item.id}" ${String(item.id) === current ? "selected" : ""}>${item.parent_id ? "　└ " : ""}${escapeHtml(item.name)}</option>`).join("")}</select>`;
}

function renderPlanItems(items, withWorkstream = false) {
  return (items.length ? items : [{ title: "", status: "planned", owner_label: "", target_date: "" }]).map(item => `
    <div class="row plan-item">
      ${withWorkstream ? `<input type="hidden" name="id" value="${escapeAttr(item.id || "")}">` : ""}
      <input name="title" placeholder="标题" value="${escapeAttr(item.title || "")}">
      <input name="owner_label" list="project-member-names" placeholder="负责人" value="${escapeAttr(item.owner_label || "")}">
      <input name="target_date" type="date" value="${escapeAttr(item.target_date || "")}">
      <select name="status">${statusOptions(item.status)}</select>
      ${withWorkstream ? milestoneWorkstreamSelect(item.workstream_id) : ""}
      <button type="button" class="danger" onclick="this.closest('.plan-item').remove(); touchAutoSave('plan')">移除</button>
    </div>
  `).join("");
}

function addPlanItem(id) {
  $(id).insertAdjacentHTML("beforeend", renderPlanItems([{ title: "", status: "planned" }], id === "milestones"));
}

async function savePlan(event) {
  event?.preventDefault();
  const form = $("plan-form");
  if (!form) return;
  const groups = (id) => Array.from($(id).querySelectorAll(".plan-item")).map(row => itemPayload(row)).filter(i => i.title);
  const milestones = groups("milestones").map((item) => {
    const { id, workstream_id: workstreamId, ...rest } = item;
    return { ...rest, ...(Number(id) ? { id: Number(id) } : {}), ...(Number(workstreamId) ? { workstream_id: Number(workstreamId) } : {}) };
  });
  const deliverables = groups("deliverables");
  // only project-level milestones are sent; the server keeps every workstream's own
  const data = await api(`/api/projects/${state.projectId}/plan`, {
    method: "PUT",
    body: JSON.stringify({ objectives: form.objectives.value, project_milestones: milestones, deliverables }),
  });
  if (milestones.some((item) => item.workstream_id) && data && data.project) {
    // a milestone moved into a workstream: show it there and drop it from this list
    updateWorkspace(data);
    toast("里程碑已移到所选工作线");
    return;
  }
  if (state.workspace?.plan && data?.plan) {
    state.workspace.plan = data.plan;
    state.workspace.risks = data.risks || state.workspace.risks;
    state.workspace.progress_status = data.progress_status || state.workspace.progress_status;
    renderWorkstreamRisks(state.workspace);
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
  const writable = canWriteWorkspace();
  $("tab-updates").innerHTML = `
    ${writable ? `
    <form id="update-form" class="panel form-grid">
      <div class="panel-head wide"><h2>本周补充</h2><span>${escapeHtml(ws.week_key)} · 修改后自动保存</span><span class="autosave-status" aria-live="polite"></span></div>
      ${textarea("completed", "已完成", u.completed || "", "wide")}
      ${textarea("in_progress", "进行中", u.in_progress || "", "wide")}
      ${textarea("blockers", "阻塞事项", u.blockers || "", "wide")}
      ${textarea("risks", "风险", u.risks || "", "wide")}
      ${textarea("next_steps", "下一步计划", u.next_steps || "", "wide")}
    </form>` : `
    <div class="panel">
      <div class="panel-head"><h2>本周补充</h2><span>${escapeHtml(ws.week_key)} · 只读</span></div>
      ${supplementFieldsHtml(u) || "<p>本周还没有填写补充内容。</p>"}
    </div>`}
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
  if (writable) {
    $("update-form").onsubmit = saveWeeklyUpdate;
    setupAutoSave("weekly-update", $("update-form"), saveWeeklyUpdate);
  }
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
  const writable = canUploadWorkspace();
  const manageable = canManageWorkspace();
  const wsFilter = sourceFilterActive();
  const visible = ws.materials.filter((m) => materialMatchesWorkstream(m, wsFilter));
  const filterHint = typeof wsFilter === "number" ? `<p class="share-readonly-hint">当前筛选「${escapeHtml(workstreamById(wsFilter).name)}」：新增资料会归到这条工作线。</p>` : "";
  $("tab-sources").innerHTML = `
    <div class="source-toolbar">
      <div class="source-tabs" role="tablist" aria-label="资料类型">
        <button type="button" data-source-tab="manual" role="tab" onclick="switchSourceTab('manual')">手工资料</button>
        <button type="button" data-source-tab="files" role="tab" onclick="switchSourceTab('files')">文件资料</button>
      </div>
      ${renderWorkstreamFilter(ws)}
    </div>
    <section id="source-files" class="source-view" role="tabpanel">
      <div class="panel source-panel">
        <div class="panel-head"><h2>文件资料</h2><span>本周新增资料会进入生成上下文</span></div>
        ${writable ? `
        <label id="material-dropzone" class="upload-dropzone" for="material-file" role="button" tabindex="0">
          <input id="material-file" class="visually-hidden" type="file" accept=".md,.markdown,.txt,.html,.htm,.pdf,.xlsx,.xls,.docx,.doc,.png,.jpg,.jpeg,.gif,.webp" multiple>
          <span class="upload-icon" aria-hidden="true">↑</span>
          <strong>拖入文件，或点击选择</strong>
          <span id="material-selection">支持 Markdown、纯文本、HTML、PDF、Excel、Word 和图片，可多选</span>
        </label>
        ${filterHint}
        <div class="upload-actions">
          <button class="primary" type="button" onclick="uploadMaterial()">上传所选文件</button>
        </div>` : `<p class="share-readonly-hint">只读权限：可预览和下载资料，需要上传资料权限才能上传。</p>`}
        <table class="table material-table"><thead><tr><th>文件</th><th>提取</th><th>摘要</th><th>更新时间</th><th>操作</th></tr></thead><tbody>${visible.filter(m => m.source_type !== "manual").map((m) => renderUploadedMaterialRow(m, writable, manageable)).join("") || "<tr><td colspan='5'>暂无上传资料。</td></tr>"}</tbody></table>
      </div>
    </section>
    <section id="source-manual" class="source-view hidden" role="tabpanel">
      <div class="panel source-panel">
        <div class="panel-head"><h2>手工资料</h2><span>仅本周录入的资料可以修改 · 修改后自动保存</span><span class="autosave-status" aria-live="polite"></span></div>
        ${writable ? `
        <div class="manual-material-form" id="manual-material-form">
          <input id="manual-material-title" placeholder="资料标题" onkeydown="if (event.key === 'Enter') addManualMaterial()">
          <textarea id="manual-material-content" placeholder="输入本周新增的背景、决策、会议记录或补充资料"></textarea>
          <div class="manual-material-actions"><button class="primary" type="button" onclick="addManualMaterial()">添加资料</button></div>
        </div>${filterHint}` : `<p class="share-readonly-hint">只读权限：手工资料仅供查看。</p>`}
        <table class="table"><thead><tr><th>标题</th><th>内容</th><th>创建时间</th><th>更新时间</th><th>操作</th></tr></thead><tbody>${visible.filter(m => m.source_type === "manual").map((m) => renderManualMaterialRow(m, writable, manageable)).join("") || "<tr><td colspan='5'>暂无手工资料。</td></tr>"}</tbody></table>
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
    : "支持 Markdown、纯文本、HTML、PDF、Excel、Word 和图片，可多选";
}

function downloadMaterial(id) {
  const link = document.createElement("a");
  link.href = `/api/projects/${state.projectId}/materials/${id}/download`;
  link.download = "";
  document.body.appendChild(link);
  link.click();
  link.remove();
}

function renderUploadedMaterialRow(m, writable = true, manageable = true) {
  const extractionMessage = m.extraction_error ? `<div class="material-message">${escapeHtml(m.extraction_error)}</div>` : "";
  const summaryMessage = m.summary_error ? `<div class="material-message">AI 摘要失败，当前显示回退摘要：${escapeHtml(m.summary_error)}</div>` : "";
  return `<tr>
    <td data-label="文件"><strong>${escapeHtml(m.filename)}</strong><small>${formatBytes(m.size_bytes)}</small>${materialWorkstreamTag(m, writable)}</td>
    <td data-label="提取"><span class="status ${m.extraction_status}">${escapeHtml(m.extraction_status)}</span>${extractionMessage}</td>
    <td data-label="摘要">${writable
      ? `<textarea id="material-summary-${m.id}" class="table-textarea summary-editor">${escapeHtml(m.summary || "")}</textarea>${summaryMessage}`
      : `<div class="locked-material">${escapeHtml(m.summary || "")}</div>`}</td>
    <td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}<small><span class="status ${m.summary_status}">${escapeHtml(m.summary_status)}</span></small></td>
    <td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button><button type="button" onclick="downloadMaterial(${m.id})">下载</button>${manageable && m.deletable ? `<button class="danger" onclick="deleteMaterial(${m.id})">删除</button>` : ""}</div></td>
  </tr>`;
}

function renderManualMaterialRow(m, writable = true, manageable = true) {
  const content = escapeHtml(m.content || "");
  if (writable && m.editable) {
    return `<tr><td data-label="标题"><input id="manual-title-${m.id}" value="${escapeAttr(m.filename)}">${materialWorkstreamTag(m, writable)}</td><td data-label="内容"><textarea id="manual-content-${m.id}" class="table-textarea material-editor">${content}</textarea></td><td data-label="创建时间">${escapeHtml(formatChinaTime(m.created_at))}</td><td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}</td><td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button>${manageable ? `<button class="danger" onclick="deleteMaterial(${m.id})">删除</button>` : ""}</div></td></tr>`;
  }
  if (m.editable) {
    return `<tr><td data-label="标题">${escapeHtml(m.filename)}${materialWorkstreamTag(m, writable)}</td><td data-label="内容"><div class="locked-material">${content}</div></td><td data-label="创建时间">${escapeHtml(formatChinaTime(m.created_at))}</td><td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}</td><td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button></div></td></tr>`;
  }
  return `<tr><td data-label="标题">${escapeHtml(m.filename)}${materialWorkstreamTag(m, writable)}</td><td data-label="内容"><div class="locked-material">${content}</div></td><td data-label="创建时间">${escapeHtml(formatChinaTime(m.created_at))}</td><td data-label="更新时间">${escapeHtml(formatChinaTime(m.updated_at))}</td><td data-label="操作"><div class="table-actions"><button onclick="previewMaterial(${m.id})">预览</button><span class="status">已锁定</span></div></td></tr>`;
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
    } else if (material.preview_kind === "image") {
      const image = $("material-preview-image");
      image.alt = material.filename;
      image.src = `/api/projects/${state.projectId}/materials/${id}/content`;
      image.classList.remove("hidden");
      $("material-preview-body").classList.add("preview-body-stack");
      if (material.content_html) {
        const markdown = $("material-preview-markdown");
        markdown.innerHTML = material.content_html;
        markdown.classList.remove("hidden");
      }
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
  const image = $("material-preview-image");
  text.textContent = "";
  markdown.innerHTML = "";
  $("material-preview-body").classList.remove("preview-body-stack");
  pdf.removeAttribute("src");
  pdf.removeAttribute("srcdoc");
  pdf.removeAttribute("sandbox");
  image.removeAttribute("src");
  image.alt = "";
  [text, markdown, pdf, image].forEach((element) => element.classList.add("hidden"));
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
    const wsFilter = sourceFilterActive();
    const body = { files: payloads };
    if (typeof wsFilter === "number") body.workstream_id = wsFilter;
    await api(`/api/projects/${state.projectId}/materials`, { method: "POST", body: JSON.stringify(body) });
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
    body: JSON.stringify({ source_type: "manual", title, content, ...(typeof sourceFilterActive() === "number" ? { workstream_id: sourceFilterActive() } : {}) }),
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
  // 保存成功后同步 picker 摘要，否则已选分支与显示不一致，看起来像没保存
  const picker = $(`branch-picker-${id}`);
  if (picker) {
    const summary = picker.querySelector("summary");
    if (summary) summary.textContent = branches.includes(TRACK_ALL_BRANCHES) ? "All" : branches.join(", ");
  }
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
        <div class="panel-title"><h2>当前周报</h2>${ws.report && ws.report.edited_at ? '<span class="status edited">已手工调整</span>' : ""}<span>最近一次成功生成的 Markdown</span></div>
        <div class="panel-actions"><button type="button" onclick="toggleAssistant(true)">问助手</button>${ws.report ? `${canWriteWorkspace() ? `<button onclick="openReportEditor()">编辑</button>` : ""}<button onclick="exportReportPdf('${escapeAttr(ws.report.week_key)}')">导出 PDF</button>` : ""}</div>
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

function openReportEditor() {
  const ws = state.workspace;
  if (!ws || !ws.report) return;
  $("report-edit-context").textContent = `${ws.report.week_key} · 更新于 ${formatChinaTime(ws.report.updated_at)}`;
  $("report-edit-content").value = ws.report.content_md || "";
  const error = $("report-edit-error");
  error.textContent = "";
  error.classList.add("hidden");
  $("report-edit-dialog").showModal();
}

async function submitReportEdit(event) {
  event.preventDefault();
  const ws = state.workspace;
  if (!ws || !ws.report) return;
  const content = $("report-edit-content").value;
  const error = $("report-edit-error");
  error.textContent = "";
  error.classList.add("hidden");
  if (!content.trim()) {
    error.textContent = "周报内容不能为空。";
    error.classList.remove("hidden");
    return;
  }
  const submit = $("report-edit-submit");
  submit.disabled = true;
  try {
    const data = await api(`/api/projects/${state.projectId}/reports/${encodeURIComponent(ws.report.week_key)}`, {
      method: "PUT",
      body: JSON.stringify({ content_md: content }),
    });
    Object.assign(ws.report, {
      content_md: content,
      content_html: data.content_html,
      updated_at: data.updated_at,
      edited_at: data.edited_at,
    });
    $("report-edit-dialog").close();
    toast("周报已保存");
    render();
  } catch (exc) {
    error.textContent = exc.message || "保存失败，请重试。";
    error.classList.remove("hidden");
  } finally {
    submit.disabled = false;
  }
}

// —— 周报助手问答：每个账号在每个项目周一条对话，修改稿需确认后才写入周报 ——
const ASSISTANT_SUGGESTIONS = [
  "本周主要进展是什么？",
  "当前最大的风险是什么，原因是什么？",
  "周报里哪些结论缺少证据支撑？",
  "把本周总结改得更简洁",
];

function assistantVisible() {
  return state.assistantOpen && !state.settingsView && state.mode === "reports" && !!state.workspace;
}

function syncAssistantPanel() {
  const panel = $("assistant-panel");
  if (!panel) return;
  const visible = assistantVisible();
  panel.classList.toggle("hidden", !visible);
  if (document.body) document.body.classList.toggle("assistant-open", visible);
  const toggle = $("open-assistant");
  if (toggle) {
    toggle.classList.toggle("hidden", !state.workspace);
    toggle.classList.toggle("active", visible);
    if (toggle.setAttribute) toggle.setAttribute("aria-expanded", String(visible));
  }
  if (!visible) return;
  const ws = state.workspace;
  const staleWeek = state.assistant.weekKey && state.assistant.weekKey !== ws.week_key;
  if ((state.assistant.projectId !== ws.project.id || staleWeek) && !state.assistant.loading && !state.assistant.sending && !state.assistant.run) {
    loadAssistant();
    return;
  }
  renderAssistant();
}

function toggleAssistant(force) {
  state.assistantOpen = typeof force === "boolean" ? force : !state.assistantOpen;
  localStorage.setItem("assistantOpen", state.assistantOpen ? "1" : "0");
  syncAssistantPanel();
  if (state.assistantOpen) {
    const input = $("assistant-input");
    if (input && input.focus) input.focus();
  }
}

function setAssistantThread(projectId, data) {
  Object.assign(state.assistant, {
    projectId,
    weekKey: data.week_key || "",
    hasReport: !!data.has_report,
    messages: data.messages || [],
  });
}

async function loadAssistant() {
  const projectId = state.projectId;
  closeAssistantStream();
  state.assistant = { ...state.assistant, projectId, messages: [], loading: true, run: null, error: "" };
  renderAssistant();
  try {
    const data = await api(`/api/projects/${projectId}/assistant`);
    if (state.projectId !== projectId) return;
    setAssistantThread(projectId, data);
    // an answer still running (e.g. after a reload) streams in from the start
    if (data.active_run) startAssistantRun(projectId, data.active_run);
  } catch (err) {
    if (state.projectId === projectId) state.assistant.error = err.message;
  } finally {
    if (state.assistant.projectId === projectId) state.assistant.loading = false;
    if (state.projectId === projectId) renderAssistant();
  }
}

// —— 工作日志：参照 T3 Code 的时间线，思考 / 工具调用 / 中间说明按发生顺序一行一条，
// 运行中的行带微光和实时计时，完成后显示耗时；工具行可展开看原始参数与结果摘要 ——
const WORK_ICONS = {
  thinking: '<path d="M9.5 4.5a3 3 0 0 0-3 3v.2A3 3 0 0 0 4.5 10.5a3 3 0 0 0 1.2 2.4A3 3 0 0 0 8.5 17h1V4.5zM14.5 4.5a3 3 0 0 1 3 3v.2a3 3 0 0 1 2 2.8 3 3 0 0 1-1.2 2.4 3 3 0 0 1-2.8 4.1h-1V4.5z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
  tool: '<path d="M14.7 6.3a4 4 0 0 0-5.4 5.1l-5 5a1.5 1.5 0 0 0 2.1 2.1l5-5a4 4 0 0 0 5.1-5.4l-2.3 2.3-2.1-.6-.6-2.1z" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linejoin="round"/>',
  text: '<path d="M5 6.5h14M5 11h14M5 15.5h9" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
  working: '<circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.6"/><path d="M12 7.5V12l3 2" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>',
  chevron: '<path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>',
};

function workIcon(name) {
  return `<svg class="work-icon" viewBox="0 0 24 24" aria-hidden="true">${WORK_ICONS[name]}</svg>`;
}

function formatWorkDuration(ms) {
  if (ms === null || ms === undefined) return "";
  if (ms < 100) return `${Math.round(ms)}ms`;
  const seconds = ms / 1000;
  if (seconds < 10) return `${seconds.toFixed(1)}s`;
  if (seconds < 60) return `${Math.floor(seconds)}s`;
  return `${Math.floor(seconds / 60)}m ${String(Math.floor(seconds % 60)).padStart(2, "0")}s`;
}

function workArgsText(args) {
  const text = JSON.stringify(args || {});
  return text === "{}" ? "" : text;
}

// a running row shows a ticking timer measured from its server-side start t
function workTimer(item, live, extraClass = "") {
  if (!live) return `<span class="work-time ${extraClass}">${escapeHtml(formatWorkDuration(item.ms))}</span>`;
  return `<span class="work-time ${extraClass}" data-work-since="${item.t}">${escapeHtml(formatWorkDuration(assistantLiveMs(item.t)))}</span>`;
}

function workRowHtml(item, live) {
  if (item.kind === "thinking") {
    const running = live && item.ms === undefined;
    return `<div class="work-row${running ? " is-live" : ""}">${workIcon("thinking")}<span class="work-label">${running ? "思考中" : "思考"}</span>${workTimer(item, running)}</div>`;
  }
  if (item.kind === "text") {
    return `<div class="work-row is-note">${workIcon("text")}<span class="work-label">${escapeHtml(item.text)}</span></div>`;
  }
  const running = live && item.ms === undefined;
  const args = workArgsText(item.args);
  const status = item.error ? '<span class="work-fail" aria-label="工具调用失败">✕</span>' : "";
  const detail = `<pre class="work-detail">${escapeHtml(`${item.name} ${args || "{}"}`)}${item.preview !== undefined ? `\n\n${escapeHtml(item.preview)}${(item.chars || 0) > (item.preview || "").length ? "\n…" : ""}` : ""}</pre>`;
  return `
    <details class="work-row is-tool${running ? " is-live" : ""}${item.error ? " is-error" : ""}" data-key="${escapeAttr(item.id || "")}">
      <summary>${workIcon("tool")}<span class="work-label"><code>${escapeHtml(item.name)}</code>${args ? ` <span class="work-args">${escapeHtml(args)}</span>` : ""}</span>${status}${workTimer(item, running)}${workIcon("chevron")}</summary>
      ${detail}
    </details>`;
}

function workLogHtml(work, options = {}) {
  const items = (work && work.items) || [];
  const live = !!options.live;
  if (!items.length && !live) return "";
  const tools = items.filter((item) => item.kind === "tool").length;
  const count = tools ? ` · ${tools} 次工具调用` : "";
  const head = live
    ? `${workIcon("working")}<span class="work-label">工作中</span><span class="work-time" data-work-since="0">${escapeHtml(formatWorkDuration(assistantLiveMs(0)))}</span>`
    : `${workIcon("working")}<span class="work-label">已工作 ${escapeHtml(formatWorkDuration(work.elapsed_ms) || "")}${count}</span>${workIcon("chevron")}`;
  const rows = items.map((item) => workRowHtml(item, live)).join("");
  if (live) return `<div class="work-log is-live"><div class="work-head">${head}</div><div class="work-rows">${rows}</div></div>`;
  return `<details class="work-log"><summary class="work-head">${head}</summary><div class="work-rows">${rows}</div></details>`;
}

// 流式回答：提问创建后台 run，EventSource 订阅 round/text/tool_start/tool_end
// 事件，断线由浏览器带 Last-Event-ID 自动续传；同一轮的多个工具在服务端并行执行
const ASSISTANT_REPORT_MARKER = "<<<REPORT>>>";
let assistantStream = null;

function closeAssistantStream() {
  if (assistantStream) assistantStream.close();
  assistantStream = null;
  setAssistantTicker(false);
}

// server time (seconds since the run began) estimated from the last event
function assistantLiveMs(since) {
  const run = state.assistant.run;
  if (!run || run.clockOffset === undefined) return 0;
  return Math.max(0, (Date.now() / 1000 - run.clockOffset - since) * 1000);
}

function assistantLiveHtml(run) {
  // the trailing text item is the answer streaming in; earlier text became
  // interim notes when a tool call followed it
  const items = run.items.slice();
  const tail = items.length && items[items.length - 1].kind === "text" ? items.pop() : null;
  const text = tail ? tail.text : "";
  const marker = text.indexOf(ASSISTANT_REPORT_MARKER);
  const visible = (marker >= 0 ? text.slice(0, marker) : text).trim();
  const drafting = marker >= 0
    ? `<div class="assistant-drafting"><span class="spinner small" aria-hidden="true"></span><span>正在生成周报修改稿…（${text.length - marker} 字）</span></div>`
    : "";
  const stopping = run.stopping ? `<div class="assistant-drafting">正在停止…</div>` : "";
  const answer = visible || drafting || stopping
    ? `<div class="assistant-bubble">${visible ? `<div class="assistant-stream">${escapeHtml(visible)}<span class="assistant-caret" aria-hidden="true"></span></div>` : ""}${drafting}${stopping}</div>`
    : "";
  return `
    <div class="assistant-msg is-user"><div class="assistant-bubble">${escapeHtml(run.question)}</div></div>
    <div class="assistant-msg is-assistant" id="assistant-live">
      ${workLogHtml({ items }, { live: true })}
      ${answer}
    </div>`;
}

function tickAssistantTimers() {
  if (!state.assistant.run || !document.querySelectorAll) return;
  document.querySelectorAll("[data-work-since]").forEach((el) => {
    el.textContent = formatWorkDuration(assistantLiveMs(Number(el.dataset.workSince)));
  });
}

let assistantTicker = 0;

function setAssistantTicker(on) {
  if (typeof window === "undefined" || !window.setInterval) return;
  if (on && !assistantTicker) assistantTicker = window.setInterval(tickAssistantTimers, 500);
  if (!on && assistantTicker) {
    window.clearInterval(assistantTicker);
    assistantTicker = 0;
  }
}

let assistantLiveFrame = 0;

function renderAssistantLive() {
  // text deltas only touch the live bubble, batched per animation frame
  if (assistantLiveFrame) return;
  const paint = () => {
    assistantLiveFrame = 0;
    const run = state.assistant.run;
    const live = $("assistant-live");
    if (!run || !live || !live.parentElement) return renderAssistant();
    const box = $("assistant-messages");
    const pinned = box.scrollHeight - box.scrollTop - box.clientHeight < 48;
    // keep expanded tool rows open across repaints
    const open = new Set([...live.querySelectorAll("details[open]")].map((el) => el.dataset.key));
    const holder = document.createElement("div");
    holder.innerHTML = assistantLiveHtml(run);
    const next = holder.lastElementChild;
    next.querySelectorAll("details").forEach((el) => { if (open.has(el.dataset.key)) el.open = true; });
    live.replaceWith(next);
    if (pinned) box.scrollTop = box.scrollHeight;
  };
  if (typeof window !== "undefined" && window.requestAnimationFrame) {
    assistantLiveFrame = window.requestAnimationFrame(paint);
  } else {
    paint();
  }
}

function startAssistantRun(projectId, run) {
  closeAssistantStream();
  const a = state.assistant;
  a.run = { id: run.id, question: run.question, items: [], stopping: false, clockOffset: Date.now() / 1000 - (run.elapsed || 0) };
  setAssistantTicker(true);
  renderAssistant();
  if (typeof EventSource === "undefined") {
    a.error = "当前浏览器不支持流式输出";
    a.run = null;
    renderAssistant();
    return;
  }
  const source = new EventSource(`/api/projects/${projectId}/assistant/runs/${run.id}/events`);
  assistantStream = source;
  const current = () => (assistantStream === source && state.projectId === projectId ? a.run : null);
  const on = (type, handler) => source.addEventListener(type, (event) => {
    const live = current();
    if (!live) return;
    const data = JSON.parse(event.data || "{}");
    // keep the clock aligned with the server's run-relative timestamps
    if (typeof data.t === "number") live.clockOffset = Date.now() / 1000 - data.t;
    handler(live, data);
  });
  // mirror of the server's WorkRecorder: the same events build the same log
  const closeThinking = (live, t) => {
    const last = live.items[live.items.length - 1];
    if (last && last.kind === "thinking" && last.ms === undefined) last.ms = Math.max(0, (t - last.t) * 1000);
  };
  on("round", (live, data) => {
    closeThinking(live, data.t);
    live.items.push({ kind: "thinking", t: data.t });
    renderAssistantLive();
  });
  on("text", (live, data) => {
    closeThinking(live, data.t);
    const last = live.items[live.items.length - 1];
    if (last && last.kind === "text") last.text += data.delta || "";
    else live.items.push({ kind: "text", t: data.t, text: data.delta || "" });
    renderAssistantLive();
  });
  on("tool_start", (live, data) => {
    closeThinking(live, data.t);
    const last = live.items[live.items.length - 1];
    if (last && last.kind === "text") last.text = last.text.trim();
    live.items.push({ kind: "tool", t: data.t, id: data.id, name: data.name, args: data.args });
    renderAssistantLive();
  });
  on("tool_end", (live, data) => {
    const tool = live.items.find((item) => item.kind === "tool" && item.id === data.id && item.ms === undefined);
    if (tool) Object.assign(tool, { ms: data.ms, error: data.error, chars: data.chars, preview: data.preview });
    renderAssistantLive();
  });
  const finish = (live, message, restoreQuestion) => {
    closeAssistantStream();
    setAssistantTicker(false);
    a.run = null;
    if (message) a.error = message;
    renderAssistant();
    // a failed or stopped question goes back into the box for editing
    const input = $("assistant-input");
    if (restoreQuestion && input && !input.value) input.value = live.question;
  };
  on("done", (live, data) => {
    setAssistantThread(projectId, data);
    finish(live, "", false);
  });
  on("error", (live, data) => finish(live, data.message || "助手回答失败", true));
  on("cancelled", (live) => { finish(live, "", true); toast("已停止回答"); });
  source.onerror = () => {
    // CONNECTING: the browser retries with Last-Event-ID; CLOSED: the run is
    // gone (e.g. service restart), so resync the stored thread
    if (source.readyState === 2 && current()) {
      closeAssistantStream();
      loadAssistant();
    }
  };
}

async function stopAssistantRun() {
  const run = state.assistant.run;
  if (!run || run.stopping) return;
  run.stopping = true;
  renderAssistantLive();
  try {
    await api(`/api/projects/${state.projectId}/assistant/runs/${run.id}/cancel`, { method: "POST", body: "{}" });
  } catch (err) {
    run.stopping = false;
    toast(err.message);
  }
}

function assistantMessageHtml(message) {
  if (message.role === "user") {
    return `<div class="assistant-msg is-user"><div class="assistant-bubble">${escapeHtml(message.content)}</div></div>`;
  }
  return `<div class="assistant-msg is-assistant">${workLogHtml(message.work)}<div class="assistant-bubble assistant-md">${message.content_html}</div>${assistantProposalHtml(message)}</div>`;
}

function assistantProposalHtml(message) {
  const proposal = message.proposal;
  if (!proposal) return "";
  const applied = !!proposal.applied_at;
  const action = applied
    ? `<span class="assistant-proposal-note">已于 ${escapeHtml(formatChinaTime(proposal.applied_at))} 应用</span>`
    : canWriteWorkspace()
      ? `<button type="button" class="primary" onclick="applyAssistantProposal(${message.id}, this)">应用到周报</button>`
      : `<span class="assistant-proposal-note">只读权限，无法应用</span>`;
  return `
    <div class="assistant-proposal">
      <details>
        <summary><strong>周报修改稿</strong><span class="status ${applied ? "success" : "edited"}">${applied ? "已应用" : "待确认"}</span></summary>
        <article class="report assistant-md">${proposal.content_html}</article>
      </details>
      <div class="assistant-proposal-actions">${action}</div>
    </div>`;
}

function renderAssistant() {
  const box = $("assistant-messages");
  if (!box) return;
  const a = state.assistant;
  const ws = state.workspace;
  const context = $("assistant-context");
  if (context) context.textContent = ws ? `${ws.project.name} · ${a.weekKey || ws.week_key}` : "";
  const clear = $("assistant-clear");
  const busy = a.sending || !!a.run;
  if (clear) clear.disabled = busy || a.loading || !a.messages.length;
  const send = $("assistant-send");
  if (send) {
    send.disabled = a.sending || a.loading || !!(a.run && a.run.stopping);
    send.textContent = a.run ? "停止" : a.sending ? "提交中…" : "发送";
    send.classList.toggle("danger", !!a.run);
    send.classList.toggle("primary", !a.run);
  }
  const input = $("assistant-input");
  if (input) input.disabled = busy || a.loading;
  if (a.loading) {
    box.innerHTML = `<div class="assistant-empty"><span class="spinner small" aria-hidden="true"></span><span>正在加载对话…</span></div>`;
    return;
  }
  const parts = a.messages.map(assistantMessageHtml);
  if (a.run) parts.push(assistantLiveHtml(a.run));
  if (a.error) parts.push(`<div class="notice danger assistant-error"><span>${escapeHtml(a.error)}</span></div>`);
  if (!parts.length) {
    const hint = a.hasReport || (ws && ws.report) ? "" : `<p class="assistant-hint">本周还没有生成周报，可以先就本周资料提问。</p>`;
    parts.push(`
      <div class="assistant-empty">
        ${hint}
        <div class="assistant-suggestions">${ASSISTANT_SUGGESTIONS.map((q) => `<button type="button" data-assistant-suggestion="${escapeAttr(q)}">${escapeHtml(q)}</button>`).join("")}</div>
      </div>`);
  }
  box.innerHTML = parts.join("");
  box.scrollTop = box.scrollHeight;
}

async function sendAssistantQuestion(question) {
  const text = String(question || "").trim();
  const a = state.assistant;
  if (!text || a.sending || a.run || a.loading || !state.projectId) return;
  const projectId = state.projectId;
  Object.assign(a, { sending: true, error: "" });
  const input = $("assistant-input");
  if (input) input.value = "";
  renderAssistant();
  try {
    const data = await api(`/api/projects/${projectId}/assistant`, {
      method: "POST",
      body: JSON.stringify({ question: text }),
    });
    a.sending = false;
    if (state.projectId === projectId) startAssistantRun(projectId, data.run);
  } catch (err) {
    a.sending = false;
    if (state.projectId === projectId) {
      a.error = err.message;
      if (input && !input.value) input.value = text;
      renderAssistant();
    }
  }
}

async function applyAssistantProposal(messageId, button) {
  const ws = state.workspace;
  if (!ws) return;
  const warning = ws.report && ws.report.edited_at ? "当前周报已有手工修改，" : "";
  if (!window.confirm(`${warning}应用后将用这份修改稿替换本周周报正文，确定应用？`)) return;
  if (button) button.disabled = true;
  const projectId = state.projectId;
  try {
    const data = await api(`/api/projects/${projectId}/assistant/messages/${messageId}/apply`, { method: "POST", body: "{}" });
    if (state.projectId !== projectId) return;
    setAssistantThread(projectId, data);
    toast("修改稿已应用到周报");
    await loadWorkspace();
  } catch (err) {
    toast(err.message);
    if (button) button.disabled = false;
  }
}

async function clearAssistant() {
  const a = state.assistant;
  if (!state.projectId || a.sending || a.run || !a.messages.length) return;
  if (!window.confirm("清空本周与助手的全部对话？")) return;
  const projectId = state.projectId;
  try {
    const data = await api(`/api/projects/${projectId}/assistant`, { method: "DELETE" });
    if (state.projectId !== projectId) return;
    setAssistantThread(projectId, data);
    a.error = "";
    renderAssistant();
  } catch (err) {
    toast(err.message);
  }
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
    else if (kind === "workstreams") await workstreamJobFinished(id, job);
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
  const tasks = ((data && data.tasks) || []).filter((task) => ["report", "template", "workstreams"].includes(task.kind));
  if (!tasks.length) {
    bubble.classList.add("hidden");
    return;
  }
  const running = tasks.filter((task) => task.status === "running").length;
  const queued = tasks.length - running;
  const limits = data.parallelism && data.capacity ? `（并行 ${data.parallelism} · 上限 ${data.capacity}）` : "";
  bubble.classList.remove("hidden");
  bubble.innerHTML = `<small>任务队列：${running} 生成中 · ${queued} 排队${limits}</small>${tasks.map((task) =>
    `<span class="queue-task-line">${task.kind === "template" ? "模板 · " : task.kind === "workstreams" ? "工作线整理 · " : ""}${escapeHtml(statusLabel(task.status))} · ${escapeHtml(task.project_name || "")} ${escapeHtml(task.week_key || "")}</span>`).join("")}`;
}

function confirmProjectGeneration(projectId) {
  const project = state.projects.find((item) => item.id === projectId);
  if (!project) return;
  state.pendingReportProjectId = projectId;
  const edited = project.report_edited
    || (projectId === state.projectId && state.workspace && state.workspace.report && !!state.workspace.report.edited_at);
  $("report-confirm-edit-warning").classList.toggle("hidden", !edited);
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
$("workstream-form").onsubmit = submitWorkstreamForm;
$("cancel-workstream").onclick = () => $("workstream-dialog").close();
$("workstream-assign-form").onsubmit = submitWorkstreamAssign;
$("cancel-workstream-assign").onclick = () => $("workstream-assign-dialog").close();
$("open-assistant").onclick = () => toggleAssistant();
$("assistant-close").onclick = () => toggleAssistant(false);
$("assistant-clear").onclick = clearAssistant;
$("assistant-form").onsubmit = (event) => {
  event.preventDefault();
  if (state.assistant.run) stopAssistantRun();
  else sendAssistantQuestion($("assistant-input").value);
};
$("assistant-input").addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey || event.isComposing || event.keyCode === 229) return;
  event.preventDefault();
  sendAssistantQuestion(event.target.value);
});
$("assistant-messages").addEventListener("click", (event) => {
  const chip = event.target.closest("[data-assistant-suggestion]");
  if (chip) sendAssistantQuestion(chip.dataset.assistantSuggestion);
});
$("assistant-panel").addEventListener("keydown", (event) => {
  if (event.key === "Escape") toggleAssistant(false);
});
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
$("page-planet").onclick = () => warpAppMode();
document.querySelectorAll("[data-mode-tab]").forEach((btn) => btn.onclick = () => {
  const target = btn.dataset.modeTab;
  if (target === "settings") {
    toggleSettingsView();
    return;
  }
  switchAppMode(target);
});
$("open-global-settings").onclick = () => toggleSettingsView(true);
document.querySelectorAll("[data-global-settings-tab]").forEach((button) => {
  button.onclick = () => switchGlobalSettingsTab(button.dataset.globalSettingsTab);
  button.onkeydown = (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const buttons = [...button.parentElement.querySelectorAll("[data-global-settings-tab]")]
      .filter((item) => !item.classList.contains("hidden"));
    const current = buttons.indexOf(button);
    const index = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1
      : (current + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length;
    const next = buttons[index];
    switchGlobalSettingsTab(next.dataset.globalSettingsTab);
    next.focus();
    next.scrollIntoView({ block: "nearest", inline: "nearest" });
  };
});
setupAutoSave("voice-settings", $("voice-settings-panel"), saveVoiceSettings);
setupAutoSave("llm-settings", $("llm-settings-panel"), saveLlmSettings);
setupAutoSave("queue-settings", $("queue-settings-panel"), saveQueueSettings);
setupAutoSave("git-settings", $("git-settings-panel"), saveGitSettings);
setupAutoSave("backup-settings", $("backup-settings-panel"), saveBackupSettings);
$("backup-schedule-type-select").addEventListener("change", syncBackupScheduleFields);
$("backup-run-now").onclick = runBackupNow;
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
$("page-planet").onkeydown = (event) => {
  if (event.key === "Enter" || event.key === " ") {
    event.preventDefault();
    warpAppMode();
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
$("cancel-report-edit").onclick = () => $("report-edit-dialog").close();
$("report-edit-form").onsubmit = submitReportEdit;
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

function renderColdStorageSettings(data) {
  $("cold-storage-enabled-input").checked = !!data.cold_storage_enabled;
  $("cold-storage-target-dir-input").value = data.cold_storage_target_dir || "";
  $("cold-storage-status").textContent = data.cold_storage_last_error
    ? `最近转存异常：${data.cold_storage_last_error}`
    : data.cold_storage_last_run
      ? `最近检查：${formatChinaTime(data.cold_storage_last_run)} · 转存 ${data.cold_storage_last_count || 0} 个文件`
      : "尚未执行转存";
  refreshAutoSaveSnapshot("cold-storage-settings");
}

async function saveColdStorageSettings() {
  const data = await api("/api/settings", {
    method: "PUT",
    body: JSON.stringify({
      cold_storage_enabled: $("cold-storage-enabled-input").checked,
      cold_storage_target_dir: $("cold-storage-target-dir-input").value.trim(),
    }),
  });
  renderColdStorageSettings(data);
}

setupAutoSave("cold-storage-settings", $("cold-storage-settings-panel"), saveColdStorageSettings);
$("cold-storage-run-now").onclick = async () => {
  const button = $("cold-storage-run-now");
  button.disabled = true;
  button.textContent = "转存中…";
  try {
    await saveColdStorageSettings();
    if (!$("cold-storage-enabled-input").checked) throw new Error("请先启用冷存储");
    const data = await api("/api/cold-storage/run", { method: "POST" });
    renderColdStorageSettings(data);
    toast(data.cold_storage_last_error ? "转存完成，部分文件失败，请查看详情" : `已转存 ${data.cold_storage_last_count || 0} 个文件`);
  } catch (error) {
    toast(error.message);
  } finally {
    button.disabled = false;
    button.textContent = "立即转存";
  }
};

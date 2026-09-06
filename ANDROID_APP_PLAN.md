# Android 客户端规划（reports companion）

version: draft 1 · 2026-09-06

本地周报工作台目前只能通过手机浏览器访问自签 HTTPS 页面来完成语音 TODO。本规划定义一个原生
Android 客户端，覆盖语音记 TODO、TODO 看板、周报查看三类高频动作，并把"记一条 TODO"压缩到
锁屏/桌面一步可达。

## 1. 目标与非目标

**V1 目标**

- 一键录音 → 服务端 whisper 转写 + LLM 结构化 → 生成 TODO，替代手机浏览器麦克风方案
- TODO 看板查看与流转（待办/进行中/已关闭；关闭需填理由，可归档到项目）
- 周报按项目浏览、历史周报阅读、PDF 跳转
- 快捷入口：桌面长按快捷方式 + 快捷设置（QS）磁贴，直达录音页

**非目标（V1 不做）**

- 本地数据库 / 离线优先：直连本地服务，服务不可达时仅展示上次内存缓存并明确提示
- 素材上传、计划编辑、仓库配置、周报生成触发等管理工作台操作（继续用网页）
- iOS / 跨平台
- 公网访问、账号体系

## 2. 技术选型

| 项 | 选择 | 说明 |
| --- | --- | --- |
| 语言/UI | Kotlin + Jetpack Compose + Material3 | 麦克风、前台服务、QS Tile 等系统能力集成最好 |
| minSdk / target | 29 / 最新稳定 | 个人设备场景，不背旧系统包袱 |
| 网络 | OkHttp + Retrofit + kotlinx.serialization | 服务端已有 gzip，OkHttp 透明解压 |
| 设置存储 | DataStore (Preferences) | 服务器地址、证书指纹、上次项目 id |
| 录音 | AudioRecord（PCM 16kHz mono）→ 手工封 WAV | 见 §4.2，MediaRecorder 默认 AAC 不被接受 |
| 周报渲染 | 服务端渲染的 `content_html` + WebView 注入主题 CSS | 归档接口只返回 HTML（`content_md` 被服务端 pop 掉），且服务端渲染保真最高；CSS 跟随明暗主题 |
| DI / 架构 | 手写轻量 MVVM（ViewModel + Repository），不引 Hilt | 5 个屏的规模不值得引入 DI 框架 |
| 代码位置 | 本仓库 `android/` 子目录 | 单仓最简；后端接口演进同仓可见 |

## 3. 依赖的后端接口（现状，无需改动）

- `GET /api/state` — 项目列表 + 设置（首屏、连通性检查）
- `GET /api/todos` / `PUT /api/todos/{id}` / `POST /api/todos/{id}/close` / `DELETE` — 看板数据与状态流转，每次返回全量 `todos`
- `POST /api/todos/voice` — body 含 `audio_base64` + `content_type`；返回 `202 {id, status}`；**已有任务时返回 `409 {active_job_id}`**
- `GET /api/voice-jobs/active`、`GET /api/voice-jobs/{id}`（轮询）、`POST /api/voice-jobs/{id}/cancel`
- `GET /api/projects/{id}/workspace` — 含 `report`（本周，含 `content_md`/`content_html`）与 `report_history`（仅元数据，正文按需拉）
- `GET /api/projects/{id}/reports/{week_key}` — 归档周报正文；`.../pdf` — PDF 文件

## 4. 关键设计点

### 4.1 自签 HTTPS 信任

服务端 TLS 证书是 `data/tls/` 下自签的。方案：**证书固定（SPKI pin）**——首次引导时用户从服务端
复制证书 SHA-256 指纹粘贴进设置页，OkHttp 用自定义 `SSLSocketFactory`/`TrustManager` 只信任该
指纹；指纹换季（证书重新生成）时在设置页更新即可。不做全网信任兜底，避免中间人。

### 4.2 录音必须是 WAV（硬约束）

`asr.py` 的 `ALLOWED_ASR_AUDIO_TYPES` 只接受 **wav / mp3 / flac**，且 `MAX_ASR_AUDIO_BYTES = 25MB`。
`MediaRecorder` 输出的 AAC/m4a 会被 400 拒绝。因此：

- 用 `AudioRecord` 采 16 kHz / 单声道 / 16-bit PCM，停止时写 44 字节 WAV 头封装
- 16 kHz mono 16-bit ≈ 1.9 MB/分钟 → 25 MB 上限约 13 分钟，录音页展示时长并做软上限（如 10 分钟）
- 录音页在前台完成，规避 Android 11+ 后台麦克风的前台服务限制；V1 不做后台录音

### 4.3 语音任务轮询与互斥

服务端同一时刻只允许一个语音任务。状态机：

```
idle → recording → uploading → job(transcribing → structuring → done/failed/cancelled)
                        └─ 409 → conflict(展示进行中的任务，提供「查看/取消」)
```

- `202` 后每 2 s 轮询 `GET /api/voice-jobs/{id}`，指数退避到 5 s 封顶
- `done` 后拉 `GET /api/todos` 刷新，并高亮 `job.todo_ids` 里新生成的条目供确认
- 上传失败的录音先落 App 缓存目录，提供手动重试，避免白说一段话

### 4.4 看板同步

实际看板为三栏（待办/进行中/已关闭），"草稿"只是待办栏的快捷输入框。`PUT /api/todos/{id}` 仅在
todo/doing 间流转；关闭走 `POST /api/todos/{id}/close` 且 `reason` 必填（可带 `project_id` 归档为素材），
关闭后不可逆。所有变更响应都带全量 `todos`，客户端整体替换，不做乐观合并（单人使用无并发写冲突）。

### 4.5 快捷入口

- 动态快捷方式（长按图标）：「语音记 TODO」直达录音页
- `TileService` 快捷设置磁贴：下拉通知栏点磁贴 → 拉起 App 录音页
- 录音页常驻大按钮 + 握住说话交互，完成后一键返回

## 5. 页面规划

沿用 `DESIGN.md` 令牌：浅色工作台为主面，看板沿用反色深蓝面（board-* token），圆角 ~12px，
中文界面。

1. **引导/设置页** — 服务器地址（默认 `https://10.200.200.3:8443`）、证书指纹粘贴、连通性测试（`GET /api/state`）
2. **首页（项目 + 周报）** — 项目选择、本周周报摘要、周报历史列表
3. **周报阅读页** — Markdown 渲染、`is_current_week` 标识、右上角跳 PDF
4. **录音页** — 大录音按钮、波形/计时、上传与转写进度（transcribing → structuring）、结果确认
5. **看板页** — 三栏看板（待办/进行中/已关闭）左右滑动 + 点卡片流转，深色反色面，待办栏内置快捷输入

导航：底部两 Tab（周报 / 看板）+ 中央录音 FAB，录音页为全屏对话框层。

## 6. 工程结构

```
android/
  app/
    src/main/kotlin/net/cyberelf/reports/
      data/          # ApiService(Retrofit)、ReposData/StateData、证书 TrustManager
      voice/         # WavRecorder(AudioRecord)、VoiceJobPoller 状态机
      ui/            # settings/ home/ report/ record/ board/ + 主题(DESIGN.md token 映射)
      shortcuts/     # 动态快捷方式、ReportsTileService
      AppViewModel.kt
    src/test/        # 轮询状态机、WAV 头封装、repository(MockWebServer)
  gradle/libs.versions.toml
```

## 7. 里程碑

| 里程碑 | 内容 | 验收 |
| --- | --- | --- |
| M0 骨架 | 工程初始化、设置页 + 证书固定、`/api/state` 连通、项目列表 | 手机上能看到自己的项目 |
| M1 语音 TODO | WAV 录音、上传、轮询、409 互斥、失败重试、结果确认 | 说一段话生成正确 TODO |
| M2 看板 | 三栏看板、状态流转、关闭（必填理由）/删除、快捷新建 | 操作后与服务端列表一致 |
| M3 周报 | 周报历史 + Markdown 阅读 + PDF 跳转 | 通顺读完一周周报 |
| M4 快捷入口打磨 | 快捷方式、QS 磁贴、深色主题对齐、错误与空态 | 桌面两步内开始录音 |

## 8. 测试策略

- 单元测试：ViewModel 状态机（FakeApi + 虚拟时间，覆盖语音任务生命周期/看板操作/周报查看/设置流转）、轮询退避与 409 互斥、WAV 头字节、repository 用 MockWebServer 对齐真实接口形状
- 覆盖率：`./gradlew createDebugUnitTestCoverageReport`（JaCoCo XML/HTML 在 `app/build/reports/coverage/test/debug/`）；JVM 可测面（ViewModel + data 层）是覆盖重点
- 契约保障：后端 `tests/` 已覆盖 API；App 侧以快照式 fixture（真实响应 JSON 存 `src/test/resources`）防字段漂移
- 真机项（Compose UI、AudioRecord 录音循环、QS 磁贴）无法 JVM 单测，走真机验收清单

## 9. 风险与对策

| 风险 | 对策 |
| --- | --- |
| 证书重新生成导致 App 全挂 | 设置页一键更新指纹；连接失败时错误文案直指证书原因 |
| 服务端已有语音任务（网页端占住） | 409 显式态：展示进行中任务 + 取消入口，而非静默失败 |
| 录音编码不兼容 | 统一 WAV 16kHz mono；上传前校验字节数上限 |
| 后台被杀中断轮询 | 轮询放 ViewModel 协程；进程被杀后从「进行中任务」页恢复（`/active` 接口天然支持） |
| LLM 结构化耗时不可控 | structuring 阶段明确进度文案 + 可取消，超时提示改用网页 |

## 10. V2 备选（不承诺）

离线缓存（Room + 同步）、素材拍照上传、计划（plan）编辑、周报生成触发、KMP 共享出 iOS、
mDNS 自动发现服务地址。

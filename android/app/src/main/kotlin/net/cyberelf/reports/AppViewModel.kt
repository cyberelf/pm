package net.cyberelf.reports

import android.app.Application
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import net.cyberelf.reports.data.AppSettings
import net.cyberelf.reports.data.BoardRepository
import net.cyberelf.reports.data.BoardResult
import net.cyberelf.reports.data.CertTrust
import net.cyberelf.reports.data.ConnResult
import net.cyberelf.reports.data.ProjectDto
import net.cyberelf.reports.data.ReportsRepository
import net.cyberelf.reports.data.ServerUrl
import net.cyberelf.reports.data.SettingsStore
import net.cyberelf.reports.data.TodoDto
import net.cyberelf.reports.data.WorkspaceDto
import net.cyberelf.reports.data.VoiceRepository
import net.cyberelf.reports.data.VoiceSubmitResult
import net.cyberelf.reports.data.friendlyMessage
import net.cyberelf.reports.voice.WavRecorder
import android.content.Intent
import android.net.Uri
import java.io.File

sealed interface ConnectionUi {
    data object Idle : ConnectionUi
    data object Testing : ConnectionUi
    data class Online(val workspaceUser: String?) : ConnectionUi
    data class Offline(val message: String, val certProblem: Boolean) : ConnectionUi
}

sealed interface FingerprintProbe {
    data object Idle : FingerprintProbe
    data object Probing : FingerprintProbe
    data class Found(val fingerprint: String) : FingerprintProbe
    data class Failed(val message: String) : FingerprintProbe
}

/** Full-screen voice sheet state machine. The server runs one voice job at a
 *  time; a 409 on submit adopts the active job's progress instead of failing. */
sealed interface VoiceUi {
    data object Hidden : VoiceUi
    data object Ready : VoiceUi
    data class Recording(val seconds: Long, val amplitude: Int) : VoiceUi
    data object Uploading : VoiceUi
    data class Running(val jobId: Long, val stage: String, val adopted: Boolean) : VoiceUi
    data class Completed(
        val transcript: String,
        val newTodos: List<TodoDto>,
        val fallback: Boolean,
        val structuringError: String,
    ) : VoiceUi

    data object Cancelled : VoiceUi
    data class Failed(val message: String, val canRetryUpload: Boolean) : VoiceUi
}

data class ReportViewerUi(
    val weekKey: String,
    val html: String?,
    val isCurrent: Boolean,
    val loading: Boolean,
    val error: String? = null,
)

class AppViewModel(
    private val app: Application,
    private val repository: ReportsRepository,
    private val voiceRepository: VoiceRepository,
    private val boardRepository: BoardRepository,
) : ViewModel() {

    enum class Tab { Reports, Board }

    sealed interface Destination {
        data object Main : Destination
        data object Settings : Destination
    }

    data class UiState(
        val settings: AppSettings = AppSettings(),
        val ready: Boolean = false,
        val destination: Destination = Destination.Main,
        val tab: Tab = Tab.Reports,
        val connection: ConnectionUi = ConnectionUi.Idle,
        val projects: List<ProjectDto> = emptyList(),
        val selectedProjectId: Long? = null,
        val fingerprintProbe: FingerprintProbe = FingerprintProbe.Idle,
        val voice: VoiceUi = VoiceUi.Hidden,
        val finishedJobNotice: String? = null,
        val todos: List<TodoDto> = emptyList(),
        val todosLoaded: Boolean = false,
        val boardBusy: Boolean = false,
        val boardError: String? = null,
        val closingTodo: TodoDto? = null,
        val workspace: WorkspaceDto? = null,
        val workspaceLoading: Boolean = false,
        val workspaceError: String? = null,
        val reportViewer: ReportViewerUi? = null,
    ) {
        val selectedProject: ProjectDto?
            get() = projects.firstOrNull { it.id == selectedProjectId }
                ?: projects.firstOrNull()
    }

    private val mutableState = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = mutableState.asStateFlow()

    private var wavRecorder: WavRecorder? = null
    private var recordingTimer: Job? = null
    private var pollJob: Job? = null
    private var lastRecording: ByteArray? = null

    init {
        viewModelScope.launch {
            val saved = repository.currentSettings()
            mutableState.update { it.copy(settings = saved, ready = true) }
            // Silent reconnect on launch when a fingerprint is already stored.
            if (saved.certSha256.isNotBlank()) {
                connect(saved.serverUrl, saved.certSha256, silent = true)
            }
        }
    }

    fun openSettings() {
        mutableState.update {
            it.copy(destination = Destination.Settings, fingerprintProbe = FingerprintProbe.Idle)
        }
    }

    fun closeSettings() {
        mutableState.update { it.copy(destination = Destination.Main) }
    }

    fun selectTab(tab: Tab) {
        mutableState.update { it.copy(tab = tab) }
        if (tab == Tab.Board && !mutableState.value.todosLoaded) loadTodos()
    }

    // ---- Board ----

    fun loadTodos() {
        viewModelScope.launch {
            mutableState.update { it.copy(boardBusy = true) }
            try {
                val list = boardRepository.todos()
                mutableState.update { it.copy(todos = list, todosLoaded = true, boardBusy = false, boardError = null) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutableState.update { it.copy(boardBusy = false, boardError = friendlyMessage(e)) }
            }
        }
    }

    fun addTodo(title: String) {
        if (title.isBlank()) return
        boardAction { boardRepository.create(title) }
    }

    /** Moving into closed routes through the reason sheet; closing is final
     *  server-side and the reason is mandatory. */
    fun moveTodo(todo: TodoDto, toStatus: String) {
        if (toStatus == todo.status) return
        if (toStatus == "closed") {
            mutableState.update { it.copy(closingTodo = todo) }
        } else {
            boardAction { boardRepository.move(todo.id, toStatus) }
        }
    }

    fun confirmClose(reason: String, projectId: Long?) {
        val todo = mutableState.value.closingTodo ?: return
        if (reason.isBlank()) return
        boardAction { boardRepository.close(todo.id, reason.trim(), projectId) }
    }

    fun dismissCloseSheet() = mutableState.update { it.copy(closingTodo = null) }

    fun deleteTodo(todo: TodoDto) = boardAction { boardRepository.delete(todo.id) }

    fun clearBoardError() = mutableState.update { it.copy(boardError = null) }

    private fun boardAction(call: suspend () -> BoardResult) {
        if (mutableState.value.boardBusy) return
        mutableState.update { it.copy(boardBusy = true) }
        viewModelScope.launch {
            when (val result = call()) {
                is BoardResult.Success -> mutableState.update {
                    it.copy(
                        todos = result.todos,
                        todosLoaded = true,
                        boardBusy = false,
                        boardError = null,
                        closingTodo = null,
                    )
                }
                is BoardResult.Error -> mutableState.update {
                    it.copy(boardBusy = false, boardError = result.message)
                }
            }
        }
    }

    fun selectProject(id: Long) {
        mutableState.update { it.copy(selectedProjectId = id) }
        loadWorkspace(id)
    }

    // ---- Reports tab ----

    fun loadWorkspace(projectId: Long) {
        viewModelScope.launch {
            mutableState.update { it.copy(workspaceLoading = true, workspaceError = null) }
            val result = repository.workspace(projectId)
            mutableState.update { s ->
                if (s.selectedProjectId != projectId) return@update s // selection moved on; drop stale payload
                result.fold(
                    onSuccess = { s.copy(workspace = it, workspaceLoading = false, workspaceError = null) },
                    onFailure = { s.copy(workspaceLoading = false, workspaceError = friendlyMessage(it)) },
                )
            }
        }
    }

    /** Current week renders straight from the workspace payload; archived
     *  weeks are fetched on demand (server returns HTML only). */
    fun openReport(weekKey: String) {
        val current = mutableState.value
        val workspace = current.workspace ?: return
        if (weekKey == workspace.weekKey && workspace.report != null) {
            mutableState.update {
                it.copy(
                    reportViewer = ReportViewerUi(
                        weekKey = weekKey,
                        html = workspace.report.contentHtml,
                        isCurrent = true,
                        loading = false,
                    ),
                )
            }
            return
        }
        val projectId = current.selectedProjectId ?: return
        mutableState.update {
            it.copy(reportViewer = ReportViewerUi(weekKey, html = null, isCurrent = false, loading = true))
        }
        viewModelScope.launch {
            val result = repository.archivedReport(projectId, weekKey)
            mutableState.update { s ->
                val viewer = s.reportViewer ?: return@update s
                if (viewer.weekKey != weekKey) return@update s
                result.fold(
                    onSuccess = {
                        s.copy(reportViewer = viewer.copy(html = it.contentHtml, loading = false, isCurrent = it.isCurrentWeek))
                    },
                    onFailure = { s.copy(reportViewer = viewer.copy(loading = false, error = friendlyMessage(it))) },
                )
            }
        }
    }

    fun closeReportViewer() = mutableState.update { it.copy(reportViewer = null) }

    /** Opens the server-rendered PDF in a browser; the self-signed cert
     *  warning is accepted once per phone, same as the web flow. */
    fun openReportPdf() {
        val current = mutableState.value
        val viewer = current.reportViewer ?: return
        val project = current.workspace?.project ?: return
        val url = ServerUrl.normalize(current.settings.serverUrl) +
            "api/projects/${project.id}/reports/${viewer.weekKey}/pdf"
        try {
            app.startActivity(
                Intent(Intent.ACTION_VIEW, Uri.parse(url)).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
            )
        } catch (e: Exception) {
            mutableState.update { it.copy(finishedJobNotice = "无法打开 PDF：${e.message ?: "没有可用的浏览器"}") }
        }
    }

    /** Tests the entered settings; on success persists them. */
    fun saveAndConnect(serverUrl: String, certSha256: String) {
        if (mutableState.value.connection is ConnectionUi.Testing) return
        mutableState.update { it.copy(connection = ConnectionUi.Testing) }
        viewModelScope.launch {
            when (val result = repository.connect(serverUrl, certSha256)) {
                is ConnResult.Online -> {
                    val url = ServerUrl.normalize(serverUrl)
                    val fingerprint = normalizedFingerprint(certSha256)
                    repository.save(url, fingerprint)
                    mutableState.update {
                        it.copy(
                            settings = it.settings.copy(
                                serverUrl = url,
                                certSha256 = fingerprint,
                            ),
                            connection = ConnectionUi.Online(result.state.workspaceUser),
                            projects = result.state.projects,
                            selectedProjectId = result.state.projects.firstOrNull()?.id,
                            destination = Destination.Main,
                        )
                    }
                    loadWorkspaceIfMissing()
                }
                is ConnResult.Offline ->
                    mutableState.update { it.copy(connection = ConnectionUi.Offline(result.message, result.certProblem)) }
            }
        }
    }

    fun probeFingerprint(serverUrl: String) {
        mutableState.update { it.copy(fingerprintProbe = FingerprintProbe.Probing) }
        viewModelScope.launch {
            val result = repository.probeCertificateFingerprint(serverUrl)
            mutableState.update {
                it.copy(
                    fingerprintProbe = result.fold(
                        onSuccess = { FingerprintProbe.Found(it) },
                        onFailure = { FingerprintProbe.Failed(it.message ?: "无法获取证书") },
                    ),
                )
            }
        }
    }

    fun refresh() {
        val saved = mutableState.value.settings
        if (saved.certSha256.isNotBlank()) connect(saved.serverUrl, saved.certSha256, silent = true)
    }

    // ---- Voice sheet ----

    fun openVoice() {
        if (mutableState.value.voice != VoiceUi.Hidden) return
        mutableState.update { it.copy(voice = VoiceUi.Ready, finishedJobNotice = null) }
    }

    fun closeVoice() {
        // Recording: discard the take. A running server job keeps processing
        // remotely; its outcome lands in finishedJobNotice.
        runCatching {
            if (wavRecorder?.isRecording == true) wavRecorder?.stop()
        }
        wavRecorder = null
        recordingTimer?.cancel()
        recordingTimer = null
        lastRecording = null
        mutableState.update { it.copy(voice = VoiceUi.Hidden) }
    }

    fun dismissFinishedNotice() = mutableState.update { it.copy(finishedJobNotice = null) }

    fun startRecording() {
        if (mutableState.value.voice !is VoiceUi.Ready) return
        val recorder = WavRecorder { amplitude ->
            val voice = mutableState.value.voice
            if (voice is VoiceUi.Recording && voice.amplitude != amplitude) {
                mutableState.update { s ->
                    (s.voice as? VoiceUi.Recording)?.let { s.copy(voice = it.copy(amplitude = amplitude)) } ?: s
                }
            }
        }
        try {
            recorder.start()
        } catch (e: Exception) {
            mutableState.update { it.copy(voice = VoiceUi.Failed("无法开始录音：${e.message}", canRetryUpload = false)) }
            return
        }
        wavRecorder = recorder
        mutableState.update { it.copy(voice = VoiceUi.Recording(seconds = 0, amplitude = 0)) }
        recordingTimer = viewModelScope.launch {
            var seconds = 0L
            while (isActive) {
                delay(1_000)
                seconds += 1
                val voice = mutableState.value.voice
                if (voice !is VoiceUi.Recording) break
                if (seconds >= MAX_RECORDING_SECONDS) {
                    stopRecording()
                    break
                }
                mutableState.update { s ->
                    (s.voice as? VoiceUi.Recording)?.let { s.copy(voice = it.copy(seconds = seconds)) } ?: s
                }
            }
        }
    }

    fun stopRecording() {
        val recorder = wavRecorder ?: return
        recordingTimer?.cancel()
        recordingTimer = null
        val wav = try {
            recorder.stop()
        } catch (e: Exception) {
            mutableState.update { it.copy(voice = VoiceUi.Failed("录音失败：${e.message}", canRetryUpload = false)) }
            return
        } finally {
            wavRecorder = null
        }
        lastRecording = wav
        viewModelScope.launch {
            // Best-effort persistence so a retry survives the sheet closing.
            runCatching { File(app.cacheDir, CACHE_FILE_NAME).writeBytes(wav) }
        }
        upload { voiceRepository.submitAudio(wav) }
    }

    /** Text-only path ({"text": ...}) when the mic is unavailable. */
    fun submitText(text: String) {
        val trimmed = text.trim()
        if (trimmed.isEmpty()) return
        lastRecording = null
        upload { voiceRepository.submitText(trimmed) }
    }

    fun retryUpload() {
        val wav = lastRecording
            ?: runCatching { File(app.cacheDir, CACHE_FILE_NAME).takeIf { it.exists() }?.readBytes() }.getOrNull()
            ?: return
        upload { voiceRepository.submitAudio(wav) }
    }

    private fun upload(call: suspend () -> VoiceSubmitResult) {
        mutableState.update { it.copy(voice = VoiceUi.Uploading) }
        viewModelScope.launch {
            when (val result = call()) {
                is VoiceSubmitResult.Submitted -> watchJob(result.jobId, adopted = false)
                is VoiceSubmitResult.Conflict -> {
                    val activeId = result.activeJobId
                    if (activeId != null && activeId > 0) {
                        watchJob(activeId, adopted = true)
                    } else {
                        mutableState.update { it.copy(voice = VoiceUi.Failed(result.message, canRetryUpload = lastRecording != null)) }
                    }
                }
                is VoiceSubmitResult.Rejected ->
                    mutableState.update { it.copy(voice = VoiceUi.Failed(result.message, canRetryUpload = lastRecording != null)) }
            }
        }
    }

    /** Adopts an in-flight server job (409 takeover or re-open). */
    fun watchActiveJob() {
        viewModelScope.launch {
            try {
                val active = voiceRepository.activeJob()
                if (active != null) watchJob(active.id, adopted = true)
                else mutableState.update { it.copy(voice = VoiceUi.Ready) }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                mutableState.update { it.copy(voice = VoiceUi.Failed(friendlyMessage(e), canRetryUpload = false)) }
            }
        }
    }

    fun cancelJob() {
        val voice = mutableState.value.voice
        val jobId = (voice as? VoiceUi.Running)?.jobId ?: return
        viewModelScope.launch {
            voiceRepository.cancel(jobId)
            // Polling observes the cancelled terminal state; if the job had
            // already completed the poll surfaces that instead.
        }
    }

    private fun watchJob(jobId: Long, adopted: Boolean) {
        pollJob?.cancel()
        mutableState.update { it.copy(voice = VoiceUi.Running(jobId, stage = "transcribing", adopted = adopted)) }
        pollJob = viewModelScope.launch {
            val job = voiceRepository.pollUntilDone(jobId) { stage ->
                mutableState.update { s ->
                    (s.voice as? VoiceUi.Running)?.let { s.copy(voice = it.copy(stage = stage)) } ?: s
                }
            }
            when (job.status) {
                "completed" -> showCompleted(job.transcript, job.didFallback, job.error, job.todoIds)
                "failed" -> {
                    val message = job.error.ifBlank { "服务端处理失败" }
                    if (mutableState.value.voice == VoiceUi.Hidden) {
                        mutableState.update { it.copy(finishedJobNotice = "语音任务失败：$message") }
                    } else {
                        mutableState.update {
                            it.copy(voice = VoiceUi.Failed(message, canRetryUpload = lastRecording != null))
                        }
                    }
                }
                else -> if (mutableState.value.voice != VoiceUi.Hidden) {
                    mutableState.update { it.copy(voice = VoiceUi.Cancelled) }
                }
            }
        }
    }

    private suspend fun showCompleted(transcript: String, fallback: Boolean, structuringError: String, todoIds: List<Long>) {
        val newTodos = try {
            val all = voiceRepository.todos()
            if (todoIds.isEmpty()) emptyList() else all.filter { it.id in todoIds }
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            emptyList()
        }
        mutableState.update {
            if (it.voice == VoiceUi.Hidden) {
                // The sheet was closed while the job ran; surface a banner.
                it.copy(finishedJobNotice = "语音任务完成：生成 ${newTodos.size} 条 TODO")
            } else {
                it.copy(
                    voice = VoiceUi.Completed(transcript, newTodos, fallback, structuringError),
                    finishedJobNotice = null,
                )
            }
        }
    }

    private fun connect(serverUrl: String, certSha256: String, silent: Boolean) {
        if (mutableState.value.connection is ConnectionUi.Testing) return
        if (!silent) mutableState.update { it.copy(connection = ConnectionUi.Testing) }
        viewModelScope.launch {
            when (val result = repository.connect(serverUrl, certSha256)) {
                is ConnResult.Online -> {
                    mutableState.update {
                        it.copy(
                            connection = ConnectionUi.Online(result.state.workspaceUser),
                            projects = result.state.projects,
                            selectedProjectId = it.selectedProjectId
                                ?: result.state.projects.firstOrNull()?.id,
                        )
                    }
                    loadWorkspaceIfMissing()
                }
                is ConnResult.Offline -> mutableState.update {
                    it.copy(connection = ConnectionUi.Offline(result.message, result.certProblem))
                }
            }
        }
    }

    /** First workspace load after a successful connection. */
    private fun loadWorkspaceIfMissing() {
        val state = mutableState.value
        val projectId = state.selectedProjectId
        if (projectId != null && state.workspace == null && !state.workspaceLoading) {
            loadWorkspace(projectId)
        }
    }

    private fun normalizedFingerprint(raw: String): String = CertTrust.normalizeFingerprint(raw) ?: raw.trim()

    companion object {
        const val MAX_RECORDING_SECONDS = 600L // ~13 min is the server cap; stop earlier
        const val CACHE_FILE_NAME = "last_recording.wav"

        val Factory: ViewModelProvider.Factory = viewModelFactory {
            initializer {
                val app = this[ViewModelProvider.AndroidViewModelFactory.APPLICATION_KEY]!!
                val store = SettingsStore(app)
                AppViewModel(
                    app,
                    ReportsRepository(store),
                    VoiceRepository.fromSettings(store),
                    BoardRepository.fromSettings(store),
                )
            }
        }
    }
}

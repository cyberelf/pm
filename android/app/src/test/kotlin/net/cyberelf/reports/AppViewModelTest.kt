package net.cyberelf.reports

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import net.cyberelf.reports.data.AppSettings
import net.cyberelf.reports.data.CloseTodoRequest
import net.cyberelf.reports.data.ConnResult
import net.cyberelf.reports.data.CreateTodoRequest
import net.cyberelf.reports.data.MutationTodosResponse
import net.cyberelf.reports.data.ProjectDto
import net.cyberelf.reports.data.ReportsBackend
import net.cyberelf.reports.data.ReportDto
import net.cyberelf.reports.data.StateDto
import net.cyberelf.reports.data.TodoDto
import net.cyberelf.reports.data.TodosResponse
import net.cyberelf.reports.data.UpdateTodoRequest
import net.cyberelf.reports.data.VoiceJobDto
import net.cyberelf.reports.data.VoiceJobStartRequest
import net.cyberelf.reports.data.VoiceJobStartResponse
import net.cyberelf.reports.data.VoiceRepository
import net.cyberelf.reports.data.ActiveVoiceJobResponse
import net.cyberelf.reports.data.BoardRepository
import net.cyberelf.reports.data.ConflictResponse
import net.cyberelf.reports.data.WorkspaceDto
import net.cyberelf.reports.voice.VoiceRecorder
import okhttp3.MediaType.Companion.toMediaType
import retrofit2.Response
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import retrofit2.HttpException
import java.io.File

/** State-machine tests for the whole app ViewModel: voice job lifecycle with
 *  virtual-time polling, board mutations, report viewing, settings flow.
 *  Runs on an unconfined test dispatcher so viewModelScope launches execute
 *  eagerly and delays are virtual. */
class AppViewModelTest {

    private val mainDispatcher = UnconfinedTestDispatcher()

    @get:Rule
    val tmp = TemporaryFolder()

    @Before
    fun setUp() {
        Dispatchers.setMain(mainDispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    // ---- Fakes ----

    private class FakeApi : net.cyberelf.reports.data.ReportsApi {
        val calls = mutableListOf<String>()
        var state = StateDto()
        var workspace = WorkspaceDto()
        var archived = ReportDto(weekKey = "")
        var todos = TodosResponse()
        var createResult = MutationTodosResponse()
        var updateResult = MutationTodosResponse()
        var closeResult = MutationTodosResponse()
        var deleteResult = MutationTodosResponse()
        var updateFailure: HttpException? = null
        var closeFailure: HttpException? = null
        var startVoiceResponse: Response<VoiceJobStartResponse> =
            Response.success(VoiceJobStartResponse(1, "transcribing"))
        val jobQueue = ArrayDeque<VoiceJobDto>()
        val cancelledJobs = mutableListOf<Long>()

        override suspend fun state() = state

        override suspend fun workspace(id: Long): WorkspaceDto {
            calls += "GET workspace/$id"
            return workspace
        }

        override suspend fun archivedReport(id: Long, weekKey: String): ReportDto {
            calls += "GET archived/$weekKey"
            return archived
        }

        override suspend fun todos(): TodosResponse {
            calls += "GET todos"
            return todos
        }

        override suspend fun createTodo(body: CreateTodoRequest): MutationTodosResponse {
            calls += "POST create ${body.title}"
            return createResult
        }

        override suspend fun updateTodo(id: Long, body: UpdateTodoRequest): MutationTodosResponse {
            calls += "PUT todo/$id status=${body.status}"
            updateFailure?.let { throw it }
            return updateResult
        }

        override suspend fun closeTodo(id: Long, body: CloseTodoRequest): MutationTodosResponse {
            calls += "POST close/$id reason=${body.reason} project=${body.projectId}"
            closeFailure?.let { throw it }
            return closeResult
        }

        override suspend fun deleteTodo(id: Long): MutationTodosResponse {
            calls += "DELETE todo/$id"
            return deleteResult
        }

        override suspend fun startVoiceJob(body: VoiceJobStartRequest): Response<VoiceJobStartResponse> {
            calls += "POST voice text=${body.text} audioLen=${body.audioBase64?.length}"
            return startVoiceResponse
        }

        override suspend fun activeVoiceJob() = ActiveVoiceJobResponse(null)

        override suspend fun voiceJob(id: Long): VoiceJobDto {
            calls += "GET job/$id"
            // Never spin forever if a test forgets to enqueue a terminal status.
            return jobQueue.removeFirstOrNull()
                ?: VoiceJobDto(id, "failed", error = "fake: job queue empty")
        }

        override suspend fun cancelVoiceJob(id: Long): Response<VoiceJobDto> {
            cancelledJobs += id
            return Response.success(VoiceJobDto(id, "cancelled"))
        }
    }

    private class FakeBackend : ReportsBackend {
        var settings = AppSettings(serverUrl = "https://10.200.200.3:8443/", certSha256 = "")
        var connectResult: ConnResult =
            ConnResult.Online(StateDto(projects = listOf(ProjectDto(4, "周报项目", progressStatus = "on track"))))
        var workspaceResult: Result<WorkspaceDto> = Result.success(WorkspaceDto())
        var archivedResult: Result<ReportDto> = Result.success(ReportDto(weekKey = "2026-W30", contentHtml = "<p>old</p>"))
        var saved: Pair<String, String>? = null
        val workspaceCalls = mutableListOf<Long>()
        val archivedCalls = mutableListOf<String>()

        override suspend fun currentSettings(): AppSettings = settings

        override suspend fun connect(url: String, fingerprint: String): ConnResult = connectResult

        override suspend fun probeCertificateFingerprint(url: String): Result<String> =
            Result.success("ab".repeat(32))

        override suspend fun workspace(projectId: Long): Result<WorkspaceDto> {
            workspaceCalls += projectId
            return workspaceResult
        }

        override suspend fun archivedReport(projectId: Long, weekKey: String): Result<ReportDto> {
            archivedCalls += weekKey
            return archivedResult
        }

        override suspend fun save(serverUrl: String, certSha256: String) {
            saved = serverUrl to certSha256
        }
    }

    private class FakeRecorder : VoiceRecorder {
        var started = false
        var stopped = false
        override val isRecording: Boolean get() = started && !stopped
        override val recordedBytes: Int get() = 0
        override fun start() {
            started = true
        }

        override fun stop(): ByteArray {
            stopped = true
            return ByteArray(64) { 7 }
        }
    }

    private fun todo(id: Long, status: String = "todo") = TodoDto(
        id = id,
        title = "TODO $id",
        status = status,
    )

    private fun createVm(
        api: FakeApi,
        backend: FakeBackend = FakeBackend(),
        recorder: FakeRecorder? = null,
    ): Pair<AppViewModel, MutableList<android.content.Intent>> {
        val launched = mutableListOf<android.content.Intent>()
        val vm = AppViewModel(
            backend = backend,
            voiceRepository = VoiceRepository(
                apiProvider = { api },
                pollSleep = { delay(it) },
                ioDispatcher = kotlinx.coroutines.Dispatchers.Unconfined,
            ),
            boardRepository = BoardRepository(
                apiProvider = { api },
                ioDispatcher = kotlinx.coroutines.Dispatchers.Unconfined,
            ),
            cacheDir = tmp.root,
            startActivity = { launched += it },
            recorderFactory = { recorder ?: FakeRecorder() },
        )
        return vm to launched
    }

    private fun queuedJob(
        id: Long,
        status: String,
        transcript: String = "",
        todoIds: List<Long> = emptyList(),
        error: String = "",
    ) = VoiceJobDto(id = id, status = status, transcript = transcript, todoIds = todoIds, error = error)

    private fun errorResponse(code: Int, body: String): Response<VoiceJobStartResponse> =
        Response.error(code, body.toResponseBody("application/json".toMediaType()))

    private fun httpException(code: Int, body: String) = HttpException(errorResponse(code, body))

    // ---- Voice flow ----

    @Test
    fun `text submission runs to completion and lists generated todos`() {
        val api = FakeApi().apply {
            jobQueue += queuedJob(1, "transcribing")
            jobQueue += queuedJob(1, "completed", transcript = "写周报", todoIds = listOf(3, 9))
            todos = TodosResponse(listOf(todo(3), todo(5), todo(9)))
        }
        val (vm, _) = createVm(api)

        vm.openVoice()
        vm.submitText("写周报")
        mainDispatcher.scheduler.advanceUntilIdle()

        val voice = vm.state.value.voice
        assertTrue(voice is VoiceUi.Completed)
        voice as VoiceUi.Completed
        assertEquals("写周报", voice.transcript)
        assertEquals(listOf(3L, 9L), voice.newTodos.map { it.id })
        assertTrue(api.calls.contains("POST voice text=写周报 audioLen=null"))
    }

    @Test
    fun `blank text submission is ignored`() {
        val api = FakeApi()
        val (vm, _) = createVm(api)

        vm.openVoice()
        vm.submitText("   ")

        assertEquals(VoiceUi.Ready, vm.state.value.voice)
        assertTrue(api.calls.none { it.startsWith("POST voice") })
    }

    @Test
    fun `409 conflict adopts the active job instead of failing`() {
        val api = FakeApi().apply {
            startVoiceResponse = errorResponse(
                409,
                """{"error": "another voice job is already running", "active_job_id": 5}""",
            )
            jobQueue += queuedJob(5, "transcribing")
            jobQueue += queuedJob(5, "completed", todoIds = listOf(2))
            todos = TodosResponse(listOf(todo(2)))
        }
        val (vm, _) = createVm(api)

        vm.openVoice()
        vm.submitText("x")
        // Eager execution stops at the first poll delay: the takeover is visible.
        val running = vm.state.value.voice as VoiceUi.Running
        assertEquals(5L, running.jobId)
        assertTrue(running.adopted)

        mainDispatcher.scheduler.advanceUntilIdle()
        assertTrue(vm.state.value.voice is VoiceUi.Completed)
    }

    @Test
    fun `failed job surfaces the server error`() {
        val api = FakeApi().apply {
            jobQueue += queuedJob(1, "transcribing")
            jobQueue += queuedJob(1, "failed", error = "whisper 不可达")
        }
        val (vm, _) = createVm(api)

        vm.openVoice()
        vm.submitText("x")
        mainDispatcher.scheduler.advanceUntilIdle()

        val voice = vm.state.value.voice as VoiceUi.Failed
        assertEquals("whisper 不可达", voice.message)
        assertEquals(false, voice.canRetryUpload) // text path has nothing to retry
    }

    @Test
    fun `cancel requests the server and lands in cancelled`() {
        val api = FakeApi().apply {
            jobQueue += queuedJob(1, "transcribing")
            jobQueue += queuedJob(1, "cancelled")
        }
        val (vm, _) = createVm(api)

        vm.openVoice()
        vm.submitText("x")
        vm.cancelJob()
        mainDispatcher.scheduler.advanceUntilIdle()

        assertEquals(listOf(1L), api.cancelledJobs)
        assertEquals(VoiceUi.Cancelled, vm.state.value.voice)
    }

    @Test
    fun `closing the sheet mid-job surfaces a banner when the job completes`() {
        val api = FakeApi().apply {
            jobQueue += queuedJob(1, "transcribing")
            jobQueue += queuedJob(1, "transcribing")
            jobQueue += queuedJob(1, "completed", todoIds = listOf(1, 2))
            todos = TodosResponse(listOf(todo(1), todo(2)))
        }
        val (vm, _) = createVm(api)

        vm.openVoice()
        vm.submitText("x")
        vm.closeVoice()
        assertEquals(VoiceUi.Hidden, vm.state.value.voice)

        mainDispatcher.scheduler.advanceUntilIdle()
        assertEquals(VoiceUi.Hidden, vm.state.value.voice)
        assertTrue(vm.state.value.finishedJobNotice!!.contains("生成 2 条 TODO"))
    }

    @Test
    fun `recording stop uploads wav and persists a retry copy`() {
        val api = FakeApi().apply {
            jobQueue += queuedJob(1, "completed", todoIds = listOf(4))
            todos = TodosResponse(listOf(todo(4)))
        }
        val recorder = FakeRecorder()
        val (vm, _) = createVm(api, recorder = recorder)

        vm.openVoice()
        vm.startRecording()
        assertTrue(recorder.started)
        vm.stopRecording()
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(recorder.stopped)
        val voice = vm.state.value.voice as VoiceUi.Completed
        assertEquals(listOf(4L), voice.newTodos.map { it.id })
        val audioCall = api.calls.first { it.startsWith("POST voice") }
        assertTrue(audioCall.contains("audioLen=") && !audioCall.contains("audioLen=null"))
        assertEquals(64, File(tmp.root, AppViewModel.CACHE_FILE_NAME).length())
    }

    @Test
    fun `recording auto-stops at the 10 minute cap`() {
        val api = FakeApi().apply {
            jobQueue += queuedJob(1, "completed")
        }
        val recorder = FakeRecorder()
        val (vm, _) = createVm(api, recorder = recorder)

        vm.openVoice()
        vm.startRecording()
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(recorder.stopped)
        assertTrue(vm.state.value.voice is VoiceUi.Completed)
    }

    @Test
    fun `retry upload resubmits the cached recording`() {
        val api = FakeApi().apply {
            startVoiceResponse = errorResponse(500, "{}")
        }
        val recorder = FakeRecorder()
        val (vm, _) = createVm(api, recorder = recorder)

        vm.openVoice()
        vm.startRecording()
        vm.stopRecording()
        mainDispatcher.scheduler.advanceUntilIdle()
        assertTrue((vm.state.value.voice as VoiceUi.Failed).canRetryUpload)

        api.startVoiceResponse = Response.success(VoiceJobStartResponse(2, "transcribing"))
        api.jobQueue += queuedJob(2, "completed")
        vm.retryUpload()
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(vm.state.value.voice is VoiceUi.Completed)
    }

    // ---- Board ----

    @Test
    fun `opening the board tab loads todos once`() {
        val api = FakeApi().apply {
            todos = TodosResponse(listOf(todo(1, "todo"), todo(2, "doing")))
        }
        val (vm, _) = createVm(api)

        vm.selectTab(AppViewModel.Tab.Board)
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(vm.state.value.todosLoaded)
        assertEquals(listOf(1L, 2L), vm.state.value.todos.map { it.id })
    }

    @Test
    fun `add todo posts the trimmed title and replaces the list`() {
        val api = FakeApi().apply {
            createResult = MutationTodosResponse(todos = listOf(todo(7, "todo")))
        }
        val (vm, _) = createVm(api)

        vm.addTodo("  写周报  ")
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(api.calls.contains("POST create 写周报"))
        assertEquals(listOf(7L), vm.state.value.todos.map { it.id })
    }

    @Test
    fun `moving to doing sends a status-only put`() {
        val api = FakeApi().apply {
            todos = TodosResponse(listOf(todo(1, "todo")))
            updateResult = MutationTodosResponse(todos = listOf(todo(1, "doing")))
        }
        val (vm, _) = createVm(api)

        vm.selectTab(AppViewModel.Tab.Board)
        mainDispatcher.scheduler.advanceUntilIdle()
        vm.moveTodo(todo(1, "todo"), "doing")
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(api.calls.contains("PUT todo/1 status=doing"))
        assertEquals("doing", vm.state.value.todos.single().status)
    }

    @Test
    fun `moving into closed opens the reason sheet without a put`() {
        val api = FakeApi().apply { todos = TodosResponse(listOf(todo(1, "doing"))) }
        val (vm, _) = createVm(api)

        vm.selectTab(AppViewModel.Tab.Board)
        mainDispatcher.scheduler.advanceUntilIdle()
        vm.moveTodo(todo(1, "doing"), "closed")
        mainDispatcher.scheduler.advanceUntilIdle()

        assertEquals(1L, vm.state.value.closingTodo?.id)
        assertTrue(api.calls.none { it.startsWith("PUT") })
    }

    @Test
    fun `confirm close posts reason and clears the sheet`() {
        val api = FakeApi().apply {
            todos = TodosResponse(listOf(todo(1, "doing")))
            closeResult = MutationTodosResponse(materialId = 12, todos = listOf(todo(1, "closed")))
        }
        val (vm, _) = createVm(api)

        vm.selectTab(AppViewModel.Tab.Board)
        mainDispatcher.scheduler.advanceUntilIdle()
        vm.moveTodo(todo(1, "doing"), "closed")
        vm.confirmClose("本周完成", projectId = 4)
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(api.calls.contains("POST close/1 reason=本周完成 project=4"))
        assertNull(vm.state.value.closingTodo)
        assertEquals("closed", vm.state.value.todos.single().status)
    }

    @Test
    fun `close validation error keeps the sheet open with a message`() {
        val api = FakeApi().apply {
            todos = TodosResponse(listOf(todo(1, "doing")))
            closeFailure = httpException(400, """{"error": "close reason is required"}""")
        }
        val (vm, _) = createVm(api)

        vm.selectTab(AppViewModel.Tab.Board)
        mainDispatcher.scheduler.advanceUntilIdle()
        vm.moveTodo(todo(1, "doing"), "closed")
        vm.confirmClose("x", projectId = null)
        mainDispatcher.scheduler.advanceUntilIdle()

        assertEquals("close reason is required", vm.state.value.boardError)
        assertEquals(1L, vm.state.value.closingTodo?.id)
    }

    @Test
    fun `delete removes the todo via the api`() {
        val api = FakeApi().apply {
            todos = TodosResponse(listOf(todo(1)))
            deleteResult = MutationTodosResponse(todos = emptyList())
        }
        val (vm, _) = createVm(api)

        vm.selectTab(AppViewModel.Tab.Board)
        mainDispatcher.scheduler.advanceUntilIdle()
        vm.deleteTodo(todo(1))
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(api.calls.contains("DELETE todo/1"))
        assertTrue(vm.state.value.todos.isEmpty())
    }

    // ---- Connection & settings ----

    @Test
    fun `stored fingerprint auto-connects and loads the workspace on launch`() {
        val backend = FakeBackend().apply {
            settings = AppSettings(serverUrl = "https://10.200.200.3:8443/", certSha256 = "ab".repeat(32))
            workspaceResult = Result.success(WorkspaceDto(weekKey = "2026-W36"))
        }
        val (vm, _) = createVm(FakeApi(), backend)
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(vm.state.value.ready)
        assertTrue(vm.state.value.connection is ConnectionUi.Online)
        assertEquals(listOf(4L), backend.workspaceCalls)
        assertEquals("2026-W36", vm.state.value.workspace?.weekKey)
    }

    @Test
    fun `save and connect persists normalized url and fingerprint`() {
        val backend = FakeBackend()
        val (vm, _) = createVm(FakeApi(), backend)
        vm.openSettings()

        vm.saveAndConnect(" 10.200.200.3:8443 ", " " + "AB:".repeat(32) + " ")
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(vm.state.value.destination == AppViewModel.Destination.Main)
        assertTrue(vm.state.value.connection is ConnectionUi.Online)
        assertEquals("https://10.200.200.3:8443/", vm.state.value.settings.serverUrl)
        assertEquals("ab".repeat(32), vm.state.value.settings.certSha256)
        assertEquals("https://10.200.200.3:8443/" to "ab".repeat(32), backend.saved)
    }

    @Test
    fun `offline result stays on the settings screen without saving`() {
        val backend = FakeBackend().apply {
            connectResult = ConnResult.Offline("服务器证书不受信任：在设置里更新证书指纹", certProblem = true)
        }
        val (vm, _) = createVm(FakeApi(), backend)
        vm.openSettings()

        vm.saveAndConnect("https://10.200.200.3:8443", "ab".repeat(32))
        mainDispatcher.scheduler.advanceUntilIdle()

        val connection = vm.state.value.connection as ConnectionUi.Offline
        assertTrue(connection.certProblem)
        assertEquals(AppViewModel.Destination.Settings, vm.state.value.destination)
        assertNull(backend.saved)
    }

    // ---- Reports ----

    @Test
    fun `current week report renders from the workspace payload without a fetch`() {
        val backend = FakeBackend().apply {
            workspaceResult = Result.success(
                WorkspaceDto(
                    project = ProjectDto(4, "周报项目"),
                    weekKey = "2026-W36",
                    report = ReportDto(weekKey = "2026-W36", contentHtml = "<h1>本周</h1>"),
                    reportHistory = listOf(
                        ReportDto(weekKey = "2026-W36", isCurrentWeek = true),
                        ReportDto(weekKey = "2026-W35"),
                    ),
                ),
            )
        }
        val (vm, _) = createVm(FakeApi(), backend)
        mainDispatcher.scheduler.advanceUntilIdle()
        vm.selectProject(4)
        mainDispatcher.scheduler.advanceUntilIdle()

        vm.openReport("2026-W36")
        mainDispatcher.scheduler.advanceUntilIdle()

        val viewer = vm.state.value.reportViewer!!
        assertEquals("<h1>本周</h1>", viewer.html)
        assertTrue(viewer.isCurrent)
        assertTrue(backend.archivedCalls.isEmpty())
    }

    @Test
    fun `archived week is fetched on demand`() {
        val backend = FakeBackend()
        val (vm, _) = createVm(FakeApi(), backend)
        mainDispatcher.scheduler.advanceUntilIdle()
        vm.selectProject(4)
        mainDispatcher.scheduler.advanceUntilIdle()

        vm.openReport("2026-W35")
        mainDispatcher.scheduler.advanceUntilIdle()

        val viewer = vm.state.value.reportViewer!!
        assertEquals("<p>old</p>", viewer.html)
        assertEquals(false, viewer.isCurrent)
        assertEquals(listOf("2026-W35"), backend.archivedCalls)
    }

    @Test
    fun `archived fetch failure shows the error in the viewer`() {
        val backend = FakeBackend().apply {
            archivedResult = Result.failure(java.io.IOException("boom"))
        }
        val (vm, _) = createVm(FakeApi(), backend)
        mainDispatcher.scheduler.advanceUntilIdle()
        vm.selectProject(4)
        mainDispatcher.scheduler.advanceUntilIdle()

        vm.openReport("2026-W30")
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(vm.state.value.reportViewer!!.error!!.contains("网络错误"))
    }

    @Test
    fun `pdf url rule builds the server pdf endpoint`() {
        assertEquals(
            "https://10.200.200.3:8443/api/projects/4/reports/2026-W36/pdf",
            reportPdfUrl("https://10.200.200.3:8443", 4, "2026-W36"),
        )
        assertEquals(
            "https://10.200.200.3:8443/api/projects/7/reports/2025-W03/pdf",
            reportPdfUrl("10.200.200.3:8443", 7, "2025-W03"),
        )
    }

    @Test
    fun `pdf action does nothing without an open viewer`() {
        val (vm, launched) = createVm(FakeApi())
        mainDispatcher.scheduler.advanceUntilIdle()

        vm.openReportPdf()
        mainDispatcher.scheduler.advanceUntilIdle()

        assertTrue(launched.isEmpty())
    }
}

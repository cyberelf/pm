package net.cyberelf.reports

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import androidx.lifecycle.viewmodel.CreationExtras
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import net.cyberelf.reports.data.AppSettings
import net.cyberelf.reports.data.CertTrust
import net.cyberelf.reports.data.ConnResult
import net.cyberelf.reports.data.ProjectDto
import net.cyberelf.reports.data.ReportsRepository
import net.cyberelf.reports.data.ServerUrl

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

class AppViewModel(private val repository: ReportsRepository) : ViewModel() {

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
    ) {
        val selectedProject: ProjectDto?
            get() = projects.firstOrNull { it.id == selectedProjectId }
                ?: projects.firstOrNull()
    }

    private val mutableState = MutableStateFlow(UiState())
    val state: StateFlow<UiState> = mutableState.asStateFlow()

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

    fun selectTab(tab: Tab) = mutableState.update { it.copy(tab = tab) }

    fun selectProject(id: Long) = mutableState.update { it.copy(selectedProjectId = id) }

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

    private fun connect(serverUrl: String, certSha256: String, silent: Boolean) {
        if (mutableState.value.connection is ConnectionUi.Testing) return
        if (!silent) mutableState.update { it.copy(connection = ConnectionUi.Testing) }
        viewModelScope.launch {
            when (val result = repository.connect(serverUrl, certSha256)) {
                is ConnResult.Online -> mutableState.update {
                    it.copy(
                        connection = ConnectionUi.Online(result.state.workspaceUser),
                        projects = result.state.projects,
                        selectedProjectId = it.selectedProjectId
                            ?: result.state.projects.firstOrNull()?.id,
                    )
                }
                is ConnResult.Offline -> mutableState.update {
                    it.copy(connection = ConnectionUi.Offline(result.message, result.certProblem))
                }
            }
        }
    }

    private fun normalizedFingerprint(raw: String): String = CertTrust.normalizeFingerprint(raw) ?: raw.trim()

    companion object {
        val Factory: ViewModelProvider.Factory = viewModelFactory {
            initializer {
                val app = this[ViewModelProvider.AndroidViewModelFactory.APPLICATION_KEY]!!
                AppViewModel(ReportsRepository(net.cyberelf.reports.data.SettingsStore(app)))
            }
        }
    }
}

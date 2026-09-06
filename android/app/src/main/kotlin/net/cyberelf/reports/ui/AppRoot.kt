package net.cyberelf.reports.ui

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material.icons.outlined.ViewKanban
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FabPosition
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import net.cyberelf.reports.AppViewModel
import net.cyberelf.reports.ui.theme.ReportsTokens

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AppRoot(viewModel: AppViewModel = viewModel(factory = AppViewModel.Factory)) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    if (!state.ready) return

    if (state.destination == AppViewModel.Destination.Settings) {
        SettingsScreen(
            serverUrl = state.settings.serverUrl,
            certSha256 = state.settings.certSha256,
            connection = state.connection,
            fingerprintProbe = state.fingerprintProbe,
            onSaveAndConnect = viewModel::saveAndConnect,
            onProbeFingerprint = viewModel::probeFingerprint,
            onClose = viewModel::closeSettings,
        )
        return
    }

    val context = LocalContext.current
    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = { Text("周报工作台") },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background,
                ),
                actions = {
                    IconButton(onClick = viewModel::openSettings) {
                        Icon(Icons.Filled.Settings, contentDescription = "设置")
                    }
                },
            )
        },
        bottomBar = {
            NavigationBar(containerColor = MaterialTheme.colorScheme.surfaceContainerLow) {
                NavigationBarItem(
                    selected = state.tab == AppViewModel.Tab.Reports,
                    onClick = { viewModel.selectTab(AppViewModel.Tab.Reports) },
                    icon = { Icon(Icons.Outlined.Description, contentDescription = null) },
                    label = { Text("周报") },
                )
                NavigationBarItem(
                    selected = state.tab == AppViewModel.Tab.Board,
                    onClick = { viewModel.selectTab(AppViewModel.Tab.Board) },
                    icon = { Icon(Icons.Outlined.ViewKanban, contentDescription = null) },
                    label = { Text("看板") },
                )
            }
        },
        floatingActionButtonPosition = FabPosition.Center,
        floatingActionButton = {
            // M1 wires recording; until then the FAB renders as a disabled placeholder.
            FloatingActionButton(
                onClick = {},
                containerColor = ReportsTokens.primary,
                contentColor = MaterialTheme.colorScheme.onPrimary,
            ) {
                Icon(Icons.Filled.Mic, contentDescription = "语音记 TODO")
            }
        },
    ) { padding ->
        when (state.tab) {
            AppViewModel.Tab.Reports -> HomeScreen(
                connection = state.connection,
                projects = state.projects,
                selectedProjectId = state.selectedProject?.id,
                onSelectProject = viewModel::selectProject,
                onRetry = viewModel::refresh,
                onOpenSettings = viewModel::openSettings,
                modifier = Modifier.padding(padding),
            )
            AppViewModel.Tab.Board -> BoardScreen(
                modifier = Modifier.padding(padding),
            )
        }
    }
}

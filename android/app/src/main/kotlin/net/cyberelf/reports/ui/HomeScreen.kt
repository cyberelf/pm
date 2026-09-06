package net.cyberelf.reports.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import net.cyberelf.reports.AppViewModel
import net.cyberelf.reports.ConnectionUi
import net.cyberelf.reports.data.ProjectDto
import net.cyberelf.reports.ui.theme.ReportsTokens

private fun progressColor(status: String?): Color = when (status) {
    "blocked" -> ReportsTokens.error
    "at risk" -> ReportsTokens.warning
    "complete" -> ReportsTokens.success
    else -> ReportsTokens.brandAccent // "on track" and unknown
}

private fun progressLabel(status: String?): String = when (status) {
    "blocked" -> "受阻"
    "at risk" -> "有风险"
    "complete" -> "本周完成"
    "on track" -> "正常推进"
    else -> status ?: ""
}

@Composable
fun HomeScreen(
    connection: ConnectionUi,
    projects: List<ProjectDto>,
    selectedProjectId: Long?,
    onSelectProject: (Long) -> Unit,
    onRetry: () -> Unit,
    onOpenSettings: () -> Unit,
    modifier: Modifier = Modifier,
) {
    when (connection) {
        is ConnectionUi.Offline -> OfflinePane(connection, onRetry, onOpenSettings, modifier)
        ConnectionUi.Idle, ConnectionUi.Testing -> ConnectingPane(modifier)
        is ConnectionUi.Online -> ProjectList(projects, selectedProjectId, onSelectProject, modifier)
    }
}

@Composable
private fun ConnectingPane(modifier: Modifier) {
    Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Text("连接中…", style = MaterialTheme.typography.bodyLarge, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun OfflinePane(
    offline: ConnectionUi.Offline,
    onRetry: () -> Unit,
    onOpenSettings: () -> Unit,
    modifier: Modifier,
) {
    Column(
        modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Text(
            if (offline.certProblem) "证书未受信任" else "连接不上服务",
            style = MaterialTheme.typography.titleLarge,
            fontWeight = FontWeight.SemiBold,
        )
        Spacer(Modifier.height(8.dp))
        Text(
            offline.message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Spacer(Modifier.height(20.dp))
        Row {
            Button(
                onClick = onRetry,
                colors = ButtonDefaults.buttonColors(
                    containerColor = ReportsTokens.primary,
                    contentColor = Color.White,
                ),
                shape = RoundedCornerShape(10.dp),
            ) { Text("重试") }
            Spacer(Modifier.width(12.dp))
            TextButton(onClick = onOpenSettings) { Text(if (offline.certProblem) "更新证书指纹" else "检查设置") }
        }
    }
}

@Composable
private fun ProjectList(
    projects: List<ProjectDto>,
    selectedProjectId: Long?,
    onSelectProject: (Long) -> Unit,
    modifier: Modifier,
) {
    if (projects.isEmpty()) {
        Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text(
                "还没有项目，先到网页端创建",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        return
    }
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = androidx.compose.foundation.layout.PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        items(projects, key = { it.id }) { project ->
            ProjectCard(
                project = project,
                selected = project.id == selectedProjectId,
                onClick = { onSelectProject(project.id) },
            )
        }
    }
}

@Composable
private fun ProjectCard(project: ProjectDto, selected: Boolean, onClick: () -> Unit) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) MaterialTheme.colorScheme.surfaceContainerHigh
            else MaterialTheme.colorScheme.surfaceContainer,
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp),
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(
                    project.name,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                )
                if (project.description.isNotBlank()) {
                    Text(
                        project.description,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        maxLines = 1,
                    )
                }
            }
            Spacer(Modifier.width(10.dp))
            if (project.status == "paused") {
                Text(
                    "已暂停",
                    style = MaterialTheme.typography.labelMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Spacer(Modifier.width(8.dp))
            }
            Box(
                Modifier
                    .size(10.dp)
                    .background(progressColor(project.progressStatus), CircleShape),
            )
            Spacer(Modifier.width(6.dp))
            Text(
                progressLabel(project.progressStatus),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

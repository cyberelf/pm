package net.cyberelf.reports.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import net.cyberelf.reports.ConnectionUi
import net.cyberelf.reports.data.ProjectDto
import net.cyberelf.reports.data.ReportDto
import net.cyberelf.reports.data.WorkspaceDto
import net.cyberelf.reports.ui.theme.ReportsTokens

private fun progressColor(status: String?): Color = when (status) {
    "blocked" -> ReportsTokens.error
    "at risk" -> ReportsTokens.warning
    "complete" -> ReportsTokens.success
    else -> ReportsTokens.brandAccent // "on track" and unknown
}

@Composable
fun HomeScreen(
    connection: ConnectionUi,
    projects: List<ProjectDto>,
    selectedProjectId: Long?,
    workspace: WorkspaceDto?,
    workspaceLoading: Boolean,
    workspaceError: String?,
    onSelectProject: (Long) -> Unit,
    onOpenReport: (String) -> Unit,
    onRetry: () -> Unit,
    onOpenSettings: () -> Unit,
    modifier: Modifier = Modifier,
) {
    when (connection) {
        is ConnectionUi.Offline -> OfflinePane(connection, onRetry, onOpenSettings, modifier)
        ConnectionUi.Idle, ConnectionUi.Testing -> ConnectingPane(modifier)
        is ConnectionUi.Online -> {
            if (projects.isEmpty()) {
                Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text(
                        "还没有项目，先到网页端创建",
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            } else {
                Column(modifier.fillMaxSize()) {
                    ProjectSelector(projects, selectedProjectId, onSelectProject)
                    WorkspaceArea(workspace, workspaceLoading, workspaceError, onOpenReport, onRetry)
                }
            }
        }
    }
}

@Composable
private fun ProjectSelector(
    projects: List<ProjectDto>,
    selectedProjectId: Long?,
    onSelectProject: (Long) -> Unit,
) {
    Row(
        Modifier
            .fillMaxWidth()
            .horizontalScroll(rememberScrollState())
            .padding(horizontal = 16.dp, vertical = 4.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        projects.forEach { project ->
            val selected = project.id == selectedProjectId
            Surface(
                shape = RoundedCornerShape(999.dp),
                color = if (selected) ReportsTokens.primary else MaterialTheme.colorScheme.surfaceContainer,
                contentColor = if (selected) Color.White else MaterialTheme.colorScheme.onSurface,
                modifier = Modifier.clickable { onSelectProject(project.id) },
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 7.dp),
                ) {
                    Box(
                        Modifier
                            .size(7.dp)
                            .background(progressColor(project.progressStatus), CircleShape),
                    )
                    Spacer(Modifier.width(6.dp))
                    Text(project.name, style = MaterialTheme.typography.labelLarge, maxLines = 1)
                }
            }
        }
    }
}

@Composable
private fun WorkspaceArea(
    workspace: WorkspaceDto?,
    loading: Boolean,
    error: String?,
    onOpenReport: (String) -> Unit,
    onRetry: () -> Unit,
) {
    when {
        loading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator(color = ReportsTokens.primary)
        }
        error != null -> Box(Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Text(error, color = MaterialTheme.colorScheme.onSurfaceVariant, style = MaterialTheme.typography.bodyMedium)
                Spacer(Modifier.height(12.dp))
                Button(
                    onClick = onRetry,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = ReportsTokens.primary, contentColor = Color.White),
                ) { Text("重试") }
            }
        }
        workspace != null -> ReportLists(workspace, onOpenReport)
    }
}

@Composable
private fun ReportLists(workspace: WorkspaceDto, onOpenReport: (String) -> Unit) {
    LazyColumn(
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(10.dp),
    ) {
        val current = workspace.report
        item(key = "current") {
            if (current != null) {
                CurrentReportCard(current, onClick = { onOpenReport(current.weekKey) })
            } else {
                Card(
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainer),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(Modifier.padding(16.dp)) {
                        Text("本周周报", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
                        Spacer(Modifier.height(4.dp))
                        Text(
                            "本周周报尚未生成，可先在网页端触发",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
        if (workspace.reportHistory.isNotEmpty()) {
            item(key = "history-head") {
                Text(
                    "历史周报",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.padding(top = 8.dp),
                )
            }
            items(workspace.reportHistory, key = { it.weekKey }) { report ->
                HistoryRow(report, onClick = { onOpenReport(report.weekKey) })
            }
        }
    }
}

/** First readable lines of the markdown as the preview. */
private fun previewLine(markdown: String?): String =
    markdown
        ?.replace(Regex("[#*_`>\\[\\]]"), "")
        ?.lines()
        ?.filter { it.isNotBlank() }
        ?.take(2)
        ?.joinToString("  ")
        ?.take(120)
        ?: ""

@Composable
private fun CurrentReportCard(report: ReportDto, onClick: () -> Unit) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = ReportsTokens.primary, contentColor = Color.White),
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
    ) {
        Column(Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    "本周周报 · ${report.weekKey}",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    modifier = Modifier.weight(1f),
                )
                Icon(Icons.AutoMirrored.Filled.ArrowForward, contentDescription = "阅读", modifier = Modifier.size(18.dp))
            }
            Spacer(Modifier.height(6.dp))
            Text(
                previewLine(report.contentMd).ifBlank { "（暂无内容预览）" },
                style = MaterialTheme.typography.bodySmall,
                color = Color(0xFFD1D5DB),
                maxLines = 2,
                overflow = TextOverflow.Ellipsis,
            )
        }
    }
}

@Composable
private fun HistoryRow(report: ReportDto, onClick: () -> Unit) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.surfaceContainer),
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(horizontal = 16.dp, vertical = 12.dp),
        ) {
            Text(
                report.weekKey,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.weight(1f),
            )
            if (report.isCurrentWeek) {
                Surface(color = MaterialTheme.colorScheme.surfaceContainerHigh, shape = RoundedCornerShape(999.dp)) {
                    Text(
                        "本周",
                        style = MaterialTheme.typography.labelSmall,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                    )
                }
                Spacer(Modifier.width(8.dp))
            }
            Text(
                report.updatedAt?.take(10) ?: "",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
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

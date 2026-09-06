package net.cyberelf.reports.ui

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Mic
import androidx.compose.material.icons.filled.Stop
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import net.cyberelf.reports.VoiceUi
import net.cyberelf.reports.ui.theme.ReportsTokens

@Composable
fun RecordScreen(
    voice: VoiceUi,
    onStartRecording: () -> Unit,
    onStopRecording: () -> Unit,
    onSubmitText: (String) -> Unit,
    onRetryUpload: () -> Unit,
    onCancelJob: () -> Unit,
    onClose: () -> Unit,
) {
    Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Box(Modifier.fillMaxSize()) {
            IconButton(
                onClick = onClose,
                modifier = Modifier
                    .align(Alignment.TopEnd)
                    .padding(8.dp),
            ) {
                Icon(Icons.Filled.Close, contentDescription = "关闭")
            }
            Column(
                Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 24.dp)
                    .padding(top = 64.dp, bottom = 32.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
            ) {
                when (voice) {
                    VoiceUi.Hidden -> Unit
                    VoiceUi.Ready -> ReadyPane(onStartRecording, onSubmitText)
                    is VoiceUi.Recording -> RecordingPane(voice, onStopRecording)
                    VoiceUi.Uploading -> ProgressPane("上传录音中…")
                    is VoiceUi.Running -> RunningPane(voice, onCancelJob)
                    is VoiceUi.Completed -> CompletedPane(voice, onClose)
                    VoiceUi.Cancelled -> CancelledPane(onClose)
                    is VoiceUi.Failed -> FailedPane(voice, onRetryUpload, onClose)
                }
            }
        }
    }
}

@Composable
private fun ReadyPane(onStartRecording: () -> Unit, onSubmitText: (String) -> Unit) {
    val context = LocalContext.current
    var denied by remember { mutableStateOf(false) }
    var textMode by remember { mutableStateOf(false) }
    var text by remember { mutableStateOf("") }
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) onStartRecording() else denied = true
    }

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text("语音记 TODO", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(6.dp))
        Text(
            "说出今天做的事，服务端转写并整理成待办",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(40.dp))
        Box(
            Modifier
                .size(132.dp)
                .background(ReportsTokens.primary, CircleShape)
                .clickable {
                    if (ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO)
                        == PackageManager.PERMISSION_GRANTED
                    ) {
                        onStartRecording()
                    } else {
                        permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    }
                },
            contentAlignment = Alignment.Center,
        ) {
            Icon(
                Icons.Filled.Mic,
                contentDescription = "开始录音",
                tint = Color.White,
                modifier = Modifier.size(52.dp),
            )
        }
        if (denied) {
            Spacer(Modifier.height(12.dp))
            Text(
                "麦克风未授权；可重新授权或改用文字输入",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )
        }
        Spacer(Modifier.height(40.dp))

        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("文字输入模式", style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.width(8.dp))
            Switch(checked = textMode, onCheckedChange = { textMode = it })
        }
        if (textMode) {
            Spacer(Modifier.height(12.dp))
            OutlinedTextField(
                value = text,
                onValueChange = { text = it },
                placeholder = { Text("直接输入待办内容…") },
                minLines = 3,
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(10.dp))
            Button(
                onClick = { onSubmitText(text) },
                enabled = text.isNotBlank(),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(containerColor = ReportsTokens.primary, contentColor = Color.White),
            ) { Text("提交") }
        }
    }
}

@Composable
private fun RecordingPane(recording: VoiceUi.Recording, onStop: () -> Unit) {
    val pulse = rememberInfiniteTransition(label = "pulse")
    val scale by pulse.animateFloat(
        initialValue = 1f,
        targetValue = 1.06f,
        animationSpec = infiniteRepeatable(tween(700), RepeatMode.Reverse),
        label = "scale",
    )
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        Text(
            formatSeconds(recording.seconds),
            style = MaterialTheme.typography.displaySmall,
            fontWeight = FontWeight.SemiBold,
        )
        Spacer(Modifier.height(20.dp))
        AmplitudeBars(recording.amplitude)
        Spacer(Modifier.height(48.dp))
        Box(
            Modifier
                .size(96.dp)
                .graphicsLayer { scaleX = scale; scaleY = scale }
                .background(ReportsTokens.error, CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            IconButton(onClick = onStop) {
                Icon(Icons.Filled.Stop, contentDescription = "停止并转写", tint = Color.White, modifier = Modifier.size(40.dp))
            }
        }
        Spacer(Modifier.height(10.dp))
        Text("轻点停止并转写（最长 10 分钟）", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun AmplitudeBars(amplitude: Int) {
    val level = (amplitude / 100f).coerceIn(0f, 1f)
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp),
        modifier = Modifier.height(56.dp),
    ) {
        val weights = listOf(0.5f, 0.8f, 1f, 0.8f, 0.5f)
        weights.forEachIndexed { index, w ->
            val height = 8.dp + 44.dp * w * (if (index == 2) level else level * 0.7f)
            Box(
                Modifier
                    .width(8.dp)
                    .height(height)
                    .background(ReportsTokens.primary, RoundedCornerShape(4.dp)),
            )
        }
    }
}

@Composable
private fun ProgressPane(label: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        CircularProgressIndicator(color = ReportsTokens.primary)
        Spacer(Modifier.height(20.dp))
        Text(label, style = MaterialTheme.typography.bodyLarge)
    }
}

@Composable
private fun RunningPane(running: VoiceUi.Running, onCancelJob: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        if (running.adopted) {
            Text(
                "服务端已有任务在进行中，正在显示其进度",
                style = MaterialTheme.typography.bodySmall,
                color = ReportsTokens.warning,
            )
            Spacer(Modifier.height(8.dp))
        }
        ProgressPane(
            when (running.stage) {
                "queued" -> "排队等待中…"
                "structuring" -> "正在整理成 TODO…"
                "retrying" -> "网络波动，继续等待…"
                else -> "转写中…"
            },
        )
        Spacer(Modifier.height(28.dp))
        OutlinedButton(onClick = onCancelJob, shape = RoundedCornerShape(10.dp)) { Text("取消任务") }
        Spacer(Modifier.height(8.dp))
        Text(
            "转写与整理由服务端完成，通常需要几十秒",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

@Composable
private fun CompletedPane(completed: VoiceUi.Completed, onClose: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        Text("完成", style = MaterialTheme.typography.headlineSmall, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(16.dp))
        Surface(color = MaterialTheme.colorScheme.surfaceContainer, shape = RoundedCornerShape(12.dp)) {
            Text(
                completed.transcript.ifBlank { "（无转写文本）" },
                style = MaterialTheme.typography.bodyMedium,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(14.dp),
            )
        }
        Spacer(Modifier.height(16.dp))
        if (completed.fallback) {
            Text(
                "LLM 整理失败，已把原文存为一条 TODO" +
                    (completed.structuringError.takeIf { it.isNotBlank() }?.let { "：$it" } ?: ""),
                style = MaterialTheme.typography.bodySmall,
                color = ReportsTokens.warning,
            )
        } else {
            Text(
                "生成 ${completed.newTodos.size} 条 TODO",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.SemiBold,
            )
        }
        Spacer(Modifier.height(10.dp))
        completed.newTodos.forEach { todo ->
            Surface(
                color = MaterialTheme.colorScheme.surfaceContainer,
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
            ) {
                Column(Modifier.padding(horizontal = 14.dp, vertical = 10.dp)) {
                    Text(todo.title, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
                    if (todo.projectName != null) {
                        Text(
                            todo.projectName,
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
        Spacer(Modifier.height(24.dp))
        Button(
            onClick = onClose,
            shape = RoundedCornerShape(10.dp),
            colors = ButtonDefaults.buttonColors(containerColor = ReportsTokens.primary, contentColor = Color.White),
        ) { Text("完成") }
    }
}

@Composable
private fun CancelledPane(onClose: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        Text("任务已取消", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(20.dp))
        OutlinedButton(onClick = onClose, shape = RoundedCornerShape(10.dp)) { Text("关闭") }
    }
}

@Composable
private fun FailedPane(failed: VoiceUi.Failed, onRetry: () -> Unit, onClose: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
        Text("出错了", style = MaterialTheme.typography.titleLarge, fontWeight = FontWeight.SemiBold)
        Spacer(Modifier.height(10.dp))
        Text(
            failed.message,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            textAlign = TextAlign.Center,
        )
        Spacer(Modifier.height(24.dp))
        Row {
            if (failed.canRetryUpload) {
                Button(
                    onClick = onRetry,
                    shape = RoundedCornerShape(10.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = ReportsTokens.primary, contentColor = Color.White),
                ) { Text("重试上传") }
                Spacer(Modifier.width(12.dp))
            }
            OutlinedButton(onClick = onClose, shape = RoundedCornerShape(10.dp)) { Text("关闭") }
        }
    }
}

private fun formatSeconds(total: Long): String = "%d:%02d".format(total / 60, total % 60)

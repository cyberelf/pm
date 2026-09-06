package net.cyberelf.reports.ui

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import net.cyberelf.reports.ConnectionUi
import net.cyberelf.reports.FingerprintProbe
import net.cyberelf.reports.ui.theme.ReportsTokens

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    serverUrl: String,
    certSha256: String,
    connection: ConnectionUi,
    fingerprintProbe: FingerprintProbe,
    onSaveAndConnect: (url: String, fingerprint: String) -> Unit,
    onProbeFingerprint: (url: String) -> Unit,
    onClose: () -> Unit,
    modifier: Modifier = Modifier,
) {
    var url by remember(serverUrl) { mutableStateOf(serverUrl) }
    var fingerprint by remember(certSha256) { mutableStateOf(certSha256) }

    Scaffold(
        modifier = modifier,
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = { Text("服务器设置") },
                navigationIcon = {
                    IconButton(onClick = onClose) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                    }
                },
            )
        },
    ) { padding ->
        Column(
            Modifier
                .padding(padding)
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 20.dp),
        ) {
            FieldLabel("服务地址")
            OutlinedTextField(
                value = url,
                onValueChange = { url = it },
                singleLine = true,
                placeholder = { Text("https://10.200.200.3:8443") },
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(6.dp))
            Text(
                "手机需与服务端在同一网络；默认端口 8443 是自签 HTTPS。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(Modifier.height(20.dp))
            FieldLabel("证书指纹 (SHA-256)")
            OutlinedTextField(
                value = fingerprint,
                onValueChange = { fingerprint = it },
                singleLine = true,
                placeholder = { Text("粘贴服务器证书指纹，或点下方获取") },
                shape = RoundedCornerShape(10.dp),
                supportingText = {
                    if (fingerprintProbe is FingerprintProbe.Failed) {
                        Text("获取失败：${fingerprintProbe.message}", color = MaterialTheme.colorScheme.error)
                    } else {
                        Text("与服务端 `openssl x509 -in 证书.pem -noout -fingerprint -sha256` 输出一致")
                    }
                },
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(8.dp))
            OutlinedButton(
                onClick = { onProbeFingerprint(url) },
                enabled = fingerprintProbe !is FingerprintProbe.Probing && url.isNotBlank(),
                shape = RoundedCornerShape(10.dp),
            ) {
                Text(
                    when (fingerprintProbe) {
                        is FingerprintProbe.Probing -> "获取中…"
                        is FingerprintProbe.Found -> "重新获取证书指纹"
                        else -> "获取证书指纹"
                    },
                )
            }
            if (fingerprintProbe is FingerprintProbe.Found) {
                Spacer(Modifier.height(8.dp))
                Text(
                    fingerprintProbe.fingerprint,
                    style = MaterialTheme.typography.bodySmall.copy(fontFamily = FontFamily.Monospace),
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    "请与服务端输出核对后点「保存并连接」。",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            Spacer(Modifier.height(28.dp))
            if (connection is ConnectionUi.Offline) {
                Text(
                    connection.message,
                    color = if (connection.certProblem) MaterialTheme.colorScheme.error
                    else MaterialTheme.colorScheme.onSurfaceVariant,
                    style = MaterialTheme.typography.bodyMedium,
                )
                Spacer(Modifier.height(12.dp))
            }
            Button(
                onClick = { onSaveAndConnect(url, fingerprint) },
                enabled = connection !is ConnectionUi.Testing && url.isNotBlank() && fingerprint.isNotBlank(),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ReportsTokens.primary,
                    contentColor = Color.White,
                ),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(
                    if (connection is ConnectionUi.Testing) "连接中…" else "保存并连接",
                    fontWeight = FontWeight.SemiBold,
                )
            }
            Spacer(Modifier.height(32.dp))
        }
    }
}

@Composable
private fun FieldLabel(text: String) {
    Text(
        text,
        style = MaterialTheme.typography.labelLarge,
        fontWeight = FontWeight.SemiBold,
        modifier = Modifier.padding(bottom = 8.dp),
    )
}

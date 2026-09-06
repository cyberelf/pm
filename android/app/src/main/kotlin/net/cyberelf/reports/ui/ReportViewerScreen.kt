package net.cyberelf.reports.ui

import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.PictureAsPdf
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.Immutable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import net.cyberelf.reports.ReportViewerUi
import net.cyberelf.reports.ui.theme.ReportsTokens

/** Theme values handed to the WebView so server-rendered HTML matches the
 *  DESIGN.md surfaces in both modes. */
@Immutable
private data class ViewerPalette(
    val background: Color,
    val foreground: String,
    val muted: String,
    val line: String,
    val codeBackground: String,
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReportViewerScreen(
    viewer: ReportViewerUi,
    onClose: () -> Unit,
    onOpenPdf: () -> Unit,
) {
    val dark = isSystemInDarkTheme()
    val palette = if (dark) {
        ViewerPalette(
            background = ReportsTokens.surfaceDark,
            foreground = "#ffffff",
            muted = "#a1a1aa",
            line = "#2a2a2a",
            codeBackground = "#1a1a1a",
        )
    } else {
        ViewerPalette(
            background = ReportsTokens.canvas,
            foreground = "#111111",
            muted = "#6b7280",
            line = "#e5e7eb",
            codeBackground = "#f5f5f5",
        )
    }

    Surface(modifier = Modifier.fillMaxSize(), color = palette.background) {
        Column(Modifier.fillMaxSize().statusBarsPadding()) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 6.dp, vertical = 2.dp),
            ) {
                IconButton(onClick = onClose) {
                    Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "返回")
                }
                Column(Modifier.weight(1f)) {
                    Text(
                        "周报 ${viewer.weekKey}",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                    if (viewer.isCurrent) {
                        Text(
                            "本周",
                            style = MaterialTheme.typography.labelSmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                IconButton(onClick = onOpenPdf, enabled = !viewer.loading && viewer.error == null) {
                    Icon(Icons.Filled.PictureAsPdf, contentDescription = "查看 PDF")
                }
            }
            when {
                viewer.loading -> Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = ReportsTokens.primary)
                }
                viewer.error != null -> Box(Modifier.fillMaxSize().padding(32.dp), contentAlignment = Alignment.Center) {
                    Text(
                        viewer.error,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
                viewer.html != null -> ReportWebView(viewer.html, palette)
            }
        }
    }
}

@Composable
private fun ReportWebView(html: String, palette: ViewerPalette) {
    val wrapped = wrapReportHtml(html, isSystemInDarkTheme())
    AndroidView(
        factory = { context ->
            WebView(context).apply {
                webViewClient = WebViewClient()
                setBackgroundColor(palette.background.toArgb())
            }
        },
        update = { webView ->
            if (webView.tag != wrapped) {
                webView.tag = wrapped
                webView.loadDataWithBaseURL(null, wrapped, "text/html", "utf-8", null)
            }
        },
        modifier = Modifier.fillMaxSize(),
    )
}

/** Wraps the server-rendered fragment with viewport + theme CSS. */
internal fun wrapReportHtml(contentHtml: String, dark: Boolean): String {
    val palette = if (dark) {
        ViewerPalette(
            background = ReportsTokens.surfaceDark,
            foreground = "#ffffff",
            muted = "#a1a1aa",
            line = "#2a2a2a",
            codeBackground = "#1a1a1a",
        )
    } else {
        ViewerPalette(
            background = ReportsTokens.canvas,
            foreground = "#111111",
            muted = "#6b7280",
            line = "#e5e7eb",
            codeBackground = "#f5f5f5",
        )
    }
    val backgroundHex = hexOf(palette.background)
    return """
        <!DOCTYPE html>
        <html>
        <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {
            font-family: system-ui, -apple-system, 'PingFang SC', 'Noto Sans SC', sans-serif;
            color: ${palette.foreground};
            background: $backgroundHex;
            margin: 0 auto;
            padding: 14px 18px 40px;
            max-width: 640px;
            line-height: 1.65;
            font-size: 15px;
            -webkit-text-size-adjust: 100%;
          }
          h1, h2, h3, h4 { line-height: 1.3; margin: 1.2em 0 0.5em; }
          a { color: #3b82f6; }
          code { background: ${palette.codeBackground}; padding: 1px 5px; border-radius: 4px; font-size: 13px; }
          pre { background: ${palette.codeBackground}; padding: 10px 12px; border-radius: 8px; overflow-x: auto; }
          pre code { background: transparent; padding: 0; }
          table { border-collapse: collapse; width: 100%; margin: 0.8em 0; }
          th, td { border: 1px solid ${palette.line}; padding: 5px 8px; font-size: 13px; text-align: left; }
          blockquote { border-left: 3px solid ${palette.line}; margin: 8px 0; padding: 2px 14px; color: ${palette.muted}; }
          img { max-width: 100%; }
          hr { border: none; border-top: 1px solid ${palette.line}; }
        </style>
        </head>
        <body>$contentHtml</body>
        </html>
    """.trimIndent()
}

private fun hexOf(color: Color): String {
    val argb = (color.alpha * 255).toInt().shl(24) or
        (color.red * 255).toInt().shl(16) or
        (color.green * 255).toInt().shl(8) or
        (color.blue * 255).toInt()
    return "#%06X".format(argb and 0xFFFFFF)
}

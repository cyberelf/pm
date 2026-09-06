package net.cyberelf.reports.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Token values lifted from DESIGN.md (reports-workspace-design-system).
object ReportsTokens {
    val primary = Color(0xFF111111)
    val primaryActive = Color(0xFF242424)
    val ink = Color(0xFF111111)
    val body = Color(0xFF374151)
    val muted = Color(0xFF6B7280)
    val hairline = Color(0xFFE5E7EB)
    val canvas = Color(0xFFFFFFFF)
    val surfaceSoft = Color(0xFFF8F9FA)
    val surfaceCard = Color(0xFFF5F5F5)
    val surfaceStrong = Color(0xFFE5E7EB)
    val surfaceDark = Color(0xFF101010)
    val surfaceDarkElevated = Color(0xFF1A1A1A)
    val onDark = Color(0xFFFFFFFF)
    val onDarkSoft = Color(0xFFA1A1AA)
    val brandAccent = Color(0xFF3B82F6)
    val success = Color(0xFF10B981)
    val warning = Color(0xFFF59E0B)
    val error = Color(0xFFEF4444)

    // TODO board inversion (board-* tokens)
    val boardCanvas = Color(0xFF172033)
    val boardLine = Color(0x33F1F5F9) // rgba(241,245,249,.2)
    val boardAccentBlue = Color(0xFF2563EB)
    val boardAccentBlueLine = Color(0xFF60A5FA)
    val boardAccentGreen = Color(0xFF059669)
    val boardAccentSlate = Color(0xFF64748B)
}

private val LightColors = lightColorScheme(
    primary = ReportsTokens.primary,
    onPrimary = Color.White,
    primaryContainer = ReportsTokens.primaryActive,
    onPrimaryContainer = Color.White,
    secondary = ReportsTokens.brandAccent,
    onSecondary = Color.White,
    background = ReportsTokens.canvas,
    onBackground = ReportsTokens.ink,
    surface = ReportsTokens.canvas,
    onSurface = ReportsTokens.ink,
    surfaceVariant = ReportsTokens.surfaceCard,
    onSurfaceVariant = ReportsTokens.muted,
    surfaceContainerLowest = ReportsTokens.canvas,
    surfaceContainerLow = ReportsTokens.surfaceSoft,
    surfaceContainer = ReportsTokens.surfaceCard,
    surfaceContainerHigh = ReportsTokens.surfaceStrong,
    surfaceContainerHighest = ReportsTokens.surfaceStrong,
    outline = ReportsTokens.hairline,
    outlineVariant = Color(0xFFF3F4F6),
    error = ReportsTokens.error,
    tertiary = ReportsTokens.success,
)

private val DarkColors = darkColorScheme(
    primary = Color.White,
    onPrimary = ReportsTokens.ink,
    primaryContainer = ReportsTokens.surfaceDarkElevated,
    onPrimaryContainer = Color.White,
    secondary = ReportsTokens.brandAccent,
    onSecondary = Color.White,
    background = ReportsTokens.surfaceDark,
    onBackground = Color.White,
    surface = ReportsTokens.surfaceDark,
    onSurface = Color.White,
    surfaceVariant = ReportsTokens.surfaceDarkElevated,
    onSurfaceVariant = ReportsTokens.onDarkSoft,
    surfaceContainerLowest = ReportsTokens.surfaceDark,
    surfaceContainerLow = ReportsTokens.surfaceDark,
    surfaceContainer = ReportsTokens.surfaceDarkElevated,
    surfaceContainerHigh = ReportsTokens.surfaceDarkElevated,
    surfaceContainerHighest = ReportsTokens.surfaceDarkElevated,
    outline = Color(0xFF2A2A2A),
    outlineVariant = Color(0xFF222222),
    error = ReportsTokens.error,
    tertiary = ReportsTokens.success,
)

@Composable
fun ReportsTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = if (isSystemInDarkTheme()) DarkColors else LightColors,
        content = content,
    )
}

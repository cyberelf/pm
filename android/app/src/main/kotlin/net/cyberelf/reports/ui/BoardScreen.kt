package net.cyberelf.reports.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import net.cyberelf.reports.ui.theme.ReportsTokens

@Composable
fun BoardScreen(modifier: Modifier = Modifier) {
    // M2 replaces this placeholder with the four-column drag board on the
    // board-canvas inversion from DESIGN.md.
    Box(
        modifier
            .fillMaxSize()
            .padding(16.dp)
            .background(ReportsTokens.boardCanvas, RoundedCornerShape(16.dp)),
        contentAlignment = Alignment.Center,
    ) {
        Text(
            "看板将在下一里程碑提供",
            color = ReportsTokens.onDarkSoft,
            fontWeight = FontWeight.Medium,
        )
    }
}

package net.cyberelf.reports

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import net.cyberelf.reports.ui.AppRoot
import net.cyberelf.reports.ui.theme.ReportsTheme

class MainActivity : ComponentActivity() {

    /** Set by onNewIntent when a shortcut/tile re-entry asks for the voice
     *  sheet; consumed by the composition once handled. */
    private var openVoiceOnReentry by mutableStateOf(false)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val initialOpenVoice = intent?.action == VoiceTileContract.ACTION_OPEN_VOICE
        setContent {
            ReportsTheme {
                AppRoot(
                    openVoiceOnStart = initialOpenVoice || openVoiceOnReentry,
                    onVoiceStarted = { openVoiceOnReentry = false },
                )
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        if (intent.action == VoiceTileContract.ACTION_OPEN_VOICE) {
            openVoiceOnReentry = true
        }
    }
}

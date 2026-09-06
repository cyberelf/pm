package net.cyberelf.reports

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import net.cyberelf.reports.ui.AppRoot
import net.cyberelf.reports.ui.theme.ReportsTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            ReportsTheme {
                AppRoot()
            }
        }
    }
}

package net.cyberelf.reports.shortcuts

import android.app.PendingIntent
import android.content.Intent
import android.os.Build
import android.service.quicksettings.TileService
import net.cyberelf.reports.MainActivity
import net.cyberelf.reports.VoiceTileContract

/** Quick-settings tile that jumps straight into the voice sheet. */
class VoiceTileService : TileService() {

    override fun onClick() {
        val intent = Intent(this, MainActivity::class.java).apply {
            action = VoiceTileContract.ACTION_OPEN_VOICE
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        if (Build.VERSION.SDK_INT >= 34) {
            // Intent overload is deprecated from 34; the PendingIntent
            // variant is the supported path.
            startActivityAndCollapse(
                PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_IMMUTABLE),
            )
        } else {
            @Suppress("DEPRECATION")
            startActivityAndCollapse(intent)
        }
    }
}

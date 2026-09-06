package net.cyberelf.reports

import net.cyberelf.reports.ui.wrapReportHtml
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class ReportViewerHtmlTest {

    @Test
    fun `wraps content with viewport and the report body`() {
        val html = wrapReportHtml("<h1>本周</h1><p>要点</p>", dark = false)
        assertTrue(html.contains("""name="viewport" content="width=device-width, initial-scale=1""""))
        assertTrue(html.contains("<h1>本周</h1><p>要点</p>"))
        assertTrue(html.contains("max-width: 640px"))
    }

    @Test
    fun `dark mode uses the inverted surface palette`() {
        val dark = wrapReportHtml("<p>x</p>", dark = true)
        assertTrue(dark.contains("color: #ffffff"))
        assertTrue(dark.contains("background: #101010"))
        assertTrue(dark.contains("border: 1px solid #2a2a2a"))
    }

    @Test
    fun `light mode uses the workspace palette`() {
        val light = wrapReportHtml("<p>x</p>", dark = false)
        assertTrue(light.contains("color: #111111"))
        assertTrue(light.contains("background: #FFFFFF"))
    }

    @Test
    fun `hex rendering drops the alpha channel cleanly`() {
        // sanity: opaque white renders as 6-digit hex, not 8-digit bleed-through
        assertEquals(1, Regex("background: #[0-9A-F]{6}\\b").findAll(wrapReportHtml("<p>x</p>", dark = false)).count())
    }
}

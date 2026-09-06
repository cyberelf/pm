package net.cyberelf.reports

import kotlinx.coroutines.runBlocking
import net.cyberelf.reports.data.CertTrust
import net.cyberelf.reports.data.buildApi
import okhttp3.OkHttpClient
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/** Workspace/archive payload contracts. Notably the archive endpoint returns
 *  rendered HTML only (content_md is popped server-side). */
class ReportsFlowTest {

    private lateinit var server: MockWebServer

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    private fun api() = buildApi(CertTrust.okHttpClient(null), server.url("/").toString())

    @Test
    fun `workspace parses report and history while ignoring heavy fields`() = runBlocking {
        server.enqueue(
            MockResponse().setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(
                    """
                    {
                      "project": {"id": 4, "name": "周报工作台", "status": "active",
                                  "updated_at": "2026-09-06T10:00:00+08:00", "progress_status": "on track",
                                  "timezone": "Asia/Shanghai", "report_provider": "codex",
                                  "system_prompt": "", "report_template": ""},
                      "week_key": "2026-W36",
                      "schedules": [], "materials": [{"whatever": 1}], "repos": [],
                      "plan": {}, "outcomes": [], "weekly_update": null,
                      "jobs": [], "risks": [], "source_diagnostics": [],
                      "progress_status": "on track",
                      "report": {"id": 9, "week_key": "2026-W36",
                                 "content_md": "# 本周\n- 事项一",
                                 "content_html": "<h1>本周</h1><ul><li>事项一</li></ul>",
                                 "latest_job_id": 77,
                                 "created_at": "2026-09-06T10:00:00+08:00",
                                 "updated_at": "2026-09-06T10:00:00+08:00"},
                      "report_history": [
                        {"week_key": "2026-W36", "latest_job_id": 77,
                         "created_at": "2026-09-06T10:00:00+08:00",
                         "updated_at": "2026-09-06T10:00:00+08:00", "is_current_week": true},
                        {"week_key": "2026-W35", "latest_job_id": 70,
                         "created_at": "2026-08-30T10:00:00+08:00",
                         "updated_at": "2026-08-30T10:00:00+08:00", "is_current_week": false}
                      ]
                    }
                    """.trimIndent(),
                ),
        )

        val workspace = api().workspace(4)

        assertEquals("2026-W36", workspace.weekKey)
        assertEquals("周报工作台", workspace.project?.name)
        assertEquals("on track", workspace.project?.progressStatus)
        assertEquals("# 本周\n- 事项一", workspace.report?.contentMd)
        assertTrue(workspace.report?.contentHtml!!.contains("事项一"))
        assertEquals(2, workspace.reportHistory.size)
        assertEquals("2026-W35", workspace.reportHistory[1].weekKey)
        assertEquals(true, workspace.reportHistory[0].isCurrentWeek)
        assertEquals("/api/projects/4/workspace", server.takeRequest().path)
    }

    @Test
    fun `archived report carries html without content_md`() = runBlocking {
        server.enqueue(
            MockResponse().setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody(
                    """
                    {"week_key": "2026-W35",
                     "content_html": "<h1>上周周报</h1><p>要点</p>",
                     "updated_at": "2026-08-30T10:00:00+08:00"}
                    """.trimIndent(),
                ),
        )

        val report = api().archivedReport(4, "2026-W35")

        assertEquals("2026-W35", report.weekKey)
        assertEquals(null, report.contentMd)
        assertTrue(report.contentHtml.contains("上周周报"))
        assertEquals("/api/projects/4/reports/2026-W35", server.takeRequest().path)
    }
}

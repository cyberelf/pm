package net.cyberelf.reports

import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import net.cyberelf.reports.data.BoardRepository
import net.cyberelf.reports.data.BoardResult
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

/** Pins the board mutation contracts: PUT carries only the status, close
 *  requires a reason (plus optional archive project), and every response's
 *  full todo list replaces app state. */
class BoardFlowTest {

    private lateinit var server: MockWebServer

    private fun repository(): BoardRepository {
        val api = buildApi(CertTrust.okHttpClient(null), server.url("/").toString())
        return BoardRepository(apiProvider = { api })
    }

    @Before
    fun setUp() {
        server = MockWebServer()
        server.start()
    }

    @After
    fun tearDown() {
        server.shutdown()
    }

    private fun enqueueTodos(vararg statuses: String) {
        val items = statuses.withIndex().joinToString(",") { (index, status) ->
            """{"id": ${index + 1}, "title": "TODO ${index + 1}", "status": "$status",
               "description": "", "close_reason": "", "project_id": null,
               "project_name": null, "material_id": null,
               "created_at": "2026-09-06T10:00:00+08:00",
               "updated_at": "2026-09-06T10:00:00+08:00", "closed_at": null,
               "description_html": ""}"""
        }
        server.enqueue(
            MockResponse().setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"todos": [$items]}"""),
        )
    }

    @Test
    fun `move sends only the new status`() = runBlocking {
        enqueueTodos("doing")

        val result = repository().move(5, "doing")

        assertTrue(result is BoardResult.Success)
        assertEquals(listOf("doing"), (result as BoardResult.Success).todos.map { it.status })
        val request = server.takeRequest()
        assertEquals("/api/todos/5", request.path)
        assertEquals("PUT", request.method)
        val body = Json.parseToJsonElement(request.body.readUtf8()).jsonObject
        assertEquals("doing", body["status"]!!.jsonPrimitive.content)
        assertTrue(!body.containsKey("title"))
    }

    @Test
    fun `close sends mandatory reason and optional project`() = runBlocking {
        server.enqueue(
            MockResponse().setResponseCode(200)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"material_id": 12, "todos": []}"""),
        )

        val result = repository().close(5, "done this week", projectId = 2)

        assertTrue(result is BoardResult.Success)
        assertEquals(12L, (result as BoardResult.Success).materialId)
        val request = server.takeRequest()
        assertEquals("/api/todos/5/close", request.path)
        assertEquals("POST", request.method)
        val body = Json.parseToJsonElement(request.body.readUtf8()).jsonObject
        assertEquals("done this week", body["reason"]!!.jsonPrimitive.content)
        assertEquals("2", body["project_id"]!!.jsonPrimitive.content)
    }

    @Test
    fun `server validation errors surface as messages`() = runBlocking {
        server.enqueue(
            MockResponse().setResponseCode(400)
                .setHeader("Content-Type", "application/json")
                .setBody("""{"error": "close reason is required"}"""),
        )

        val result = repository().close(5, " ", projectId = null)

        assertTrue(result is BoardResult.Error)
        assertEquals("close reason is required", (result as BoardResult.Error).message)
    }

    @Test
    fun `create posts the trimmed title`() = runBlocking {
        enqueueTodos("todo")

        val result = repository().create("  写周报  ")

        assertTrue(result is BoardResult.Success)
        val request = server.takeRequest()
        assertEquals("/api/todos", request.path)
        assertEquals("POST", request.method)
        val body = Json.parseToJsonElement(request.body.readUtf8()).jsonObject
        assertEquals("写周报", body["title"]!!.jsonPrimitive.content)
    }
}

package net.cyberelf.reports.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowDropDown
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.filled.Send
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import net.cyberelf.reports.data.ProjectDto
import net.cyberelf.reports.data.TodoDto
import net.cyberelf.reports.ui.theme.ReportsTokens

// board-* inversion tokens from DESIGN.md (alpha prefixes computed from the
// rgba values there).
private val BoardCardFill = Color(0xFF1E2A40) // board-column-fill over canvas
private val BoardTodoFill = Color(0x572563EB)
private val BoardDoingFill = Color(0x52059669)
private val BoardClosedFill = Color(0x6164748B)
private val BoardTodoLine = Color(0xBF60A5FA)
private val BoardDoingLine = Color(0xB834D399)
private val BoardClosedLine = Color(0xAD94A3B8)
private val BoardHeadLine = Color(0x33FFFFFF)
private val BoardChipFill = Color(0x24FFFFFF)
private val OnBoard = ReportsTokens.onDark
private val OnBoardMuted = ReportsTokens.onDarkSoft

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BoardScreen(
    todos: List<TodoDto>,
    projects: List<ProjectDto>,
    loaded: Boolean,
    busy: Boolean,
    error: String?,
    closingTodo: TodoDto?,
    onRefresh: () -> Unit,
    onAdd: (String) -> Unit,
    onMove: (TodoDto, String) -> Unit,
    onDelete: (TodoDto) -> Unit,
    onCloseConfirm: (String, Long?) -> Unit,
    onCloseSheetDismiss: () -> Unit,
    onDismissError: () -> Unit,
    modifier: Modifier = Modifier,
) {
    LaunchedEffect(loaded) { if (!loaded) onRefresh() }

    Box(
        modifier
            .fillMaxSize()
            .padding(12.dp)
            .background(ReportsTokens.boardCanvas, RoundedCornerShape(16.dp)),
    ) {
        Column(Modifier.fillMaxSize()) {
            error?.let { message ->
                BoardErrorBar(message, onDismissError)
            }
            if (!loaded) {
                Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    CircularProgressIndicator(color = BoardTodoLine)
                }
                return@Column
            }
            BoardPager(todos, onAdd, onMove, onDelete)
        }

        closingTodo?.let { todo ->
            CloseSheet(todo, projects, busy, onCloseConfirm, onCloseSheetDismiss)
        }
    }
}

@Composable
private fun BoardErrorBar(message: String, onDismiss: () -> Unit) {
    Surface(
        color = Color(0x33EF4444),
        shape = RoundedCornerShape(10.dp),
        modifier = Modifier
            .fillMaxWidth()
            .padding(10.dp),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(start = 12.dp)) {
            Text(message, color = OnBoard, style = MaterialTheme.typography.bodySmall, modifier = Modifier.weight(1f))
            IconButton(onClick = onDismiss) {
                Icon(Icons.Filled.Close, contentDescription = "关闭提示", tint = OnBoardMuted, modifier = Modifier.size(16.dp))
            }
        }
    }
}

private data class BoardColumn(
    val status: String,
    val title: String,
    val fill: Color,
    val line: Color,
)

private val columns = listOf(
    BoardColumn("todo", "待办", BoardTodoFill, BoardTodoLine),
    BoardColumn("doing", "进行中", BoardDoingFill, BoardDoingLine),
    BoardColumn("closed", "已关闭", BoardClosedFill, BoardClosedLine),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun BoardPager(
    todos: List<TodoDto>,
    onAdd: (String) -> Unit,
    onMove: (TodoDto, String) -> Unit,
    onDelete: (TodoDto) -> Unit,
) {
    val pagerState = rememberPagerState(pageCount = { columns.size })
    val scope = rememberCoroutineScope()

    Column(Modifier.fillMaxSize()) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(top = 10.dp, bottom = 4.dp),
            horizontalArrangement = Arrangement.Center,
        ) {
            columns.forEachIndexed { index, column ->
                val selected = pagerState.currentPage == index
                Box(
                    Modifier
                        .padding(horizontal = 5.dp)
                        .size(if (selected) 10.dp else 7.dp)
                        .background(
                            if (selected) column.line else BoardHeadLine,
                            CircleShape,
                        )
                        .clickable { scope.launch { pagerState.animateScrollToPage(index) } },
                )
            }
        }
        HorizontalPager(state = pagerState, modifier = Modifier.weight(1f)) { page ->
            val column = columns[page]
            val items = todos.filter { it.status == column.status }
            Column(Modifier.fillMaxSize().padding(10.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        column.title,
                        color = OnBoard,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Spacer(Modifier.width(8.dp))
                    Box(
                        Modifier
                            .background(BoardChipFill, RoundedCornerShape(999.dp))
                            .padding(horizontal = 8.dp, vertical = 2.dp),
                    ) {
                        Text("${items.size}", color = OnBoardMuted, style = MaterialTheme.typography.labelSmall)
                    }
                }
                Spacer(Modifier.height(4.dp))
                Box(
                    Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(BoardHeadLine),
                )
                if (column.status == "todo") {
                    Spacer(Modifier.height(10.dp))
                    DraftBar(onAdd)
                }
                Spacer(Modifier.height(10.dp))
                if (items.isEmpty()) {
                    Box(Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) {
                        Text("暂无${column.title}事项", color = OnBoardMuted, style = MaterialTheme.typography.bodySmall)
                    }
                } else {
                    LazyColumn(
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                        contentPadding = PaddingValues(bottom = 16.dp),
                        modifier = Modifier.weight(1f),
                    ) {
                        items(items, key = { it.id }) { todo ->
                            BoardCard(todo, column, onMove, onDelete)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun DraftBar(onAdd: (String) -> Unit) {
    var draft by remember { mutableStateOf("") }
    Row(verticalAlignment = Alignment.CenterVertically) {
        OutlinedTextField(
            value = draft,
            onValueChange = { draft = it },
            placeholder = { Text("快速记一条待办…", color = OnBoardMuted, style = MaterialTheme.typography.bodySmall) },
            singleLine = true,
            shape = RoundedCornerShape(10.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedTextColor = OnBoard,
                unfocusedTextColor = OnBoard,
                focusedBorderColor = BoardTodoLine,
                unfocusedBorderColor = BoardHeadLine,
                cursorColor = BoardTodoLine,
            ),
            modifier = Modifier.weight(1f),
        )
        Spacer(Modifier.width(8.dp))
        IconButton(
            onClick = {
                if (draft.isNotBlank()) {
                    onAdd(draft)
                    draft = ""
                }
            },
        ) {
            Icon(Icons.Filled.Send, contentDescription = "新建待办", tint = BoardTodoLine)
        }
    }
}

@Composable
private fun BoardCard(
    todo: TodoDto,
    column: BoardColumn,
    onMove: (TodoDto, String) -> Unit,
    onDelete: (TodoDto) -> Unit,
) {
    var actionsOpen by remember { mutableStateOf(false) }
    Surface(
        color = column.fill,
        shape = RoundedCornerShape(12.dp),
        border = androidx.compose.foundation.BorderStroke(1.dp, column.line),
        modifier = Modifier
            .fillMaxWidth()
            .clickable { actionsOpen = true },
    ) {
        Column(Modifier.padding(horizontal = 12.dp, vertical = 10.dp)) {
            Text(todo.title, color = OnBoard, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.Medium)
            Row(verticalAlignment = Alignment.CenterVertically, modifier = Modifier.padding(top = 4.dp)) {
                if (todo.projectName != null) {
                    Box(
                        Modifier
                            .background(BoardChipFill, RoundedCornerShape(999.dp))
                            .padding(horizontal = 7.dp, vertical = 1.dp),
                    ) {
                        Text(
                            todo.projectName,
                            color = OnBoardMuted,
                            style = MaterialTheme.typography.labelSmall,
                        )
                    }
                }
                if (todo.status == "closed" && todo.closeReason?.isNotBlank() == true) {
                    Spacer(Modifier.width(8.dp))
                    Text(
                        todo.closeReason,
                        color = OnBoardMuted,
                        style = MaterialTheme.typography.labelSmall,
                        maxLines = 1,
                    )
                }
            }
        }
    }
    if (actionsOpen) {
        TodoActionsSheet(
            todo = todo,
            onAction = { action ->
                actionsOpen = false
                when (action) {
                    "doing" -> onMove(todo, "doing")
                    "todo" -> onMove(todo, "todo")
                    "closed" -> onMove(todo, "closed")
                    "delete" -> onDelete(todo)
                }
            },
            onDismiss = { actionsOpen = false },
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun TodoActionsSheet(todo: TodoDto, onAction: (String) -> Unit, onDismiss: () -> Unit) {
    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(Modifier.padding(bottom = 24.dp)) {
            Text(
                todo.title,
                style = MaterialTheme.typography.titleSmall,
                fontWeight = FontWeight.SemiBold,
                modifier = Modifier.padding(horizontal = 20.dp, vertical = 6.dp),
            )
            when (todo.status) {
                "todo" -> SheetAction("移到进行中") { onAction("doing") }
                "doing" -> SheetAction("退回待办") { onAction("todo") }
            }
            if (todo.status != "closed") {
                SheetAction("关闭…") { onAction("closed") }
                SheetAction("删除", danger = true) { onAction("delete") }
            }
            SheetAction("取消") { onDismiss() }
        }
    }
}

@Composable
private fun SheetAction(label: String, danger: Boolean = false, onClick: () -> Unit) {
    TextButton(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Text(
            label,
            color = if (danger) MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.onSurface,
        )
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun CloseSheet(
    todo: TodoDto,
    projects: List<ProjectDto>,
    busy: Boolean,
    onConfirm: (String, Long?) -> Unit,
    onDismiss: () -> Unit,
) {
    var reason by remember(todo.id) { mutableStateOf("") }
    var projectExpanded by remember { mutableStateOf(false) }
    var selectedProject by remember(todo.id) { mutableStateOf<ProjectDto?>(null) }

    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(Modifier.padding(horizontal = 20.dp).padding(bottom = 28.dp)) {
            Text("关闭 TODO", style = MaterialTheme.typography.titleMedium, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(4.dp))
            Text(todo.title, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            Spacer(Modifier.height(14.dp))
            OutlinedTextField(
                value = reason,
                onValueChange = { reason = it },
                placeholder = { Text("关闭原因（必填，会存档为项目素材）") },
                minLines = 2,
                shape = RoundedCornerShape(10.dp),
                modifier = Modifier.fillMaxWidth(),
            )
            Spacer(Modifier.height(10.dp))
            Box {
                OutlinedTextField(
                    value = selectedProject?.name ?: "归档项目（可选）",
                    onValueChange = {},
                    readOnly = true,
                    singleLine = true,
                    shape = RoundedCornerShape(10.dp),
                    trailingIcon = {
                        IconButton(onClick = { projectExpanded = !projectExpanded }) {
                            Icon(Icons.Filled.ArrowDropDown, contentDescription = "选择项目")
                        }
                    },
                    modifier = Modifier.fillMaxWidth(),
                )
                androidx.compose.material3.DropdownMenu(
                    expanded = projectExpanded,
                    onDismissRequest = { projectExpanded = false },
                ) {
                    androidx.compose.material3.DropdownMenuItem(
                        text = { Text("不归档到项目") },
                        onClick = {
                            selectedProject = null
                            projectExpanded = false
                        },
                    )
                    projects.forEach { project ->
                        androidx.compose.material3.DropdownMenuItem(
                            text = { Text(project.name) },
                            onClick = {
                                selectedProject = project
                                projectExpanded = false
                            },
                        )
                    }
                }
            }
            Spacer(Modifier.height(16.dp))
            Button(
                onClick = { onConfirm(reason, selectedProject?.id) },
                enabled = !busy && reason.isNotBlank(),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ReportsTokens.primary,
                    contentColor = Color.White,
                ),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(if (busy) "关闭中…" else "确认关闭")
            }
        }
    }
}

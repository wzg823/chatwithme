# ChatWithMe - 小说创作工作流应用设计文档

> 版本：v0.1
> 日期：2026-05-07

---

## 一、产品定位

以「上下文管理器」为核心特色的 AI 辅助小说创作 Web 应用，通过 PromptChat 的按钮系统作为 UX 层触发创作工作流各阶段。

---

## 二、核心概念

| 概念 | 说明 |
|------|------|
| 小说（Novel） | 一个完整的创作项目，包含世界观、大纲、章节等 |
| 创作阶段 | 世界构建 / 总大纲 / 分卷大纲 / 单章细纲 / 单章成文 |
| 上下文整理节点 | 每个阶段自动整理该阶段的创作上下文包 |
| 伏笔追踪表 | 记录埋下的伏笔及回收计划 |
| 章节摘要 | 每章完成后自动生成的摘要 |

---

## 三、创作流程（5层）

```
第1层：世界构建 →
第2层：总大纲 →
第3层：分卷大纲 → 上下文整理节点(卷级) →
第4层：单章细纲 → 上下文整理节点(章级) →
第5层：单章成文 → 审核节点 → 更新伏笔表 + 章节摘要表
```

- 预设流程，用户可增删调整
- 每层对应系统注入型按钮激活上下文整理

---

## 四、页面结构

```
┌────────────┬─────────────────────────┬──────────────────────┐
│ 左：小说列表 │ 中：对话区               │ 右：写作辅助面板      │
│            │                         │                      │
│ 📚 我的小说 │ 顶部：书名 | 模型选择    │ [世界观] [角色]    │
│ • 玄幻之... │                         │ [大纲] [伏笔]      │
│ • test001  │ ┌─────────────────────┐ │ [AI配置]          │
│ • test002  │ │                     │ │                     │
│ • test003  │ │    对话消息流     │ │ 展开后显示对应   │
│            │ │                     │ │ 结构化内容        │
│ [+ 新建]   │ └─────────────────────┘ │                  │
│            │ 输入框 + 快捷按钮         │                  │
└────────────┴─────────────────────────┴──────────────────────┘
```

快捷按钮：`总结` `润色` `续写` `扩写` `[角色]` `[世界观]` `[设定]` ...

---

## 五、交互模式（混合模式）

| 模式 | 触发 | 说明 |
|------|------|------|
| 对话驱动 | 点击阶段按钮 | 激活系统提示词 → 在主对话区自由输入 → AI 协作 |
| 表单驱动 | 右侧面板tab | 打开结构化表单填写 → 自动生成上下文 → 传入对话 |

---

## 六、数据模型（独立存储）

| 表名 | 用途 |
|------|------|
| novels | 小说项目（每本书一个） |
| world_settings | 世界观设定 |
| outlines | 总大纲 / 分卷大纲 |
| chapters | 章节（细纲+正文+状态） |
| plot_threads | 伏笔追踪表 |
| chapter_summaries | 已完成章节摘要 |
| messages | 对话消息 |
| prompt_buttons | 快捷按钮配置 |
| prompt_categories | 按钮分类 |
| model_config | 模型配置 |

---

## 七、技术选型

### 前端

| 用途 | 方案 |
|------|------|
| 框架 | Vue 3 |
| 状态管理 | Pinia |
| 打包工具 | Vite |
| 样式 | Tailwind CSS |
| Markdown | markdown-it + highlight.js |
| 流式请求 | fetch + ReadableStream |
| 图标 | Lucide Icons |
| 拖拽排序 | vue-draggable-plus |

### 后端

| 用途 | 方案 |
|------|------|
| Web 框架 | FastAPI |
| AI 请求代理 | httpx + SSE |
| 流式转发 | StreamingResponse |
| 数据库 ORM | SQLAlchemy 2.0 |
| 数据校验 | Pydantic v2 |
| 数据库 | SQLite |

---

## 八、API 接口设计

### 核心接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/chat | 对话（流式返回） |
| GET/POST | /api/novels | 小说CRUD |
| GET/POST | /api/world-settings | 世界观CRUD |
| GET/POST | /api/outlines | 大纲CRUD |
| GET/POST | /api/chapters | 章节CRUD |
| GET/POST | /api/plot-threads | 伏笔CRUD |
| GET/POST | /api/chapter-summaries | 章节摘要CRUD |
| GET/POST | /api/prompt-buttons | 快捷按钮CRUD |
| GET/POST | /api/model-config | 模型配置 |

### Model Adapter 接口

```python
interface ModelAdapter {
  send_message(messages: Message[], config: ModelConfig) -> AsyncStream[string]
}
```

---

## 九、预留扩展

- 多用户账号体系（后端 users 表）
- 云端会话同步
- 提示词库导入/导出
- PostgreSQL 切换（改连接字符串即可）
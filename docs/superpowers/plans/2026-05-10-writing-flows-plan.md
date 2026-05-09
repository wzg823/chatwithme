# 小说创作流程实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在右侧辅助面板增加「流程」标签页，支持按不同创作阶段进行独立会话

**Architecture:** 
- Message 表新增 flow_type 字段区分会话
- 流程配置存储在 system_config 的 prompt_templates 中
- 前端发送消息时将流程提示词作为前缀

**Tech Stack:** FastAPI + Vue 3 + Pinia + SQLite

---

### Task 1: 后端 - Message 表添加 flow_type 字段

**Files:**
- Modify: `backend/app/models/models.py:19-27`

- [ ] **Step 1: 添加 flow_type 字段**

修改 `Message` 类，在 `novel_id` 后添加 `flow_type` 字段：

```python
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)
    content = Column(Text)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    flow_type = Column(String, nullable=True)  # 新增
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="messages")
```

- [ ] **Step 2: 更新数据库（ Alembic 迁移或直接添加列）**

检查项目是否使用 Alembic，如使用则创建迁移；否则直接在数据库执行：

```sql
ALTER TABLE messages ADD COLUMN flow_type VARCHAR;
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/models/models.py
git commit -m "feat: add flow_type field to Message model"
```

---

### Task 2: 后端 - novels router 支持 flow_type

**Files:**
- Modify: `backend/app/routers/novels.py:56-66`

- [ ] **Step 1: 修改 get_novel_messages 支持 flow_type 参数**

```python
@router.get("/novels/{novel_id}/messages", response_model=list[MessageSchema])
def get_novel_messages(novel_id: int, flow_type: str = None, db: Session = Depends(get_db)):
    query = db.query(Message).filter(Message.novel_id == novel_id)
    if flow_type:
        query = query.filter(Message.flow_type == flow_type)
    else:
        # 默认获取 null（兼容旧数据）
        query = query.filter(Message.flow_type == None)
    return query.all()
```

- [ ] **Step 2: 修改 create_novel_message 支持 flow_type**

```python
@router.post("/novels/{novel_id}/messages", response_model=MessageSchema)
def create_novel_message(novel_id: int, message: MessageCreate, flow_type: str = None, db: Session = Depends(get_db)):
    msg = Message(role=message.role, content=message.content, novel_id=novel_id, flow_type=flow_type)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
```

注意：`MessageCreate` 是 Pydantic 模型，需要支持 flow_type（在请求体中传入或作为 query 参数）

- [ ] **Step 3: 提交**

```bash
git add backend/app/routers/novels.py
git commit -m "feat: support flow_type in novels messages API"
```

---

### Task 3: 后端 - 存储流程配置（writing_flows）

**Files:**
- Modify: `backend/app/routers/model_configs.py`
- 或新增 `backend/app/routers/configs.py`

- [ ] **Step 1: 在 ModelConfig 模型中添加 prompt_templates 字段**

修改 `ModelConfig` 类，添加 JSON 字段：

```python
from sqlalchemy.dialects.postgresql import JSON
# 或使用 SQLite 时使用 Text 存储 JSON 字符串
import json

class ModelConfig(Base):
    __tablename__ = "model_configs"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, default="openai")
    base_url = Column(String, nullable=True)
    model = Column(String, default="gpt-4")
    api_key = Column(String, nullable=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=4096)
    prompt_templates = Column(Text, nullable=True)  # 新增，存储 JSON 字符串
```

- [ ] **Step 2: 修改 API 返回 prompt_templates**

修改 `model_configs.py` 的响应模型和 CRUD：

```python
class ModelConfigResponse(BaseModel):
    id: int
    provider: str
    base_url: str | None
    model: str
    api_key: str | None
    temperature: float
    max_tokens: int
    prompt_templates: str | None  # JSON 字符串

    class Config:
        from_attributes = True
```

- [ ] **Step 3: 提交**

```bash
git add backend/app/routers/model_configs.py backend/app/models/models.py
git commit -m "feat: add prompt_templates field to ModelConfig"
```

---

### Task 4: 前端 - Store 添加流程相关状态

**Files:**
- Modify: `frontend/src/stores/chat.ts`

- [ ] **Step 1: 添加 WritingFlow 类型和状态**

```typescript
export interface WritingFlow {
  id: string
  name: string
  prompt: string
  enabled: boolean
}

const writingFlows = ref<WritingFlow[]>([
  { id: 'outline', name: '大纲', prompt: '请帮我设计小说大纲：', enabled: true },
  { id: 'volume', name: '卷纲', prompt: '请帮我设计这一卷的卷纲：', enabled: true },
  { id: 'body', name: '正文', prompt: '请续写以下内容：', enabled: true }
])

const currentFlow = ref<string | null>(null)
```

- [ ] **Step 2: 添加相关方法**

```typescript
const fetchWritingFlows = async () => {
  const res = await axios.get('/api/model-configs')
  if (res.data.length > 0) {
    const templates = res.data[0].prompt_templates
    if (templates) {
      try {
        const obj = JSON.parse(templates)
        if (obj.writing_flows) {
          writingFlows.value = obj.writing_flows
        }
      } catch (e) {}
    }
  }
}

const saveWritingFlows = async () => {
  const res = await axios.get('/api/model-configs')
  if (res.data.length > 0) {
    const config = res.data[0]
    const templates = JSON.stringify({ writing_flows: writingFlows.value })
    await axios.put('/api/model-configs/1', {
      ...config,
      prompt_templates: templates
    })
  }
}

const selectFlow = async (flowId: string | null) => {
  currentFlow.value = flowId
  if (currentNovel.value) {
    const res = await axios.get(`/api/novels/${currentNovel.value.id}/messages?flow_type=${flowId || ''}`)
    messages.value = res.data
  }
}
```

- [ ] **Step 3: 更新 sendMessage 支持流程前缀**

修改 `sendMessage` 方法：

```typescript
const sendMessage = async (content: string, promptButtons: string[] = []) => {
  if (!currentNovel.value) return

  // 如果选择了流程，添加流程提示词前缀
  let finalContent = content
  if (currentFlow.value) {
    const flow = writingFlows.value.find(f => f.id === currentFlow.value)
    if (flow?.prompt) {
      finalContent = flow.prompt + '\n' + content
    }
  }
  // ... 后续逻辑使用 finalContent
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/stores/chat.ts
git commit -m "feat: add writing flows support in store"
```

---

### Task 5: 前端 - 右侧面板添加流程标签页

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 添加流程标签页按钮**

修改辅助面板的 tabs数组：

```vue
<button
  v-for="tab in ['世界观', '角色', '大纲', '伏笔', 'AI配置', '流程']"
  :key="tab"
  @click="activeTab = tab"
  class="px-2 py-1 text-sm"
  :class="activeTab === tab ? 'border-b-2 border-blue-500' : ''"
>
  {{ tab }}
</button>
```

- [ ] **Step 2: 添加流程标签页内容**

```vue
<div v-if="activeTab === '流程'" class="space-y-2">
  <div
    v-for="flow in store.writingFlows"
    :key="flow.id"
    class="p-2 border rounded cursor-pointer hover:bg-gray-100 flex items-center justify-between"
    :class="{ 'bg-blue-100': store.currentFlow === flow.id }"
    @click="store.selectFlow(flow.id)"
  >
    <span>{{ flow.name }}</span>
    <span v-if="!flow.enabled" class="text-xs text-gray-400">已禁用</span>
  </div>
  <div v-if="!store.writingFlows.length" class="text-gray-400 text-sm">
    暂无创作流程，请在配置中添加
  </div>
</div>
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat: add flow tab in sidebar"
```

---

### Task 6: 前端 - 配置弹窗添加流程管理界面

**Files:**
- Modify: `frontend/src/App.vue` (配置弹窗部分)

- [ ] **Step 1: 添加流程配置区域**

在配置弹窗的「提示词模板」标签页中添加：

```vue
<div v-if="configTab === 'prompt'">
  <!-- 原有按钮模板 -->
  
  <hr class="my-4" />
  
  <h3 class="font-bold mb-2">创作流程</h3>
  <div v-for="(flow, idx) in store.writingFlows" :key="flow.id" class="mb-3 p-2 border rounded">
    <div class="flex items-center gap-2 mb-1">
      <input
        v-model="flow.name"
        class="border rounded px-2 py-1 flex-1"
        placeholder="名称"
      />
      <input
        type="checkbox"
        v-model="flow.enabled"
        :id="'flow-enabled-' + flow.id"
      />
      <label :for="'flow-enabled-' + flow.id" class="text-sm">启用</label>
      <button @click="removeFlow(idx)" class="text-red-500">删除</button>
    </div>
    <textarea
      v-model="flow.prompt"
      class="w-full border rounded p-2"
      rows="2"
      placeholder="流程提示词前缀"
    ></textarea>
  </div>
  <button @click="addFlow" class="w-full py-2 border-2 border-dashed border-gray-300 rounded text-gray-500 hover:border-blue-400">
    + 新增流程
  </button>
</div>
```

- [ ] **Step 2: 添加相关方法**

在 script 中添加：

```typescript
const addFlow = () => {
  store.writingFlows.push({
    id: 'flow-' + Date.now(),
    name: '',
    prompt: '',
    enabled: true
  })
}

const removeFlow = (idx: number) => {
  store.writingFlows.splice(idx, 1)
}
```

- [ ] **Step 3: 更新保存配置方法**

修改 `saveConfig`，保存 writingFlows：

```typescript
const saveConfig = async () => {
  await store.saveSystemConfig()
  await store.saveWritingFlows()  // 新增
  showConfig.value = false
}
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/App.vue
git commit -m "feat: add flow management in config"
```

---

### Task 7: 测试与验证

**Files:**
- 修改的所有文件

- [ ] **Step 1: 启动后端服务**

```bash
cd backend
uvicorn app.main:app --reload
```

- [ ] **Step 2: 启动前端服务**

```bash
cd frontend
npm run dev
```

- [ ] **Step 3: 测试流程**

1. 打开浏览器访问 http://localhost:5173
2. 选择一本小说
3. 在右侧面板点击「流程」标签页
4. 点击「大纲」，确认切换到新会话
5. 发送消息，确认提示词前缀被添加
6. 切换到「正文」，发送消息
7. 切换回「大纲」，确认之前的大纲会话已恢复

- [ ] **Step 4: 测试配置**

1. 打开配置弹窗
2. 进入「提示词模板」标签页
3. 添加新流程，填写名称和提示词
4. 保存后在流程标签页确认显示
5. 删除流程，确认已移除

- [ ] **Step 5: 提交**

```bash
git add .
git commit -m "feat: complete writing flows feature"
```

---

## 执行方式

**Plan complete and saved to `docs/superpowers/plans/2026-05-10-writing-flows-plan.md`.**

Two execution options:

1. **Subagent-Driven (recommended)** - 分派子任务执行，两阶段审查
2. **Inline Execution** - 当前会话批量执行，嵌入审查点

选择哪种方式？
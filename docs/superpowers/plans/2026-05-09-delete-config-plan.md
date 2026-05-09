# 删除小说与系统配置功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在前端添加删除小说按钮和系统配置页面（API配置 + 提示词模板）

**Architecture:** 后端已有 ModelConfig 和 PromptButton 表，可复用。前端在左侧边栏添加配置按钮，点击弹出配置弹窗。删除小说按钮直接显示在每本小说旁边。

**Tech Stack:** Vue 3 + Pinia + Tailwind CSS, FastAPI + SQLAlchemy + SQLite

---

## Task 1: 后端 - 验证/扩展 ModelConfig DELETE API

**Files:**
- Modify: `backend/app/routers/model_configs.py`

- [ ] **Step 1: 添加 DELETE API**

在 `model_configs.py` 文件末尾添加：

```python
@router.delete("/model-configs/{config_id}")
def delete_model_config(config_id: int, db: Session = Depends(get_db)):
    config = db.get(ModelConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="ModelConfig not found")
    db.delete(config)
    db.commit()
    return {"deleted": True}
```

- [ ] **Step 2: 添加 PUT API（更新配置）**

```python
@router.put("/model-configs/{config_id}", response_model=ModelConfigResponse)
def update_model_config(config_id: int, config: ModelConfigCreate, db: Session = Depends(get_db)):
    db_config = db.get(ModelConfig, config_id)
    if not db_config:
        raise HTTPException(status_code=404, detail="ModelConfig not found")
    for key, value in config.model_dump(exclude_none=True).items():
        setattr(db_config, key, value)
    db.commit()
    db.refresh(db_config)
    return db_config
```

- [ ] **Step 3: 测试 DELETE API**

Run: `curl -X DELETE http://localhost:8000/api/model-configs/1`
Expected: `{"deleted": true}`

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/model_configs.py
git commit -m "feat: add DELETE and PUT for model-configs API"
```

---

## Task 2: 后端 - 验证/扩展 PromptButton CRUD

**Files:**
- Check: `backend/app/routers/` 是否有 prompts.py

- [ ] **Step 1: 检查 prompts.py 文件**

```bash
ls backend/app/routers/prompts.py
```

- [ ] **Step 2: 如果存在，检查是否有 DELETE**

如果没有，需要添加。如果已存在且有 DELETE，跳过此步骤。

- [ ] **Step 3: Commit（如果有改动）**

---

## Task 3: 前端 - 添加删除小说功能

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/stores/chat.ts`

- [ ] **Step 1: 在 store 添加 deleteNovel 方法**

在 `chat.ts` 的 return 语句前添加：

```typescript
const deleteNovel = async (id: number) => {
  await axios.delete('/api/novels/' + id)
  novels.value = novels.value.filter(n => n.id !== id)
  if (currentNovel.value?.id === id) {
    currentNovel.value = null
    messages.value = []
  }
}
```

在 return 中添加：
```typescript
return {
  // ...existing
  deleteNovel
}
```

- [ ] **Step 2: 在 App.vue 添加删除按钮**

在小说列表项中添加删除图标按钮：

```vue
<div class="flex items-center justify-between">
  <span>{{ novel.title }}</span>
  <button @click.stop="confirmDelete(novel)" class="text-red-500 hover:text-red-700">
    🗑️
  </button>
</div>
```

- [ ] **Step 3: 添加确认删除方法**

在 script 中添加：

```typescript
const confirmDelete = (novel: Novel) => {
  if (confirm(`确定删除小说《${novel.title}》吗？此操作不可撤销。`)) {
    store.deleteNovel(novel.id)
  }
}
```

- [ ] **Step 4: 测试功能**

验证：
1. 打开前端页面
2. 鼠标悬停在某本小说上
3. 点击删除按钮
4. 确认弹窗出现
5. 点击确认，小说从列表消失

- [ ] **Step 5: Commit**

```bash
git add frontend/src/App.vue frontend/src/stores/chat.ts
git commit -m "feat: add delete novel functionality"
```

---

## Task 4: 前端 - 添加配置按钮和弹窗

**Files:**
- Modify: `frontend/src/App.vue`
- Modify: `frontend/src/stores/chat.ts`

- [ ] **Step 1: 在 store 添加配置相关方法**

在 `chat.ts` 添加：

```typescript
const systemConfig = ref({
  apiKey: '',
  defaultModel: 'gpt-4',
  isDefault: false
})
const promptTemplates = ref([
  { name: '总结', content: '请总结以上内容要点：' },
  { name: '润色', content: '请润色以下内容：' },
  { name: '续写', content: '请续写：' },
  { name: '扩写', content: '请扩写：' }
])

const fetchSystemConfig = async () => {
  const res = await axios.get('/api/model-configs')
  if (res.data.length > 0) {
    const config = res.data[0]
    systemConfig.value = {
      apiKey: config.api_key || '',
      defaultModel: config.model,
      isDefault: false
    }
  }
}

const saveSystemConfig = async () => {
  await axios.post('/api/model-configs', {
    provider: 'openai',
    model: systemConfig.value.defaultModel,
    api_key: systemConfig.value.apiKey,
    temperature: 0.7,
    max_tokens: 4096
  })
}

const fetchPromptTemplates = async () => {
  const res = await axios.get('/api/prompt-buttons')
  promptTemplates.value = res.data.map((b: any) => ({ name: b.name, content: b.content }))
}

const savePromptTemplates = async () => {
  for (const t of promptTemplates.value) {
    await axios.post('/api/prompt-buttons', {
      name: t.name,
      button_type: 'prompt',
      content: t.content,
      category: 'default'
    })
  }
}
```

在 return 中添加：
```typescript
return {
  // ...existing
  systemConfig,
  promptTemplates,
  fetchSystemConfig,
  saveSystemConfig,
  fetchPromptTemplates,
  savePromptTemplates
}
```

- [ ] **Step 2: 在 App.vue 添加配置按钮**

在 [+ 新建] 按钮后添加：

```vue
<button
  @click="openConfig"
  class="mt-4 w-full py-2 border rounded flex items-center justify-center gap-2 hover:bg-gray-100"
>
  ⚙️ 配置
</button>
```

- [ ] **Step 3: 添加配置弹窗组件**

在 template 末尾添加：

```vue
<!-- 配置弹窗 -->
<div v-if="showConfig" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
  <div class="bg-white rounded-lg w-[500px] max-h-[80vh] overflow-y-auto">
    <div class="flex items-center justify-between p-4 border-b">
      <span class="font-bold">⚙️ 系统配置</span>
      <button @click="showConfig = false">✕</button>
    </div>
    <div class="flex border-b">
      <button
        @click="configTab = 'api'"
        class="px-4 py-2"
        :class="configTab === 'api' ? 'border-b-2 border-blue-500' : ''"
      >
        API配置
      </button>
      <button
        @click="configTab = 'prompt'"
        class="px-4 py-2"
        :class="configTab === 'prompt' ? 'border-b-2 border-blue-500' : ''"
      >
        提示词模板
      </button>
    </div>
    <div class="p-4">
      <!-- API配置 Tab -->
      <div v-if="configTab === 'api'">
        <div class="mb-4">
          <label class="block text-sm mb-1">API Key</label>
          <input
            v-model="store.systemConfig.apiKey"
            type="password"
            class="w-full border rounded p-2"
          />
        </div>
        <div class="mb-4">
          <label class="block text-sm mb-1">模型</label>
          <select v-model="store.systemConfig.defaultModel" class="w-full border rounded p-2">
            <option value="gpt-4">GPT-4</option>
            <option value="gpt-4o">GPT-4o</option>
            <option value="gpt-4o-mini">GPT-4o-mini</option>
          </select>
        </div>
      </div>
      <!-- 提示词模板 Tab -->
      <div v-if="configTab === 'prompt'">
        <div v-for="(t, idx) in store.promptTemplates" :key="idx" class="mb-4">
          <label class="block text-sm mb-1">{{ t.name }}</label>
          <textarea
            v-model="t.content"
            class="w-full border rounded p-2"
            rows="2"
          ></textarea>
        </div>
      </div>
    </div>
    <div class="flex justify-end gap-2 p-4 border-t">
      <button @click="showConfig = false" class="px-4 py-2 border rounded">取消</button>
      <button @click="saveConfig" class="px-4 py-2 bg-blue-500 text-white rounded">保存</button>
    </div>
  </div>
</div>
```

- [ ] **Step 4: 添加相关变量和方法**

在 script 中添加：

```typescript
const showConfig = ref(false)
const configTab = ref('api')

const openConfig = async () => {
  showConfig.value = true
  await store.fetchSystemConfig()
  await store.fetchPromptTemplates()
}

const saveConfig = async () => {
  await store.saveSystemConfig()
  await store.savePromptTemplates()
  showConfig.value = false
}
```

- [ ] **Step 5: 测试功能**

验证：
1. 点击配置按钮，弹窗出现
2. 可以切换 API配置 / 提示词模板 两个 Tab
3. 可以输入 API Key 和选择模型
4. 可以编辑提示词模板
5. 点击保存，弹窗关闭

- [ ] **Step 6: Commit**

```bash
git add frontend/src/App.vue frontend/src/stores/chat.ts
git commit -m "feat: add system config dialog with API and prompt templates"
```

---

## 验证清单

- [ ] 小说列表每项有删除按钮
- [ ] 点击删除按钮弹出确认框
- [ ] 确认后小说被删除
- [ ] 左侧边栏底部有配置按钮
- [ ] 点击配置按钮弹出配置弹窗
- [ ] 弹窗有两个 Tab：API配置 和 提示词模板
- [ ] API配置可以输入 API Key 和选择模型
- [ ] 提示词模板可以编辑快捷按钮的提示词
- [ ] 保存后数据正确提交到后端
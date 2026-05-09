# DeepSeek + Custom Provider 支持实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标:** 在前端配置界面添加 Provider 下拉框（OpenAI / DeepSeek / Custom），支持 DeepSeek 和自定义 API

**架构:** 前端 App.vue 中添加 Provider 选择，store 中保存 provider 和 base_url。custom 模式显示额外输入框。

**Tech Stack:** Vue 3 + Pinia + Tailwind CSS

---

### Task 1: 更新 Chat Store 添加 provider 和 baseUrl 字段

**Files:**
- Modify: `frontend/src/stores/chat.ts:83-116`

- [ ] **Step 1: 添加 providerTemplates 常量**

在 `promptTemplates` 之后添加：

```typescript
const providerTemplates = {
  openai: {
    base_url: 'https://api.openai.com/v1',
    models: ['gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']
  },
  deepseek: {
    base_url: 'https://api.deepseek.com',
    models: ['deepseek-chat']
  },
  custom: {
    base_url: '',
    models: []
  }
}
```

- [ ] **Step 2: 修改 systemConfig 初始化**

修改 `systemConfig` 初始值：

```typescript
const systemConfig = ref({
  provider: 'openai',      // 新增
  baseUrl: '',             // 新增
  model: 'gpt-4',
  apiKey: '',
  temperature: 0.7,
  maxTokens: 4096
})
```

- [ ] **Step 3: 修改 fetchSystemConfig**

更新 `fetchSystemConfig` 函数，支持加载 provider 和 base_url：

```typescript
const fetchSystemConfig = async () => {
  const res = await axios.get('/api/model-configs')
  if (res.data.length > 0) {
    const config = res.data[0]
    const provider = config.provider || 'openai'
    systemConfig.value = {
      provider: provider,
      baseUrl: config.base_url || providerTemplates[provider]?.base_url || '',
      model: config.model || 'gpt-4',
      apiKey: config.api_key || '',
      temperature: config.temperature || 0.7,
      maxTokens: config.max_tokens || 4096
    }
  }
}
```

- [ ] **Step 4: 修改 saveSystemConfig**

更新 `saveSystemConfig` 函数，保存 provider 和 base_url：

```typescript
const saveSystemConfig = async () => {
  await axios.post('/api/model-configs', {
    provider: systemConfig.value.provider,
    base_url: systemConfig.value.baseUrl,
    model: systemConfig.value.model,
    api_key: systemConfig.value.apiKey,
    temperature: systemConfig.value.temperature,
    max_tokens: systemConfig.value.maxTokens
  })
}
```

- [ ] **Step 5: 导出可用模型列表函数**

在 return 之前添加：

```typescript
const getModelsForProvider = (provider: string) => {
  return providerTemplates[provider]?.models || []
}
```

更新 return：

```typescript
return {
  // ... existing
  getModelsForProvider,
  providerTemplates
}
```

---

### Task 2: 更新 App.vue 配置界面

**Files:**
- Modify: `frontend/src/App.vue:119-135`

- [ ] **Step 1: 添加 Provider 下拉框**

在 API配置 tab 的第一个字段（API Key 之前）添加：

```vue
<div class="mb-4">
  <label class="block text-sm mb-1">Provider</label>
  <select v-model="store.systemConfig.provider" class="w-full border rounded p-2">
    <option value="openai">OpenAI</option>
    <option value="deepseek">DeepSeek</option>
    <option value="custom">Custom</option>
  </select>
</div>
```

- [ ] **Step 2: 修改模型下拉框为动态选项**

替换静态 model 下拉框：

```vue
<div class="mb-4">
  <label class="block text-sm mb-1">模型</label>
  <select
    v-model="store.systemConfig.model"
    class="w-full border rounded p-2"
    :disabled="store.systemConfig.provider === 'custom'"
  >
    <option
      v-for="model in store.getModelsForProvider(store.systemConfig.provider)"
      :key="model"
      :value="model"
    >
      {{ model.toUpperCase() }}
    </option>
    <option v-if="store.systemConfig.provider === 'custom'" value="">
      自定义模型
    </option>
  </select>
</div>
```

- [ ] **Step 3: 添加 Custom 模式的 Base URL 输入框**

在模型选择之后添加（v-if="store.systemConfig.provider === 'custom'"）：

```vue
<div v-if="store.systemConfig.provider === 'custom'" class="mb-4">
  <label class="block text-sm mb-1">Base URL</label>
  <input
    v-model="store.systemConfig.baseUrl"
    type="text"
    placeholder="https://api.example.com/v1"
    class="w-full border rounded p-2"
  />
</div>
```

- [ ] **Step 4: 添加 Custom 模式的模型输入框**

在 Base URL 之后添加（当 custom 且模型为空时显示）：

```vue
<div v-if="store.systemConfig.provider === 'custom' && !store.getModelsForProvider(store.systemConfig.provider).includes(store.systemConfig.model)" class="mb-4">
  <label class="block text-sm mb-1">模型名称</label>
  <input
    v-model="store.systemConfig.model"
    type="text"
    placeholder="e.g. claude-3-opus"
    class="w-full border rounded p-2"
  />
</div>
```

- [ ] **Step 5: 添加 Temperature 和 Max Tokens**

在其他字段之后添加：

```vue
<div class="mb-4">
  <label class="block text-sm mb-1">Temperature: {{ store.systemConfig.temperature }}</label>
  <input
    v-model="store.systemConfig.temperature"
    type="range"
    min="0"
    max="2"
    step="0.1"
    class="w-full"
  />
</div>
<div class="mb-4">
  <label class="block text-sm mb-1">Max Tokens: {{ store.systemConfig.maxTokens }}</label>
  <input
    v-model="store.systemConfig.maxTokens"
    type="number"
    min="1"
    max="128000"
    class="w-full border rounded p-2"
  />
</div>
```

---

### Task 3: 测试验证

**Files:**
- Test: 手动测试

- [ ] **Step 1: 测试 OpenAI Provider**

1. 打开配置界面
2. 选择 OpenAI
3. 确认模型下拉框显示: GPT-4, GPT-4O, GPT-4O-MINI, GPT-3.5-TURBO
4. 填写 API Key
5. 保存配置

- [ ] **Step 2: 测试 DeepSeek Provider**

1. 切换到 DeepSeek
2. 确认模型下拉框显示: DEEPSEEK-CHAT
3. 填写 API Key
4. 保存配置

- [ ] **Step 3: 测试 Custom Provider**

1. 切换到 Custom
2. 确认显示 Base URL 输入框
3. 确认显示模型名称输入框
4. 填写自定义 base_url 和 model
5. 保存配置

- [ ] **Step 4: 验证数据持久化**

1. 重新打开配置界面
2. 确认之前保存的配置已正确加载
3. 确认 provider、base_url、model 都已保存

---

### Task 4: 提交代码

- [ ] **Step 1: 添加并提交更改**

```bash
git add frontend/src/stores/chat.ts frontend/src/App.vue
git commit -m "feat: add DeepSeek + Custom provider support"
```
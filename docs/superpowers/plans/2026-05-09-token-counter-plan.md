# Token 使用计数显示实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在会话框底部显示当前会话累计使用的 token 数量

**Architecture:** 后端在 SSE 流结束后返回 usage 数据，前端解析并累加到 sessionTokens，在输入框附近显示计数

**Tech Stack:** Vue 3 + Pinia, FastAPI + httpx

---

## 文件结构

### Modify: `backend/app/adapters/openai.py`
- 在 `stream_message` 方法中，SSE 流结束后提取 usage 并发送

### Modify: `frontend/src/stores/chat.ts`
- 添加 `sessionTokens` ref
- 修改解析逻辑，检测并累加 usage 数据

### Modify: `frontend/src/App.vue`
- 在输入框下方显示 token 计数

---

## Task 1: 后端返回 usage 数据

###  Files:
- Modify: `backend/app/adapters/openai.py:42-62`

- [ ] **Step 1: 查看 OpenAI API 返回 usage 的方式**

OpenAI/DeepSeek API 在流式响应中，usage 数据在响应头 `x-usage` 或最后的 SSE 消息中。需要确认具体格式。

```python
# 在 stream_message 方法末尾，遍历完后添加 usage
# httpx 流式响应可以通过 response.headers 获取 usage
```

- [ ] **Step 2: 修改 stream_message 方法**

在 `stream_message` 方法的最后，提取 usage 并以 SSE 格式发送：

```python
def stream_message(self, messages: list, config: dict):
    url = f"{self.base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": config.get("model", self.model),
        "messages": messages,
        "temperature": config.get("temperature", 0.7),
        "max_tokens": config.get("max_tokens", 4096),
        "stream": True
    }
    extra_params = self._build_extra_params(config)
    data.update(extra_params)

    with httpx.Client(timeout=30.0) as client:
        with client.stream("POST", url, json=data, headers=headers) as response:
            response.raise_for_status()
            full_response = ""
            for chunk in response.iter_text():
                full_response += chunk
                if chunk.strip():
                    yield chunk
            
            # 解析完整响应获取 usage
            # 注意：需要记录 messages 的 token 数
            # OpenAI API usage 在最后的非流式响应或响应头中
```

**注意**：OpenAI 的流式响应不直接包含 usage，需要：
1. 方案A：发送两次请求（非流式获取 usage，流式发送内容）
2. 方案B：从响应头 `x-usage` 获取

推荐方案B，因为更高效。

- [ ] **Step 3: 测试后端返回**

```bash
# 启动后端并测试 chat 接口
curl -X POST http://localhost:8000/api/chat ...
# 检查返回是否包含 usage
```

---

## Task 2: 前端解析 usage

### Files:
- Modify: `frontend/src/stores/chat.ts:55-133`

- [ ] **Step 1: 添加 sessionTokens ref**

在 store 开头添加：
```typescript
const sessionTokens = ref(0)
```

- [ ] **Step 2: 修改解析逻辑**

在 `while (true)` 循环后，检测 usage 格式：

```typescript
// 检测 usage 格式
try {
  const json = JSON.parse(data)
  if (json.usage) {
    const prompt = json.usage.prompt_tokens || 0
    const completion = json.usage.completion_tokens || 0
    sessionTokens.value += prompt + completion
  }
} catch {
  // Not JSON, ignore
}
```

- [ ] **Step 3: 导出 sessionTokens**

在 return 中添加：
```typescript
sessionTokens,
```

---

## Task 3: UI 显示 Token 计数

### Files:
- Modify: `frontend/src/App.vue:56-78`

- [ ] **Step 1: 在输入框下方添加显示**

在输入框 div 中，p-4 下面的结构：

```html
<div class="mt-2 flex items-center justify-between">
  <div class="flex gap-2">
    <button
      v-for="btn in promptButtons"
      :key="btn.name"
      @click="sendWithPrompt(btn)"
      class="px-3 py-1 border rounded hover:bg-gray-100"
    >
      {{ btn.name }}
    </button>
  </div>
  <div class="text-sm text-gray-500">
    Tokens: {{ store.sessionTokens.toLocaleString() }}
  </div>
</div>
```

- [ ] **Step 2: 测试 UI 显示**

启动前端，检查输入框下方是否显示 "Tokens: 0"

---

## Task 4: 集成测试

- [ ] **Step 1: 完整流程测试**

1. 启动后端服务
2. 启动前端服务
3. 选择/创建小说
4. 发送消息
5. 检查 token 计数是否更新

- [ ] **Step 2: 验证数据准确性**

对比后端日志和前端显示的 token 数

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-09-token-counter-plan.md`. 两个执行选项：**

**1. Subagent-Driven (recommended)** - 我 dispatch 一个 fresh subagent per task，review between tasks，fast iteration

**2. Inline Execution** - 使用 executing-plans 在此 session 中执行

**Which approach?**
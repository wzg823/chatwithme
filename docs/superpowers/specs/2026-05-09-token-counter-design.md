# Token 使用计数显示设计

## 目标
在会话框底部（输入框旁边）显示当前会话累计使用的 token 数量。

## 实现方案

### 后端改动
在 SSE 流结束后，发送 usage 数据：
```
data: {"usage": {"prompt_tokens": N, "completion_tokens": M}}
data: [DONE]
```

OpenAI/DeepSeek API 会在响应头的 `x Usage` 或响应体最后返回 usage 数据。

### 前端改动
1. **store/chat.ts**: 添加 `sessionTokens` ref，解析并累加 usage
2. **App.vue**: 在输入框下方显示 token 计数

## 技术细节

### 后端实现
在 `adapter.stream_message` 中，需要处理最后的 usage：
- OpenAI API：`response.meta()` 或 `response.json()` 中的 `usage` 字段
- SSE 结束时发送最后的 usage

### 前端解析
修改 [chat.ts:96-113](frontend/src/stores/chat.ts#L96-L113) 的解析逻辑，在 buffer 处理时检测 usage 块：
```
// 检测 usage 格式
try {
  const json = JSON.parse(data)
  if (json.usage) {
    totalTokens += json.usage.prompt_tokens + json.usage.completion_tokens
  }
}
```

### UI 显示
位置：输入框右侧或下方
格式：`Tokens: 1,234` 或 `本次会话: 1.2K tokens`

## 文件修改清单
1. `backend/app/adapters/openai.py` - 添加 usage 返回
2. `frontend/src/stores/chat.ts` - 添加 sessionTokens 状态
3. `frontend/src/App.vue` - 显示 token 计数
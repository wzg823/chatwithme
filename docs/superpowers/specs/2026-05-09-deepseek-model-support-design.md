---
name: deepseek-model-support
description: Add DeepSeek + Custom model provider options with configuration UI
---

# DeepSeek + Custom 模型支持设计

## 目标

在配置界面添加 Provider 选择（OpenAI / DeepSeek / Custom），允许用户选择使用不同模型提供商，并能分别配置各自的 API Key。

## 数据模型

### ModelConfig 表结构（已有）

| 字段 | 类型 | 说明 |
|------|------|------|
| provider | String | 模型提供商：openai / deepseek / custom |
| base_url | String | API 基础地址（custom 时必填） |
| model | String | 模型名称 |
| api_key | String | API Key |
| temperature | Float | 温度参数 |
| max_tokens | Integer | 最大 token 数 |

### 预设 Provider 模板

| Provider | base_url | 可用模型 |
|----------|----------|----------|
| OpenAI | https://api.openai.com/v1 | gpt-4, gpt-4-turbo, gpt-3.5-turbo |
| DeepSeek | https://api.deepseek.com | deepseek-chat |
| Custom | 用户手动输入 | 用户手动输入 |

## 后端设计

### API 端点（已有）

`/api/model-configs` - CRUD 操作已存在，无需大改

### 修改点

- `chat.py` 的 `get_adapter` 函数已支持 deepseek，无需修改

## 前端设计

### 配置界面

```
┌─────────────────────────────────────┐
│ [API 配置] [Prompt 模板]             │
├─────────────────────────────────────┤
│ Provider: [OpenAI ▼]                │
│                                    │
│ Model:      [gpt-4 ▼]               │
│                                    │
│ API Key:    [**************] [显示]   │
│                                    │
│ Temperature: [0.7] (范围 0-2)       │
│ Max Tokens:  [4096] (范围 1-128000)│
│                                    │
│ [保存配置]                          │
└─────────────────────────────────────┘
```

当选择 Custom 时，额外显示：

```
│ Base URL: [https://api.example.com] │
│ Model:    [_______________]         │
```

### Provider 联动逻辑

```javascript
const providerTemplates = {
  openai: {
    base_url: 'https://api.openai.com/v1',
    models: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
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

选择 Provider 时：
1. 自动填充 base_url（custom 除外）
2. 更新 Model 下拉框选项
3. custom 模式显示额外 base_url 输入框

### 状态管理

```typescript
const systemConfig = ref({
  provider: 'openai',     // 新增
  baseUrl: '',            // 新增
  model: 'gpt-4',
  apiKey: '',
  temperature: 0.7,
  maxTokens: 4096
})
```

## 实现步骤

1. 前端配置界面添加 Provider 下拉框
2. 实现 Provider 联动 Model 下拉框逻辑
3. custom 模式显示 base_url 输入框
4. 修改保存逻辑，包含 provider 和 base_url
5. 区分不同 provider 的 API Key 存储

## 注意事项

- 切换 provider 时自动更新 model 选项
- 保持向后兼容：旧数据没有 provider 默认为 openai
- Custom 模式下 base_url 和 model 都需要用户手动输入
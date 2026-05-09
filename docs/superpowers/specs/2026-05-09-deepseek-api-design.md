# DeepSeek API 接入设计

## 概述

为项目添加 DeepSeek API 支持，让用户可以在对话时选择使用哪个模型，并支持设置默认模型。

## 1. 数据库层

### 新增表：UserModelPreference

```python
class UserModelPreference(Base):
    __tablename__ = "user_model_preferences"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=True)  # 如果有多用户系统
    model_config_id = Column(Integer, ForeignKey("model_configs.id"))
    is_default = Column(Boolean, default=False)
```

现有的 `ModelConfig` 表无需修改，已包含：
- provider: 提供商 (openai/deepseek)
- base_url: API 端点
- model: 模型名
- api_key: API 密钥
- temperature, max_tokens: 生成参数

## 2. Adapter 层

修改 `OpenAIAdapter` 类的初始化和调用逻辑：

```python
class OpenAIAdapter(ModelAdapter):
    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model

    def _build_extra_params(self, config: dict) -> dict:
        """构建 DeepSeek 特有参数"""
        extra = {}
        if config.get("reasoning_effort"):
            extra["reasoning_effort"] = config["reasoning_effort"]
        if config.get("thinking"):
            extra["thinking"] = config["thinking"]
        return extra
```

修改 `get_adapter()` 函数支持动态配置：

```python
def get_adapter(model_config: ModelConfig):
    if model_config.provider == "openai" or model_config.provider == "deepseek":
        from app.adapters.openai import OpenAIAdapter
        return OpenAIAdapter(
            api_key=model_config.api_key,
            base_url=model_config.base_url,
            model=model_config.model
        )
    return None
```

## 3. API 层

修改 `/chat` 接口：

```python
@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. 获取 novel 和消息
    novel = db.query(Novel).filter(Novel.id == request.novel_id).first()
    messages = [{"role": m.role, "content": m.content} for m in novel.messages]
    if request.messages:
        for user_msg in request.messages:
            msg = Message(role=user_msg["role"], content=user_msg["content"], novel_id=novel.id)
            db.add(msg)
            messages.append({"role": user_msg["role"], "content": user_msg["content"]})
    db.commit()

    # 2. 获取模型配置（优先使用请求中的 model_config_id）
    model_config_id = request.model_config_id
    if not model_config_id:
        # 尝试获取用户默认模型
        pref = db.query(UserModelPreference).filter(...).first()
        if pref:
            model_config_id = pref.model_config_id
    
    model_config = db.query(ModelConfig).filter(ModelConfig.id == model_config_id).first()
    
    # 3. 调用适配器
    adapter = get_adapter(model_config)
    config = {
        "model": model_config.model,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
        "reasoning_effort": request.reasoning_effort,
        "thinking": request.thinking
    }

    def generate():
        for chunk in adapter.stream_message(messages, config):
            yield chunk

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 新增接口

- `GET /model-configs`: 获取可用模型列表
- `POST /model-configs`: 创建模型配置
- `GET /user-model-preferences`: 获取用户默认模型
- `POST /user-model-preferences`: 设置用户默认模型

## 4. 前端层

### 模型选择下拉框

在对话页面添加模型选择器：
- 显示可用模型列表（provider + model 名）
- 支持搜索过滤

### 设置页面

- 可以添加/编辑模型配置
- 可以设置默认模型
- 可以删除未使用的配置

### 支持的模型

| 模型名 | 提供商 | 说明 |
|-------|--------|------|
| gpt-4 | OpenAI | 通用 |
| deepseek-v4-flash | DeepSeek | 性价比高 |
| deepseek-v4-pro | DeepSeek | 高质量 |
| deepseek-reasoner | DeepSeek | 思考模型 |

## 5. DeepSeek 特殊参数

根据 DeepSeek 文档，支持以下参数：

- `reasoning_effort`: 思考强度 (low/medium/high)
- `thinking`: 思考类型配置

这些参数通过 ChatRequest 传入。

## 6. 错误处理

- API Key 无效：返回 401 错误
- API 调用失败：返回具体错误信息
- 网络超时：返回超时错误
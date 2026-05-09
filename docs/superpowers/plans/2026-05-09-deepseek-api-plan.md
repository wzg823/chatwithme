# DeepSeek API 接入实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为项目添加 DeepSeek API 支持，让用户可以选择使用哪个模型，并支持设置默认模型。

**Architecture:** 
- 新增 `UserModelPreference` 模型存储用户默认模型选择
- 修改 `OpenAIAdapter` 支持传入 ModelConfig 对象
- 新增路由 `/model-configs` 和 `/user-model-preferences`
- 修改 `/chat` 接口支持 model_config_id 参数

**Tech Stack:** FastAPI, SQLAlchemy, httpx

---

### Task 1: 添加 UserModelPreference 模型

**Files:**
- Modify: `.worktrees/chatwithme-v1/backend/app/models/models.py`

- [ ] **Step 1: 添加 UserModelPreference 模型类**

```python
class UserModelPreference(Base):
    __tablename__ = "user_model_preferences"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    model_config_id = Column(Integer, ForeignKey("model_configs.id"))
    is_default = Column(Boolean, default=False)
```

- [ ] **Step 2: 提交**

```bash
git add .worktrees/chatwithme-v1/backend/app/models/models.py
git commit -m "feat: add UserModelPreference model"
```

---

### Task 2: 更新 ChatRequest Schema

**Files:**
- Modify: `.worktrees/chatwithme-v1/backend/app/models/schemas.py`

- [ ] **Step 1: 添加新字段到 ChatRequest**

```python
class ChatRequest(BaseModel):
    novel_id: int
    messages: list
    prompt_buttons: Optional[list] = None
    model_config_id: Optional[int] = None
    reasoning_effort: Optional[str] = None
    thinking: Optional[dict] = None
```

- [ ] **Step 2: 提交**

```bash
git add .worktrees/chatwithme-v1/backend/app/models/schemas.py
git commit -m "feat: add model_config_id to ChatRequest schema"
```

---

### Task 3: 创建模型配置路由

**Files:**
- Create: `.worktrees/chatwithme-v1/backend/app/routers/model_configs.py`

- [ ] **Step 1: 创建 model_configs 路由**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import ModelConfig, UserModelPreference
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ModelConfigCreate(BaseModel):
    provider: str
    base_url: Optional[str] = None
    model: str
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096

class ModelConfigResponse(ModelConfigCreate):
    id: int

    class Config:
        from_attributes = True

class UserModelPreferenceCreate(BaseModel):
    user_id: Optional[int] = None
    model_config_id: int
    is_default: bool = True

class UserModelPreferenceResponse(BaseModel):
    id: int
    user_id: Optional[int]
    model_config_id: int
    is_default: bool

    class Config:
        from_attributes = True

@router.get("/model-configs", response_model=list[ModelConfigResponse])
def list_model_configs(db: Session = Depends(get_db)):
    return db.query(ModelConfig).all()

@router.post("/model-configs", response_model=ModelConfigResponse)
def create_model_config(config: ModelConfigCreate, db: Session = Depends(get_db)):
    db_config = ModelConfig(**config.model_dump(exclude_none=True))
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

@router.get("/user-model-preferences", response_model=list[UserModelPreferenceResponse])
def list_user_model_preferences(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(UserModelPreference)
    if user_id is not None:
        query = query.filter(UserModelPreference.user_id == user_id)
    return query.all()

@router.post("/user-model-preferences", response_model=UserModelPreferenceResponse)
def create_user_model_preference(pref: UserModelPreferenceCreate, db: Session = Depends(get_db)):
    # 如果设置默认，先清除其他默认
    if pref.is_default:
        db.query(UserModelPreference).filter(
            UserModelPreference.user_id == pref.user_id,
            UserModelPreference.is_default == True
        ).update({"is_default": False})
    
    db_pref = UserModelPreference(**pref.model_dump())
    db.add(db_pref)
    db.commit()
    db.refresh(db_pref)
    return db_pref
```

- [ ] **Step 2: 注册路由到 main.py**

```python
from app.routers import chat, novels, model_configs
# ...
app.include_router(model_configs.router, prefix="/api")
```

- [ ] **Step 3: 提交**

```bash
git add .worktrees/chatwithme-v1/backend/app/routers/model_configs.py .worktrees/chatwithme-v1/backend/app/main.py
git commit -m "feat: add model configs and user preferences endpoints"
```

---

### Task 4: 修改 Chat 接口支持模型选择

**Files:**
- Modify: `.worktrees/chatwithme-v1/backend/app/routers/chat.py`

- [ ] **Step 1: 修改 chat 接口获取模型配置**

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Message, Novel, ModelConfig, UserModelPreference
from app.models.schemas import ChatRequest

router = APIRouter()

def get_adapter(model_config: ModelConfig):
    if model_config.provider in ("openai", "deepseek"):
        from app.adapters.openai import OpenAIAdapter
        return OpenAIAdapter(
            api_key=model_config.api_key,
            base_url=model_config.base_url,
            model=model_config.model
        )
    return None

@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    novel = db.query(Novel).filter(Novel.id == request.novel_id).first()

    messages = [{"role": m.role, "content": m.content} for m in novel.messages]
    if request.messages:
        for user_msg in request.messages:
            msg = Message(role=user_msg["role"], content=user_msg["content"], novel_id=novel.id)
            db.add(msg)
            messages.append({"role": user_msg["role"], "content": user_msg["content"]})
    db.commit()

    # 获取模型配置
    model_config_id = request.model_config_id
    if not model_config_id:
        # 尝试获取用户默认模型
        pref = db.query(UserModelPreference).filter(
            UserModelPreference.is_default == True
        ).first()
        if pref:
            model_config_id = pref.model_config_id
    
    if not model_config_id:
        # 使用默认配置
        model_config = db.query(ModelConfig).first()
        if not model_config:
            model_config = ModelConfig(
                provider="openai",
                model="gpt-4",
                temperature=0.7,
                max_tokens=4096
            )
            db.add(model_config)
            db.commit()
            db.refresh(model_config)
    else:
        model_config = db.query(ModelConfig).filter(ModelConfig.id == model_config_id).first()

    adapter = get_adapter(model_config)
    
    config = {
        "model": model_config.model,
        "temperature": model_config.temperature,
        "max_tokens": model_config.max_tokens,
    }
    
    if request.reasoning_effort:
        config["reasoning_effort"] = request.reasoning_effort
    if request.thinking:
        config["thinking"] = request.thinking

    def generate():
        for chunk in adapter.stream_message(messages, config):
            yield chunk

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/novels/{novel_id}/messages")
def get_messages(novel_id: int, db: Session = Depends(get_db)):
    return db.query(Message).filter(Message.novel_id == novel_id).all()
```

- [ ] **Step 2: 提交**

```bash
git add .worktrees/chatwithme-v1/backend/app/routers/chat.py
git commit -m "feat: support model selection in chat endpoint"
```

---

### Task 5: 修改 Adapter 支持 DeepSeek 参数

**Files:**
- Modify: `.worktrees/chatwithme-v1/backend/app/adapters/openai.py`

- [ ] **Step 1: 添加 DeepSeek 特殊参数支持**

```python
import httpx
from app.adapters.base import ModelAdapter

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

    def send_message(self, messages: list, config: dict) -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": config.get("model", self.model),
            "messages": messages,
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 4096)
        }
        # 添加 DeepSeek 特有参数
        extra_params = self._build_extra_params(config)
        data.update(extra_params)
        
        with httpx.Client() as client:
            response = client.post(url, json=data, headers=headers)
            return response.json()["choices"][0]["message"]["content"]

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
        # 添加 DeepSeek 特有参数
        extra_params = self._build_extra_params(config)
        data.update(extra_params)
        
        with httpx.Client() as client:
            with client.stream("POST", url, json=data, headers=headers) as response:
                for chunk in response.iter_text():
                    if chunk.startswith("data: "):
                        yield chunk[6:]
```

- [ ] **Step 2: 提交**

```bash
git add .worktrees/chatwithme-v1/backend/app/adapters/openai.py
git commit -m "feat: support DeepSeek extra parameters in adapter"
```

---

### Task 6: 添加默认 DeepSeek 模型配置

**Files:**
- Modify: `.worktrees/chatwithme-v1/backend/app/models/database.py` 或新建迁移脚本

- [ ] **Step 1: 添加默认 DeepSeek 模型配置**

可以在首次运行时自动添加默认配置，或者提供 SQL 迁移脚本：

```sql
-- 默认模型配置
INSERT INTO model_configs (provider, base_url, model, api_key, temperature, max_tokens)
VALUES 
  ('openai', 'https://api.openai.com/v1', 'gpt-4', NULL, 0.7, 4096),
  ('deepseek', 'https://api.deepseek.com', 'deepseek-v4-flash', NULL, 0.7, 4096),
  ('deepseek', 'https://api.deepseek.com', 'deepseek-v4-pro', NULL, 0.7, 4096),
  ('deepseek', 'https://api.deepseek.com', 'deepseek-reasoner', NULL, 0.7, 4096);
```

- [ ] **Step 2: 提交**

```bash
git add docs/superpowers/plans/2026-05-09-deepseek-api-plan.md
git commit -m "docs: add default DeepSeek model configs"
```

---

## 执行选项

**Plan complete and saved to `docs/superpowers/plans/2026-05-09-deepseek-api-plan.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
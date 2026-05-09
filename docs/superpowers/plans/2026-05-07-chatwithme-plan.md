# ChatWithMe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个基于 PromptChat 风格的小说创作工作流应用，通过系统注入型按钮触发创作各阶段的上下文整理

**Architecture:** Vue 3 前端 + FastAPI 后端 + SQLite 数据库，三栏布局（左：小说列表，中：对话区，右：写作辅助面板）

**Tech Stack:** Vue 3, Pinia, Tailwind CSS, FastAPI, SQLAlchemy 2.0, SQLite

---

## File Structure

```
CHATWITHME/
├── frontend/                    # Vue 3 项目
│   ├── src/
│   │   ├── api/               # API 封装
│   │   ├── stores/            # Pinia 状态
│   │   ├── components/       # 组件
│   │   │   ├── LeftSidebar.vue   # 左侧：小说列表
│   │   │   ├── ChatArea.vue    # 中间：对话区
│   │   │   ├── RightPanel.vue  # 右侧：写作辅助
│   │   │   ├── PromptButton.vue # 快捷按钮
│   │   │   └── Message.vue     # 消息气泡
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── backend/                    # Python FastAPI
│   ├── app/
│   │   ├── routers/
│   │   │   ├── chat.py        # 对话接口
│   │   │   ├── novels.py      # 小说CRUD
│   │   │   ├── prompts.py    # 快捷按钮CRUD
│   │   │   └── config.py    # 模型配置
│   │   ├── models/
│   │   │   ├── database.py  # 数据库连接
│   │   │   └── schemas.py    # Pydantic 模型
│   │   ├── adapters/        # AI 适配器
│   │   │   ├── base.py
│   │   │   ├── openai.py
│   │   │   └── anthropic.py
│   │   └── main.py
│   ├── data/
│   │   └── chatwithme.db    # SQLite 数据库
│   └── requirements.txt
│
└── docs/
    └── superpowers/
        └── plans/
            └── 2026-05-07-chatwithme-plan.md
```

---

## Task 1: 后端基础架构

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/main.py`
- Create: `backend/app/models/database.py`
- Create: `backend/app/models/schemas.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
pydantic==2.5.3
httpx==0.26.0
python-dotenv==1.0.0
sse-starlette==1.8.2
```

- [ ] **Step 2: 创建 database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./data/chatwithme.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: 创建 schemas.py**

```python
from pydantic import BaseModel
from typing import Optional

# Novel
class NovelBase(BaseModel):
    title: str

class NovelCreate(NovelBase):
    pass

class Novel(NovelBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True

# Message
class MessageCreate(BaseModel):
    role: str
    content: str
    novel_id: int

class Message(MessageCreate):
    id: int

    class Config:
        from_attributes = True

# Prompt Button
class PromptButtonBase(BaseModel):
    name: str
    type: str  # send, insert, system
    content: str
    category: str

class PromptButtonCreate(PromptButtonBase):
    pass

class PromptButton(PromptButtonBase):
    id: int

    class Config:
        from_attributes = True

# Chat Request
class ChatRequest(BaseModel):
    novel_id: int
    messages: list
    prompt_buttons: Optional[list] = None
```

- [ ] **Step 4: 创建 main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, novels, prompts

app = FastAPI(title="ChatWithMe API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api")
app.include_router(novels.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 创建 routers/__init__.py**

```python
# Empty file to make routers a package
```

- [ ] **Step 6: Commit**

```bash
cd "c:/Users/wzg823/Desktop/工作/CHATWITHME/.worktrees/chatwithme-v1"
git add backend/requirements.txt backend/app/
git commit -m "feat: add backend basic structure"
```

---

## Task 2: 数据库模型与小说 CRUD

**Files:**
- Create: `backend/app/models/models.py`
- Modify: `backend/app/routers/novels.py`

- [ ] **Step 1: 创建 models.py**

```python
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.database import Base

class Novel(Base):
    __tablename__ = "novels"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("Message", back_populates="novel")
    world_settings = relationship("WorldSetting", back_populates="novel")
    outlines = relationship("Outline", back_populates="novel")
    chapters = relationship("Chapter", back_populates="novel")
    plot_threads = relationship("PlotThread", back_populates="novel")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)  # user, assistant
    content = Column(Text)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="messages")

class WorldSetting(Base):
    __tablename__ = "world_settings"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="world_settings")

class Outline(Base):
    __tablename__ = "outlines"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    level = Column(String)  # total, volume, chapter
    title = Column(String)
    content = Column(Text)
    order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="outlines")

class Chapter(Base):
    __tablename__ = "chapters"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    number = Column(Integer)
    title = Column(String)
    outline = Column(Text)  # 细纲
    content = Column(Text)  # 正文
    status = Column(String, default="draft")  # draft, writing, completed, reviewed
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="chapters")

class PlotThread(Base):
    __tablename__ = "plot_threads"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    content = Column(Text)
    introduced_chapter = Column(Integer)
    status = Column(String, default="active")  # active, resolved
    resolve_chapter = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    novel = relationship("Novel", back_populates="plot_threads")

class PromptCategory(Base):
    __tablename__ = "prompt_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    icon = Column(String, default="📝")
    sort_order = Column(Integer, default=0)

    buttons = relationship("PromptButton", back_populates="category")

class PromptButton(Base):
    __tablename__ = "prompt_buttons"
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("prompt_categories.id"))
    name = Column(String)
    button_type = Column(String)  # send, insert, system
    content = Column(Text)
    enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    category = relationship("PromptCategory", back_populates="buttons")

class ModelConfig(Base):
    __tablename__ = "model_configs"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, default="openai")
    base_url = Column(String, nullable=True)
    model = Column(String, default="gpt-4")
    api_key = Column(String, nullable=True)
    temperature = Column(Integer, default=0.7)
    max_tokens = Column(Integer, default=4096)
```

- [ ] **Step 2: 创建 novels.py router**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import list
from app.models.database import get_db, Novel
from app.models.schemas import Novel as NovelSchema, NovelCreate

router = APIRouter()

@router.get("/novels", response_model=list[NovelSchema])
def get_novels(db: Session = Depends(get_db)):
    return db.query(Novel).all()

@router.post("/novels", response_model=NovelSchema)
def create_novel(novel: NovelCreate, db: Session = Depends(get_db)):
    db_novel = Novel(title=novel.title)
    db.add(db_novel)
    db.commit()
    db.refresh(db_novel)
    return db_novel

@router.get("/novels/{novel_id}", response_model=NovelSchema)
def get_novel(novel_id: int, db: Session = Depends(get_db)):
    return db.query(Novel).filter(Novel.id == novel_id).first()

@router.delete("/novels/{novel_id}")
def delete_novel(novel_id: int, db: Session = Depends(get_db)):
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    db.delete(novel)
    db.commit()
    return {"deleted": True}
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/models.py backend/app/routers/novels.py
git commit -m "feat: add database models and novel CRUD"
```

---

## Task 3: 对话 API（流式）

**Files:**
- Modify: `backend/app/routers/chat.py`
- Create: `backend/app/adapters/base.py`
- Create: `backend/app/adapters/openai.py`

- [ ] **Step 1: 创建 adapters/base.py**

```python
from abc import ABC, abstractmethod

class ModelAdapter(ABC):
    @abstractmethod
    def send_message(self, messages: list, config: dict) -> str:
        pass

    @abstractmethod
    def stream_message(self, messages: list, config: dict):
        pass
```

- [ ] **Step 2: 创建 adapters/openai.py**

```python
import httpx
from app.adapters.base import ModelAdapter

class OpenAIAdapter(ModelAdapter):
    def __init__(self, api_key: str, base_url: str = None, model: str = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        self.model = model

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
        with httpx.Client() as client:
            with client.stream("POST", url, json=data, headers=headers) as response:
                for chunk in response.iter_text():
                    if chunk.startswith("data: "):
                        yield chunk[6:]
```

- [ ] **Step 3: 创建 chat.py router**

```python
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.models.database import get_db, Message, Novel
from app.models.schemas import ChatRequest

router = APIRouter()

def get_adapter(provider: str):
    if provider == "openai":
        from app.adapters.openai import OpenAIAdapter
        return OpenAIAdapter(api_key="dummy")
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
    
    adapter = get_adapter("openai")
    
    def generate():
        for chunk in adapter.stream_message(messages, {}):
            yield chunk
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/novels/{novel_id}/messages")
def get_messages(novel_id: int, db: Session = Depends(get_db)):
    return db.query(Message).filter(Message.novel_id == novel_id).all()
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/chat.py backend/app/adapters/
git commit -m "feat: add streaming chat API"
```

---

## Task 4: 前端项目初始化

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "chatwithme-frontend",
  "private": true,
  "version": "0.0.1",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.15",
    "pinia": "^2.1.7",
    "axios": "^1.6.5",
    "markdown-it": "^14.0.0",
    "highlight.js": "^11.9.0",
    "lucide-vue-next": "^0.312.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.3",
    "typescript": "^5.3.3",
    "vite": "^5.0.11",
    "vue-tsc": "^1.8.27",
    "tailwindcss": "^3.4.1",
    "postcss": "^8.4.33",
    "autoprefixer": "^10.4.17",
    "@types/markdown-it": "^13.0.7"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建 tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Step 4: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ChatWithMe - 小说创作工作流</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 5: 创建 src/main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'

const app = createApp(App)
app.use(createPinia())
app.mount('#app')
```

- [ ] **Step 6: 创建 src/style.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #app {
  height: 100%;
  margin: 0;
}
```

- [ ] **Step 7: Commit**

```bash
git add frontend/
git commit -m "feat: initialize Vue 3 frontend project"
```

---

## Task 5: 前端主布局与状态

**Files:**
- Create: `frontend/src/stores/chat.ts`
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 创建 stores/chat.ts**

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}

export interface Novel {
  id: number
  title: string
  created_at: string
}

export const useChatStore = defineStore('chat', () => {
  const novels = ref<Novel[]>([])
  const currentNovel = ref<Novel | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  
  const fetchedNovels = async () => {
    const res = await axios.get('/api/novels')
    novels.value = res.data
  }
  
  const createNovel = async (title: string) => {
    const res = await axios.post('/api/novels', { title })
    novels.value.push(res.data)
    return res.data
  }
  
  const selectNovel = async (novel: Novel) => {
    currentNovel.value = novel
    const res = await axios.get(`/api/novels/${novel.id}/messages`)
    messages.value = res.data
  }
  
  const sendMessage = async (content: string, promptButtons: string[] = []) => {
    if (!currentNovel.value) return
    
    loading.value = true
    messages.value.push({ id: 0, role: 'user', content })
    
    try {
      const res = await axios.post('/api/chat', {
        novel_id: currentNovel.value.id,
        messages: [{ role: 'user', content }],
        prompt_buttons: promptButtons
      }, {
        responseType: 'stream'
      })
      
      const reader = res.data.getReader()
      const decoder = new TextDecoder()
      let assistantContent = ''
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value)
        assistantContent += chunk
        // Update UI with chunk
      }
      
      messages.value.push({ id: 0, role: 'assistant', content: assistantContent })
    } finally {
      loading.value = false
    }
  }
  
  return {
    novels,
    currentNovel,
    messages,
    loading,
    fetchedNovels,
    createNovel,
    selectNovel,
    sendMessage
  }
})
```

- [ ] **Step 2: 创建 App.vue（三栏布局）**

```vue
<template>
  <div class="h-screen flex">
    <!-- Left: 小说列表 -->
    <div class="w-56 border-r border-gray-200 bg-gray-50 p-4">
      <h2 class="font-bold text-lg mb-4">📚 我的小说</h2>
      <div
        v-for="novel in store.novels"
        :key="novel.id"
        class="p-2 rounded cursor-pointer hover:bg-gray-100"
        :class="{ 'bg-blue-100': store.currentNovel?.id === novel.id }"
        @click="store.selectNovel(novel)"
      >
        {{ novel.title }}
      </div>
      <button
        @click="createNewNovel"
        class="mt-4 w-full py-2 border-2 border-dashed border-gray-300 rounded text-gray-500 hover:border-blue-400 hover:text-blue-500"
      >
        + 新建
      </button>
    </div>
    
    <!-- Middle: 对话区 -->
    <div class="flex-1 flex flex-col">
      <!-- 顶部栏 -->
      <div class="h-14 border-b border-gray-200 flex items-center px-4 justify-between">
        <span class="font-medium">{{ store.currentNovel?.title || '选择小说开始创作' }}</span>
        <select v-model="selectedModel" class="border rounded px-2 py-1">
          <option value="gpt-4">GPT-4</option>
          <option value="claude-3">Claude 3</option>
        </select>
      </div>
      
      <!-- 消息流 -->
      <div class="flex-1 overflow-y-auto p-4">
        <div
          v-for="msg in store.messages"
          :key="msg.id"
          class="mb-4"
          :class="msg.role === 'user' ? 'text-right' : 'text-left'"
        >
          <div
            class="inline-block p-3 rounded-lg max-w-[80%]"
            :class="msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200'"
          >
            {{ msg.content }}
          </div>
        </div>
      </div>
      
      <!-- 输入区 -->
      <div class="border-t border-gray-200 p-4">
        <input
          v-model="inputMessage"
          @keydown.enter="sendMessage"
          placeholder="输入消息..."
          class="w-full border rounded-lg p-3"
          :disabled="store.loading"
        />
        <div class="mt-2 flex gap-2">
          <button
            v-for="btn in promptButtons"
            :key="btn.name"
            @click="sendWithPrompt(btn)"
            class="px-3 py-1 border rounded hover:bg-gray-100"
          >
            {{ btn.name }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Right: 写作辅助面板 -->
    <div class="w-72 border-l border-gray-200 bg-gray-50 p-4">
      <div class="flex gap-2 mb-4">
        <button
          v-for="tab in ['世界观', '角色', '大纲', '伏笔', 'AI配置']"
          :key="tab"
          @click="activeTab = tab"
          class="px-2 py-1 text-sm"
          :class="activeTab === tab ? 'border-b-2 border-blue-500' : ''"
        >
          {{ tab }}
        </button>
      </div>
      <div class="text-gray-500 text-sm">
        {{ activeTab }} 内容展示区
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChatStore } from './stores/chat'

const store = useChatStore()
const inputMessage = ref('')
const selectedModel = ref('gpt-4')
const activeTab = ref('世界观')
const promptButtons = ref([
  { name: '总结', content: '请总结以上内容要点：' },
  { name: '润色', content: '请润色以下内容：' },
  { name: '续写', content: '请续写：' },
  { name: '扩写', content: '请扩写：' }
])

onMounted(() => {
  store.fetchedNovels()
})

const createNewNovel = async () => {
  const title = prompt('请输入小说标题:')
  if (title) {
    await store.createNovel(title)
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  await store.sendMessage(inputMessage.value)
  inputMessage.value = ''
}

const sendWithPrompt = async (btn: any) => {
  await store.sendMessage(btn.content)
}
</script>
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/stores/frontend/src/App.vue
git commit -m "feat: add main layout and chat store"
```

---

## Task 6: 整合测试

**Files:**
- Run: `backend/uvicorn` and `frontend/vite`
- Test: flow

- [ ] **Step 1: 启动后端**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: 启动前端**

```bash
cd frontend
npm install
npm run dev
```

- [ ] **Step 3: 测试创建小说流程**

- [ ] **Step 4: Commit**

```bash
git commit -m "chore: add project integration"
```

---

## 执行方式

**Plan complete. Two execution options:**

**1. Subagent-Driven (recommended)** - 每个 Task 分配独立子代理，分阶段审查

**2. Inline Execution** - 本会话批量执行

Which approach?
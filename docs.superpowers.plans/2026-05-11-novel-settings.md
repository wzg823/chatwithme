# 创作设定集管理 - 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在右侧边栏提供创作设定集的维护功能，支持架构、大纲、备忘录三个分类，子分类和条目完全由用户自定义。

**Architecture:** 无预设数据，子分类由用户直接创建并关联到条目
- 后端：新增 NovelSetting model + API routes
- 前端：Pinia store 新增方法 + Vue 组件改造右侧边栏
- 数据存储：SQLite 数据库，只需 novels_settings 表

**Tech Stack:** FastAPI, SQLAlchemy, Vue 3, Pinia, TypeScript

---

## 文件结构

```
backend/
├── app/
│   ├── models/
│   │   ├── models.py          # 修改：新增 NovelSetting
│   │   ├── database.py       # 修改：import 新模型
│   │   └── schemas.py       # (可选)Pydantic schemas
│   ├── routers/
│   │   └── settings.py      # 新增：设定集 CRUD API
│   └── main.py             # 修改：注册 settings router
frontend/
├── src/
│   ├── stores/
│   │   └── chat.ts        # 修改：新增设定集 store 方法
│   └── App.vue            # 修改：改造右侧边栏 UI
```

---

## Task 1: 创建数据库模型

**Files:**
- Modify: `backend/app/models/models.py`

- [ ] **Step 1: 添加 NovelSetting 模型定义**

在 `models.py` 末尾添加：

```python
class NovelSetting(Base):
    __tablename__ = "novel_settings"
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id"))
    category = Column(String)  # '架构' | '大纲' | '备忘录'
    sub_category = Column(String)  # 子分类名称，用户自定义
    title = Column(String)      # 条目标题
    content = Column(Text)     # JSON 格式的内容
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    novel = relationship("Novel", back_populates="novel_settings")
```

- [ ] **Step 2: 更新 Novel relationship**

在 `Novel` 类中添加：
```python
novel_settings = relationship("NovelSetting", back_populates="novel", cascade="all, delete")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/models.py
git commit -m "feat: 添加 NovelSetting 模型"
```

---

## Task 2: 更新 database.py

**Files:**
- Modify: `backend/app/models/database.py`

- [ ] **Step 1: 添加 import**

在 import 行添加：
```python
from app.models.models import Novel, Message, WorldSetting, Outline, Chapter, PlotThread, PromptCategory, PromptButton, ModelConfig, NovelFlows, NovelSetting
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/models/database.py
git commit -m "feat: database 导入 NovelSetting"
```

---

## Task 3: 创建 API 路由

**Files:**
- Create: `backend/app/routers/settings.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: 创建 settings router**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import NovelSetting
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json

router = APIRouter()

class NovelSettingSchema(BaseModel):
    id: int
    novel_id: int
    category: str
    sub_category: str
    title: str
    content: Optional[dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class NovelSettingCreate(BaseModel):
    category: str
    sub_category: str
    title: str
    content: Optional[dict] = {}

class NovelSettingUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[dict] = None

@router.get("/novels/{novel_id}/settings", response_model=dict)
def get_novel_settings(novel_id: int, category: str = None, db: Session = Depends(get_db)):
    """获取小说的设定，按 category 和 sub_category 分组"""
    query = db.query(NovelSetting).filter(NovelSetting.novel_id == novel_id)
    if category:
        query = query.filter(NovelSetting.category == category)
    
    settings = query.all()
    
    # 按 category -> sub_category 分组
    result = {}
    for s in settings:
        cat = s.category
        sub = s.sub_category
        if cat not in result:
            result[cat] = {}
        if sub not in result[cat]:
            result[cat][sub] = []
        result[cat][sub].append({
            "id": s.id,
            "novel_id": s.novel_id,
            "category": s.category,
            "sub_category": s.sub_category,
            "title": s.title,
            "content": json.loads(s.content) if s.content else {},
            "created_at": s.created_at,
            "updated_at": s.updated_at
        })
    
    return result

@router.post("/novels/{novel_id}/settings", response_model=NovelSettingSchema)
def create_novel_setting(novel_id: int, setting: NovelSettingCreate, db: Session = Depends(get_db)):
    """创建新设定"""
    content_json = json.dumps(setting.content) if setting.content else "{}"
    db_setting = NovelSetting(
        novel_id=novel_id,
        category=setting.category,
        sub_category=setting.sub_category,
        title=setting.title,
        content=content_json
    )
    db.add(db_setting)
    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.put("/novels/{novel_id}/settings/{setting_id}", response_model=NovelSettingSchema)
def update_novel_setting(novel_id: int, setting_id: int, setting: NovelSettingUpdate, db: Session = Depends(get_db)):
    """更新设定"""
    db_setting = db.query(NovelSetting).filter(NovelSetting.id == setting_id, NovelSetting.novel_id == novel_id).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    if setting.title is not None:
        db_setting.title = setting.title
    if setting.content is not None:
        db_setting.content = json.dumps(setting.content)
    
    db.commit()
    db.refresh(db_setting)
    return db_setting

@router.delete("/novels/{novel_id}/settings/{setting_id}")
def delete_novel_setting(novel_id: int, setting_id: int, db: Session = Depends(get_db)):
    """删除设定"""
    db_setting = db.query(NovelSetting).filter(NovelSetting.id == setting_id, NovelSetting.novel_id == novel_id).first()
    if not db_setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    db.delete(db_setting)
    db.commit()
    return {"deleted": True}
```

- [ ] **Step 2: 注册 router**

在 `main.py` 中添加：

```python
from app.routers import chat, novels, model_configs, settings

app.include_router(settings.router, prefix="/api")
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/routers/settings.py backend/app/main.py
git commit -m "feat: 添加设定集 CRUD API"
```

---

## Task 4: 前端 Store

**Files:**
- Modify: `frontend/src/stores/chat.ts`

- [ ] **Step 1: 添加接口定义**

```typescript
export interface NovelSetting {
  id: number
  novel_id: number
  category: string
  sub_category: string
  title: string
  content: any
  created_at?: string
  updated_at?: string
}
```

- [ ] **Step 2: 添加 store 状态和方法**

```typescript
const novelSettings = ref<Record<string, Record<string, NovelSetting[]>>>({})

const fetchNovelSettings = async (novelId: number, category?: string) => {
  const url = category 
    ? `/api/novels/${novelId}/settings?category=${category}`
    : `/api/novels/${novelId}/settings`
  const res = await axios.get(url)
  novelSettings.value = res.data
}

const createNovelSetting = async (novelId: number, setting: { category: string; sub_category: string; title: string; content: any }) => {
  const res = await axios.post(`/api/novels/${novelId}/settings`, setting)
  await fetchNovelSettings(novelId, setting.category)
  return res.data
}

const updateNovelSetting = async (novelId: number, settingId: number, updates: { title?: string; content?: any }, category?: string) => {
  const res = await axios.put(`/api/novels/${novelId}/settings/${settingId}`, updates)
  if (category) {
    await fetchNovelSettings(novelId, category)
  }
  return res.data
}

const deleteNovelSetting = async (novelId: number, settingId: number, category: string) => {
  await axios.delete(`/api/novels/${novelId}/settings/${settingId}`)
  await fetchNovelSettings(novelId, category)
}
```

- [ ] **Step 3: 更新 return**

```typescript
return {
  // ... 现有字段
  novelSettings,
  fetchNovelSettings,
  createNovelSetting,
  updateNovelSetting,
  deleteNovelSetting
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/stores/chat.ts
git commit -m "feat: 添加设定集 store 方法"
```

---

## Task 5: 前端 UI

**Files:**
- Modify: `frontend/src/App.vue`

- [ ] **Step 1: 改造右侧边栏模板**

替换现有的右侧边栏（大约第 122-138 行）：

```vue
<!-- Right: 写作辅助面板 -->
<div class="w-[500px] border-l border-gray-200 bg-gray-50 p-4 overflow-y-auto">
  <!-- Tab -->
  <div class="flex gap-2 mb-4 border-b">
    <button
      v-for="tab in ['架构', '大纲', '备忘录']"
      :key="tab"
      @click="switchSettingTab(tab)"
      class="px-3 py-2 text-sm"
      :class="settingTab === tab ? 'border-b-2 border-blue-500 font-medium' : 'text-gray-500'"
    >
      {{ tab }}
    </button>
  </div>

  <!-- 子分类按钮 -->
  <div class="mb-3 flex gap-2 flex-wrap">
    <button
      v-for="sub in currentSubCategories"
      :key="sub"
      @click="settingSubCategory = sub"
      class="px-2 py-1 text-xs border rounded"
      :class="settingSubCategory === sub ? 'bg-blue-100 border-blue-500' : 'bg-white'"
    >
      {{ sub }}
    </button>
    <button
      @click="addNewSubCategory"
      class="px-2 py-1 text-xs border border-dashed rounded hover:border-blue-400"
    >
      + 新增分类
    </button>
  </div>

  <!-- 设定列表 -->
  <div class="space-y-2">
    <div
      v-for="setting in currentSettings"
      :key="setting.id"
      class="p-2 bg-white border rounded"
    >
      <div class="flex justify-between items-center">
        <span 
          class="font-medium text-sm cursor-pointer"
          :class="editingSettingId === setting.id ? 'text-blue-600' : ''"
          @click="toggleEditSetting(setting)"
        >
          {{ setting.title }}
        </span>
        <button @click="confirmDeleteSetting(setting.id)" class="text-gray-400 hover:text-red-500 text-xs">×</button>
      </div>
      <!-- 编辑区 -->
      <div v-if="editingSettingId === setting.id" class="mt-2 space-y-2">
        <input
          v-model="editingTitle"
          class="w-full border rounded px-2 py-1 text-sm"
          placeholder="标题"
        />
        <textarea
          v-model="editingContent"
          class="w-full border rounded px-2 py-1 text-sm font-mono"
          rows="6"
          placeholder="JSON 内容"
        ></textarea>
        <div class="flex gap-2">
          <button @click="saveSetting" class="px-2 py-1 text-xs bg-blue-500 text-white rounded">保存</button>
          <button @click="editingSettingId = null" class="px-2 py-1 text-xs border rounded">取消</button>
        </div>
      </div>
    </div>

    <!-- 新增按钮 -->
    <button
      v-if="settingSubCategory"
      @click="showAddSetting = true"
      class="w-full py-2 border-2 border-dashed border-gray-300 rounded text-gray-500 hover:border-blue-400 text-sm"
    >
      + 新增设定
    </button>
  </div>

  <!-- 新增弹窗 -->
  <div v-if="showAddSetting" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-4 w-80">
      <div class="font-bold mb-3">新增设定</div>
      <input v-model="newSettingTitle" class="w-full border rounded px-2 py-1 mb-2" placeholder="标题" />
      <textarea v-model="newSettingContent" class="w-full border rounded px-2 py-1 mb-3 font-mono" rows="4" placeholder="JSON 内容" />
      <div class="flex justify-end gap-2">
        <button @click="showAddSetting = false" class="px-3 py-1 border rounded">取消</button>
        <button @click="createSetting" class="px-3 py-1 bg-blue-500 text-white rounded">确定</button>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 2: 添加相关状态和方法**

```typescript
const settingTab = ref('架构')
const settingSubCategory = ref('')
const editingSettingId = ref<number | null>(null)
const editingTitle = ref('')
const editingContent = ref('')
const showAddSetting = ref(false)
const newSettingTitle = ref('')
const newSettingContent = ref('{}')

const currentSubCategories = computed(() => {
  const cat = store.novelSettings[settingTab.value]
  return cat ? Object.keys(cat) : []
})

const currentSettings = computed(() => {
  const cat = store.novelSettings[settingTab.value]
  if (!cat || !settingSubCategory.value) return []
  return cat[settingSubCategory.value] || []
})

const switchSettingTab = async (tab: string) => {
  settingTab.value = tab
  settingSubCategory.value = ''
  editingSettingId.value = null
  if (store.currentNovel) {
    await store.fetchNovelSettings(store.currentNovel.id, tab)
  }
}

const addNewSubCategory = () => {
  const name = prompt('请输入新分类名称:')
  if (name && name.trim()) {
    settingSubCategory.value = name.trim()
  }
}

const toggleEditSetting = (setting: NovelSetting) => {
  if (editingSettingId.value === setting.id) {
    editingSettingId.value = null
  } else {
    editingSettingId.value = setting.id
    editingTitle.value = setting.title
    editingContent.value = JSON.stringify(setting.content || {}, null, 2)
  }
}

const saveSetting = async () => {
  if (!store.currentNovel || !editingSettingId.value) return
  try {
    const content = JSON.parse(editingContent.value || '{}')
    await store.updateNovelSetting(store.currentNovel.id, editingSettingId.value, {
      title: editingTitle.value,
      content
    }, settingTab.value)
    editingSettingId.value = null
  } catch (e) {
    alert('JSON 格式错误')
  }
}

const confirmDeleteSetting = async (id: number) => {
  if (!store.currentNovel) return
  if (confirm('确定删除此设定吗？')) {
    await store.deleteNovelSetting(store.currentNovel.id, id, settingTab.value)
  }
}

const createSetting = async () => {
  if (!store.currentNovel || !settingSubCategory.value || !newSettingTitle.value) return
  try {
    const content = JSON.parse(newSettingContent.value || '{}')
    await store.createNovelSetting(store.currentNovel.id, {
      category: settingTab.value,
      sub_category: settingSubCategory.value,
      title: newSettingTitle.value,
      content
    })
    showAddSetting.value = false
    newSettingTitle.value = ''
    newSettingContent.value = '{}'
  } catch (e) {
    alert('JSON 格式错误')
  }
}
```

- [ ] **Step 3: 切换 Tab 时加载数据**

在 `viewNovelDetail` 中添加：
```typescript
if (store.currentNovel) {
  await store.fetchNovelSettings(store.currentNovel.id, settingTab.value)
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.vue
git commit -m "feat: 改造右侧边栏为设定集管理面板"
```

---

## Task 6: 验证和测试

- [ ] **Step 1: 启动后端**

```bash
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- [ ] **Step 2: 测试 API**

```bash
# 创建设定
curl -X POST http://localhost:8000/api/novels/1/settings \
  -H "Content-Type: application/json" \
  -d '{"category":"架构","sub_category":"人设","title":"主角","content":{"name":"张三","age":25}}'

# 获取设定
curl "http://localhost:8000/api/novels/1/settings?category=架构"
```

- [ ] **Step 3: 启动前端**

```bash
cd frontend && npm run dev
```

- [ ] **Step 4: 测试 UI**

在浏览器中：
1. 选择一本小说
2. 切换右侧边栏的 Tab（架构/大纲/备忘录）
3. 点击"新增分类"创建子分类（如"人设"）
4. 在子分类下新增设定
5. 编辑设定内容
6. 删除设定
7. 刷新页面，数据应持久化

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "feat: 完成创作设定集管理功能"
```

---

## 预期结果

完成后，用户应该能够：
- 在右侧边栏看到架构、大纲、备忘录三个固定 Tab
- 用户自定义子分类（点击"新增分类"）
- 每个小说的设定独立存储
- 支持新增、编辑、删除具体设定条目
- 设定内容以 JSON 格式存储

---

## 自检清单

- [ ] Spec 覆盖：三个固定 Tab ✓
- [ ] Spec 覆盖：用户自定义子分类 ✓
- [ ] Spec 覆盖：每个小说独立配置 ✓
- [ ] Spec 覆盖：title + content 结构 ✓
- [ ] DB 模型正确 ✓
- [ ] API 端点完整 ✓
- [ ] 前端 UI 可交互 ✓
- [ ] 数据持久化 ✓
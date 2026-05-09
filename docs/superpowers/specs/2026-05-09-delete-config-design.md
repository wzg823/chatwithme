# ChatWithMe - 删除小说与系统配置功能设计

> 版本：v0.1
> 日期：2026-05-09

---

## 一、功能概览

增加两个功能：
1. 删除小说功能
2. 系统配置页面（API配置 + 提示词模板）

---

## 二、UI 设计

### 2.1 左侧边栏结构

```
┌────────────┐
│ 📚 我的小说 │
│ • 小说1  🗑️│
│ • 小说2  🗑️│
│ [+ 新建]   │
├────────────┤
│ [⚙️ 配置]   │  ← 新增按钮
└────────────┘
```

### 2.2 删除确认对话框

标题：`确定删除小说《{title}》吗？`
内容：`此操作不可撤销。`
按钮：`取消` `确定删除`

### 2.3 配置弹窗

- 弹窗形式（非页面跳转）
- 宽度：500px
- 位置：居中 overlay

#### API 配置 Tab

| 字段 | 类型 | 说明 |
|------|------|------|
| API Key | password/input | API 密钥 |
| 模型选择 | select | 下拉选择模型 |
| 设为默认 | checkbox | 是否设为默认 |

#### 提示词模板 Tab

| 字段 | 类型 | 说明 |
|------|------|------|
| 总结 | textarea | 总结提示词 |
| 润色 | textarea | 润色提示词 |
| 续写 | textarea | 续写提示词 |
| 扩写 | textarea | 扩写提示词 |

---

## 三、后端 API 设计

### 3.1 删除小说

| 项目 | 内容 |
|------|------|
| Method | DELETE |
| Path | /api/novels/{novel_id} |
| 已存在 | 是 |

### 3.2 系统配置 API

| Method | Path | 说明 |
|--------|------|------|
| GET/POST | /api/system-config | 系统配置 CRUD |

### 3.3 提示词模板 API

| Method | Path | 说明 |
|--------|------|------|
| GET/POST | /api/prompt-templates | 提示词模板 CRUD |

---

## 四、数据模型

### 4.1 SystemConfig 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| api_key | String | API 密钥 |
| default_model | String | 默认模型 |
| is_default | Boolean | 是否默认 |

### 4.2 PromptTemplate 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| name | String | 名称 |
| template | Text | 提示词内容 |

---

## 五、实现顺序

1. 后端：添加 SystemConfig 和 PromptTemplate 模型
2. 后端：添加 system_config 和 prompt_templates router
3. 前端：添加删除小说按钮 + 确认框
4. 前端：添加配置按钮 + 配置弹窗
5. 前端：store 添加相关方法
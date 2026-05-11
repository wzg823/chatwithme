# 创作设定集管理 - 设计文档

## 需求概述

在右侧边栏提供创作设定集的维护功能，用于记录小说创作参考内容。Tab 和子分类完全由用户自定义。

## 数据结构

### 表：novel_settings

各小说的实际设定内容。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| novel_id | Integer | 外键关联小说 |
| category | String | 一级分类：架构/大纲/备忘录 |
| sub_category | String | 子分类名称（如人设、势力等，用户自定义） |
| title | String | 条目标题 |
| content | JSON | 自由结构的设定内容 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

**注：一级分类（架构/大纲/备忘录）固定，用户创建子分类和条目。**

## API 设计

由于没有预设，子分类由用户直接创建：

```
GET    /api/novels/{novel_id}/settings?category=架构
       返回该小说指定category下的所有设定（按sub_category分组）

POST   /api/novels/{novel_id}/settings
       创建新设定
       Body: { category, sub_category, title, content }

PUT    /api/novels/{novel_id}/settings/{id}
       更新设定
       Body: { title, content }

DELETE /api/novels/{novel_id}/settings/{id}
       删除设定
```

## 前端 UI

### 布局

- 右侧边栏固定三个 Tab：架构、大纲、备忘录
- 每个 Tab 下，自动显示该小说已有的子分类（从数据中提取）
- 点击子分类显示该分类下的条目列表
- 支持新增子分类、新增/编辑/删除具体条目

### 交互

- 点击条目展开详情编辑器
- title 输入框 + content JSON 编辑器（textarea）
- 新增时输入 sub_category（文本输入，用户自定义）
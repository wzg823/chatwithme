# 创作设定集管理 - 设计文档

## 需求概述

在右侧边栏提供创作设定集的维护功能，用于记录小说创作参考内容。

## 数据结构

### 表：setting_templates

全局预设的二级容器类型（用于下拉选项）。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| category | String | 一级分类：架构/大纲/备忘录 |
| name | String | 二级容器名称，如人设、势力、物品等 |
| sort_order | Integer | 排序 |

### 表：novel_settings

各小说的实际设定内容。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| novel_id | Integer | 外键关联小说 |
| category | String | 一级分类：架构/大纲/备忘录 |
| sub_category | String | 二级容器名称 |
| title | String | 条目标题 |
| content | JSON | 自由结构的设定内容 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

## 预设数据

### 架构 (category)

- 人设
- 势力
- 物品
- 地图
- 门派
- 功法
- 货币
- 其他

### 大纲 (category)

- 全书大纲
- 卷纲
- 章纲
- 正文大纲

### 备忘录 (category)

- （空，用户自行添加）

## API 设计

```
GET    /api/novels/{novel_id}/settings?category=架构
       返回该小说指定category下的所有设定

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
- 每个 Tab 下，按 sub_category 分组展示
- 每组内以列表形式显示条目（显示 title）
- 支持新增、编辑、删除具体条目

### 交互

- 点击条目展开详情编辑器
- title 输入框 + content JSON 编辑器（textarea 或 JSON 编辑器组件）
- 新增时选择 sub_category（从预设下拉）
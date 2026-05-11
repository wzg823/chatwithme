# 导出功能 - 设计文档

## 需求概述

为当前小说提供导出设定集功能，用户可在弹窗中自由选择要导出的内容（Tab、子分类、具体条目），导出为JSON或Markdown格式。

## 需求确认

- **导出范围**：当前选中的小说
- **Tab选择**：自由选择任意Tab、子分类、条目
- **导出格式**：JSON 和 Markdown 两种

## UI 设计

### 弹窗布局

- 标题：`导出《小说名》设定集`
- 左侧：树状选择器（Checkbox树）
- 右侧：预览区

### 树状结构

```
├ ☑ 架构 (Tab)
│  ├ ☑ 子分类1
│  │  ├ ☑ 条目A
│  │  └ ☑ 条目B
│  └ ☑ 子分类2
│     └ ☑ 条目C
├ ☑ 大纲 (Tab)
└ ☐ 备忘录
```

### 交互规则

- 勾选Tab：该Tab下所有内容默认全选
- 勾选子分类：该分类下所有条目勾选
- 可单独勾选/取消单个条目
- 上级取消，下级自动取消；下级全勾选，上级自动勾选

### 底部按钮

- `[取消]` `[导出JSON]` `[导出Markdown]`

## 数据结构

```typescript
interface ExportTree {
  novel_id: number
  novel_title: string
  exported_at: string
  tabs: {
    category: string  // "架构" | "大纲" | "备忘录"
    enabled: boolean
    sub_categories: {
      name: string
      enabled: boolean
      settings: {
        id: number
        title: string
        content: any
      }[]
    }[]
  }[]
}
```

## 导出文件

- JSON: `{novel_title}_{时间戳}.json`
- Markdown: `{novel_title}_{时间戳}.md`

### Markdown 格式示例

```markdown
# 《小说名》设定集

## 架构

### 子分类1

#### 条目A
设定内容...

#### 条目B
设定内容...

### 子分类2

#### 条目C
设定内容...
```

## 实现方案

**前端实现** - 纯前端处理，直接在浏览器生成文件

### 前端改动

1. App.vue 添加导出按钮（位于配置按钮旁边）
2. 新增 ExportModal 组件（弹窗）
3. 前端生成文件并触发下载

### 目录结构

```
frontend/src/
  components/
    ExportModal.vue   # 新增
```

## 实现顺序

1. 添加导出按钮到 App.vue
2. 创建 ExportModal.vue 组件
3. 实现树状选择器逻辑
4. 实现 JSON 导出功能
5. 实现 Markdown 导出功能
6. 测试

## 验收标准

1. 点击导出按钮弹出模态框
2. 树状结构显示所有Tab、子分类、条目
3. 勾选联动正确
4. 可导出JSON文件，格式正确
5. 可导出Markdown文件，格式正确
6. 文件名包含小说名和时间戳
# 小说创作流程设计

## 概述

在右侧辅助面板增加「流程」标签页，支持按不同创作阶段（大纲、卷纲、正文等）进行会话，每个流程有独立的对话历史。

## 交互结构

- **左侧**：小说列表（不变）
- **中间**：对话区（不变）
- **右侧**：辅助面板新增「流程」标签页

### 流程标签页

- 显示所有已启用的创作流程
- 点击流程切换到该流程的会话
- 如果之前进入过该流程，恢复之前的对话历史
- 如果是首次进入，创建新会话

## 数据模型

### 流程配置（存储在 system_config 的 prompt_templates）

```json
{
  "writing_flows": [
    {
      "id": "uuid",
      "name": "大纲",
      "prompt": "请帮我设计小说大纲...",
      "enabled": true
    },
    {
      "id": "uuid",
      "name": "卷纲",
      "prompt": "请帮我设计这一卷的卷纲...",
      "enabled": true
    },
    {
      "id": "uuid",
      "name": "正文",
      "prompt": "请续写以下内容：",
      "enabled": true
    }
  ]
}
```

### 消息表扩展

Message 表新增 `flow_type` 字段（nullable），标识该消息属于哪个流程。

- `flow_type = null`：默认会话（兼容现有数据）
- `flow_type = 'outline'`：大纲流程
- `flow_type = 'volume'`：卷纲流程
- `flow_type = 'body'`：正文流程
- 自定义流程使用对应的 id

## 配置界面

在配置弹窗的「提示词模板」标签页中：

1. 显示现有流程列表（可排序）
2. 启用/禁用开关
3. 删除按钮
4. 新增流程按钮
5. 每个流程可编辑名称和提示词

## 发送逻辑

用户输入内容后，实际发送：

```
{流程提示词}
{用户输入内容}
```

流程提示词为空时，不添加前缀。

## API 设计

### 获取流程配置

`GET /api/config` 返回 system_config 的 prompt_templates 中包含 writing_flows

### 保存流程配置

`PUT /api/config` 整体保存 system_config（含 writing_flows）

### 获取指定流程的消息

`GET /api/novels/{novel_id}/messages?flow_type=outline`

### 创建消息时指定流程

`POST /api/novels/{novel_id}/messages` 请求体中加入 `flow_type` 字段

## 实施步骤

1. 后端：Message 表增加 flow_type 字段
2. 后端：novels router 支持 flow_type 参数
3. 前端：右侧面板增加「流程」标签页
4. 前端：配置弹窗增加流程管理界面
5. 前端：发送消息时附加流程提示词前缀
6. 前端：加载消息时按 flow_type 过滤
# 在会话页面显示当前节点

**Date:** 2026-05-10

## 需求
在会话页面顶部显示当前所在的流程节点名称，让用户清楚自己处于哪个创作阶段。

## 设计

### 位置与布局
在消息列表顶部添加一个标签条，显示当前节点名称：

```vue
<div v-if="store.currentFlow" class="flex items-center justify-between px-4 py-2 bg-gray-100 rounded-t-lg">
  <span class="text-sm text-gray-500">当前节点：</span>
  <span class="font-semibold text-blue-600">{{ currentFlowName }}</span>
  <button @click="exitNodeChat" class="text-sm text-gray-400 hover:text-gray-600">✕ 退出</button>
</div>
```

### 逻辑
- `currentFlowName` 从 `store.novelFlows` 中查找当前 `store.currentFlow` 对应的流程名称
- 新增 `exitNodeChat` 函数：返回小说详情页，清除 `currentFlow`

### 样式
- 标签条使用浅灰色背景与圆角
- 节点名称使用蓝色突出显示
- 退出按钮使用浅灰色，hover 时加深

## 实现步骤

1. 在 App.vue 添加 `currentFlowName` 计算属性
2. 在消息区域顶部添加节点标签条
3. 添加 `exitNodeChat` 函数
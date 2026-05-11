# 导出功能实现计划

> **For agentic workers:** Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为当前小说添加导出设定集功能，支持JSON和Markdown格式导出

**Architecture:** 纯前端实现，利用浏览器API生成文件并触发下载。ExportModal作为独立组件，通过props获取store中的novelSettings数据。

**Tech Stack:** Vue 3 + Composition API + TypeScript

---

### 文件结构

```
frontend/src/
  components/
    ExportModal.vue    # 新建：导出弹窗组件
  App.vue           # 修改：添加导出按钮和导入ExportModal
  stores/
    chat.ts         # 修改：添加导出数据准备方法
```

---

### Task 1: 创建 ExportModal 组件

**Files:**
- Create: `frontend/src/components/ExportModal.vue`

- [ ] **Step 1: 创建 ExportModal.vue 文件**

```vue
<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="close">
    <div class="bg-white rounded-lg w-[600px] max-h-[80vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b">
        <span class="font-bold">导出《{{ novelTitle }}》设定集</span>
        <button @click="close" class="text-gray-400 hover:text-gray-600">×</button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- Tab选择 -->
        <div class="mb-4 flex gap-2">
          <label v-for="tab in tabs" :key="tab" class="flex items-center gap-2 cursor-pointer">
            <input type="checkbox" v-model="tab.enabled" @change="onTabChange(tab)" class="w-4 h-4" />
            <span>{{ tab.category }}</span>
          </label>
        </div>

        <!-- 树状结构 -->
        <div class="space-y-2">
          <div v-for="tab in enabledTabs" :key="tab.category" class="border rounded-lg overflow-hidden">
            <!-- Tab标题 -->
            <div class="bg-gray-100 px-3 py-2 flex items-center gap-2">
              <input
                type="checkbox"
                :checked="tab.allSelected"
                :indeterminate="tab.someSelected && !tab.allSelected"
                @change="toggleTabAll(tab, $event.target.checked)"
                class="w-4 h-4"
              />
              <span class="font-medium">{{ tab.category }}</span>
            </div>

            <!-- 子分类列表 -->
            <div class="ml-4">
              <div v-for="sub in tab.subCategories" :key="sub.name" class="border-t">
                <div class="px-2 py-2 flex items-center gap-2">
                  <input
                    type="checkbox"
                    :checked="sub.allSelected"
                    :indeterminate="sub.someSelected && !sub.allSelected"
                    @change="toggleSubAll(sub, $event.target.checked)"
                    class="w-4 h-4"
                  />
                  <span class="text-sm">{{ sub.name }}</span>
                </div>

                <!-- 条目列表 -->
                <div class="ml-6 space-y-1">
                  <label v-for="item in sub.settings" :key="item.id" class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50">
                    <input type="checkbox" v-model="item.selected" class="w-4 h-4" />
                    <span class="text-sm">{{ item.title }}</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-2 p-4 border-t">
        <button @click="close" class="px-4 py-2 border rounded">取消</button>
        <button @click="exportJSON" class="px-4 py-2 bg-blue-500 text-white rounded">导出JSON</button>
        <button @click="exportMarkdown" class="px-4 py-2 bg-green-500 text-white rounded">导出Markdown</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { NovelSetting } from '../stores/chat'

interface SettingItem extends NovelSetting {
  selected: boolean
}

interface SubCategory {
  name: string
  allSelected: boolean
  someSelected: boolean
  settings: SettingItem[]
}

interface TabGroup {
  category: string
  enabled: boolean
  allSelected: boolean
  someSelected: boolean
  subCategories: SubCategory[]
}

const props = defineProps<{
  show: boolean
  novelTitle: string
  settings: Record<string, Record<string, NovelSetting[]>>
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const tabs = ref<TabGroup[]>([])

// 初始化树状数据
watch(() => props.settings, () => {
  initTree()
}, { immediate: true, deep: true })

function initTree() {
  const categories = ['架构', '大纲', '备忘录']
  tabs.value = categories.map(cat => {
    const subCats = props.settings[cat] || {}
    const subList: SubCategory[] = Object.entries(subCats).map(([name, settings]) => ({
      name,
      allSelected: false,
      someSelected: false,
      settings: settings.map(s => ({ ...s, selected: true }))
    }))

    return {
      category: cat,
      enabled: true,
      allSelected: true,
      someSelected: false,
      subCategories: subList
    }
  })
  updateSelectedStatus()
}

function updateSelectedStatus() {
  for (const tab of tabs.value) {
    let all = true, some = false
    for (const sub of tab.subCategories) {
      const items = sub.settings
      sub.allSelected = items.length > 0 && items.every(i => i.selected)
      sub.someSelected = items.some(i => i.selected)
      if (!sub.allSelected) all = false
      if (sub.someSelected) some = true
    }
    tab.allSelected = all
    tab.someSelected = some
  }
}

function onTabChange(tab: TabGroup) {
  for (const sub of tab.subCategories) {
    for (const item of sub.settings) {
      item.selected = tab.enabled
    }
  }
  updateSelectedStatus()
}

function toggleTabAll(tab: TabGroup, checked: boolean) {
  for (const sub of tab.subCategories) {
    for (const item of sub.settings) {
      item.selected = checked
    }
  }
  updateSelectedStatus()
}

function toggleSubAll(sub: SubCategory, checked: boolean) {
  for (const item of sub.settings) {
    item.selected = checked
  }
  updateSelectedStatus()
}

const enabledTabs = computed(() => tabs.value.filter(t => t.subCategories.length > 0))

function close() {
  emit('close')
}

function getSelectedData() {
  return tabs.value
    .filter(t => t.enabled)
    .map(tab => ({
      category: tab.category,
      sub_categories: tab.subCategories
        .map(sub => ({
          name: sub.name,
          settings: sub.settings.filter(i => i.selected).map(i => ({
            id: i.id,
            title: i.title,
            content: i.content
          }))
        }))
        .filter(sub => sub.settings.length > 0)
    }))
    .filter(tab => tab.sub_categories.length > 0)
}

function exportJSON() {
  const data = {
    novel_id: 0,
    novel_title: props.novelTitle,
    exported_at: new Date().toISOString(),
    tabs: getSelectedData()
  }

  const json = JSON.stringify(data, null, 2)
  downloadFile(json, `${props.novelTitle}_${timestamp()}.json`, 'application/json')
  close()
}

function exportMarkdown() {
  const data = getSelectedData()
  let md = `# 《${props.novelTitle}》设定集\n\n`

  for (const tab of data) {
    md += `## ${tab.category}\n\n`
    for (const sub of tab.sub_categories) {
      md += `### ${sub.name}\n\n`
      for (const item of sub.settings) {
        md += `#### ${item.title}\n${item.content || '(无内容)'}\n\n`
      }
    }
  }

  downloadFile(md, `${props.novelTitle}_${timestamp()}.md`, 'text/markdown')
  close()
}

function timestamp() {
  const now = new Date()
  return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}`
}

function downloadFile(content: string, filename: string, type: string) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
</script>
```

- [ ] **Step 2: 测试组件创建**

检查文件是否创建成功：`ls -la frontend/src/components/`

---

### Task 2: 在 App.vue 添加导出按钮

**Files:**
- Modify: `frontend/src/App.vue:13` - 添加导出按钮
- Modify: `frontend/src/App.vue:169` - 导入 ExportModal
- Modify: `frontend/src/App.vue:167` - template中添加 ExportModal

- [ ] **Step 1: 添加导出按钮**

在配置按钮后添加导出按钮：

```vue
<button @click="openConfig" class="mt-2 w-full py-2 border rounded flex items-center justify-center gap-2 hover:bg-gray-100">⚙️ 配置</button>
<button @click="openExport" class="mt-2 w-full py-2 border rounded flex items-center justify-center gap-2 hover:bg-gray-100">📤 导出</button>
```

- [ ] **Step 2: 添加 ExportModal 相关代码**

1. 在 imports 中添加：
```ts
import ExportModal from './components/ExportModal.vue'
```

2. 在 template 末尾添加：
```vue
<ExportModal
  :show="showExport"
  :novel-title="store.currentNovel?.title || ''"
  :settings="store.novelSettings"
  @close="showExport = false"
/>
```

3. 添加 showExport 状态：
```ts
const showExport = ref(false)
const openExport = () => {
  showExport.value = true
}
```

- [ ] **Step 3: 验证功能**

1. 启动开发服务器：`cd frontend && npm run dev`
2. 在浏览器中查看导出按钮是否显示
3. 点击导出按钮，检查弹窗是否正常显示
4. 测试导出JSON和Markdown功能

---

### Task 3: 测试完整功能

**Files:**
- Test: `frontend` 本地开发环境

- [ ] **Step 1: 验证导出流程**

1. 选择一本小说
2. 确保设定集中有内容
3. 点击导出按钮
4. 检查弹窗显示
5. 测试勾选/取消勾选联动
6. 测试JSON导出，验证文件内容
7. 测试MD导出，验证文件内容

---

### 验收标准

1. 导出按钮显示在配置按钮下方
2. 点击导出弹出 modal 框
3. 树状结构正确显示所有 Tab、子分类、条目
4. 勾选父级自动勾选所有子级
5. 取消父级自动取消所有子级
6. 导出JSON文件格式正确
7. 导出Markdown文件格式正确
8. 文件名包含小说名和日期

---

## 执行选项

**两种执行方式：**

**1. 子代理驱动 (推荐)** - 每 task 分配给独立子代理，任务间审查，快速迭代

**2. 直接执行** - 在当前会话直接执行所有任务

选择哪种方式？
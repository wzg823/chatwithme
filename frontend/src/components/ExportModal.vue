<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="emit('close')">
    <div class="bg-white rounded-lg w-[600px] max-h-[80vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b">
        <span class="font-bold">导出《{{ novelTitle }}》设定集</span>
        <button @click="emit('close')" class="text-gray-400 hover:text-gray-600 text-xl">×</button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- 树状选择结构 -->
        <div class="space-y-1">
          <div v-for="tab in tabs" :key="tab.category">
            <!-- Tab 行 -->
            <div class="flex items-center gap-2 py-2 border-b">
              <input
                type="checkbox"
                :checked="tab.allSelected"
                :indeterminate="tab.someSelected && !tab.allSelected"
                @change="toggleTabAll(tab, $event.target.checked)"
                class="w-4 h-4"
              />
              <span class="font-medium">{{ tab.category }}</span>
            </div>

            <!-- 子分类和条目 -->
            <div class="ml-4">
              <div v-for="sub in tab.subCategories" :key="sub.name" class="ml-4">
                <!-- 子分类行 -->
                <div class="flex items-center gap-2 py-1">
                  <input
                    type="checkbox"
                    :checked="sub.allSelected"
                    :indeterminate="sub.someSelected && !sub.allSelected"
                    @change="toggleSubAll(sub, $event.target.checked)"
                    class="w-4 h-4"
                  />
                  <span class="text-sm">{{ sub.name }}</span>
                </div>
                <!-- 条目 -->
                <div class="ml-8 space-y-1">
                  <label v-for="item in sub.settings" :key="item.id" class="flex items-center gap-2 py-1 hover:bg-gray-50">
                    <input type="checkbox" v-model="item.selected" class="w-4 h-4" />
                    <span class="text-sm">{{ item.title }}</span>
                  </label>
                </div>
              </div>

              <!-- 空分类提示 -->
              <div v-if="tab.subCategories.length === 0" class="ml-8 py-2 text-gray-400 text-sm">
                暂无分类
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-end gap-2 p-4 border-t">
        <button @click="emit('close')" class="px-4 py-2 border rounded">取消</button>
        <button @click="exportJSON" class="px-4 py-2 bg-blue-500 text-white rounded">导出JSON</button>
        <button @click="exportMarkdown" class="px-4 py-2 bg-green-500 text-white rounded">导出Markdown</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface SettingItem {
  id: number
  novel_id: number
  category: string
  sub_category: string
  title: string
  content: any
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

interface Props {
  show: boolean
  novelTitle: string
  settings: Record<string, Record<string, SettingItem[]>>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

// 转换原始数据为树状结构
function transformSettings(settings: Record<string, Record<string, SettingItem[]>>): TabGroup[] {
  const allTabs = ['架构', '大纲', '备忘录']
  const tabs: TabGroup[] = []

  for (const cat of allTabs) {
    const subCategories = settings[cat] || {}
    const tab: TabGroup = {
      category: cat,
      enabled: false,
      allSelected: false,
      someSelected: false,
      subCategories: []
    }

    for (const [subName, items] of Object.entries(subCategories)) {
      const sub: SubCategory = {
        name: subName,
        allSelected: false,
        someSelected: false,
        settings: items.map(item => ({ ...item, selected: false }))
      }
      tab.subCategories.push(sub)
    }

    tabs.push(tab)
  }

  return tabs
}

// 初始化tabs数据
const tabs = ref<TabGroup[]>([])

// 监听settings变化
watch(() => props.settings, (newSettings) => {
  tabs.value = transformSettings(newSettings)
}, { immediate: true, deep: true })

// 监听show变化，重置数据
watch(() => props.show, (newShow) => {
  if (newShow) {
    tabs.value = transformSettings(props.settings)
  }
})

// Tab勾选状态变化 - 现在不需要单独处理，toggleTabAll已处理

// 切换Tab全选
function toggleTabAll(tab: TabGroup, checked: boolean) {
  tab.subCategories.forEach(sub => {
    sub.settings.forEach(item => {
      item.selected = checked
    })
    updateSubSelection(sub)
  })
  updateTabSelection(tab)
}

// 切换子分类全选
function toggleSubAll(sub: SubCategory, checked: boolean) {
  sub.settings.forEach(item => {
    item.selected = checked
  })
  updateSubSelection(sub)

  // 找到所属的Tab并更新
  const parentTab = tabs.value.find(tab =>
    tab.subCategories.some(s => s.name === sub.name)
  )
  if (parentTab) {
    updateTabSelection(parentTab)
  }
}

// 更新子分类的勾选状态
function updateSubSelection(sub: SubCategory) {
  const selectedCount = sub.settings.filter(item => item.selected).length
  sub.allSelected = selectedCount === sub.settings.length && sub.settings.length > 0
  sub.someSelected = selectedCount > 0 && selectedCount < sub.settings.length
}

// 更新Tab的勾选状态
function updateTabSelection(tab: TabGroup) {
  const selectedCount = tab.subCategories.reduce(
    (count, sub) => count + sub.settings.filter(item => item.selected).length,
    0
  )
  const totalCount = tab.subCategories.reduce(
    (count, sub) => count + sub.settings.length,
    0
  )
  tab.allSelected = selectedCount === totalCount && totalCount > 0
  tab.someSelected = selectedCount > 0 && selectedCount < totalCount

  // 更新enabled状态
  tab.enabled = selectedCount > 0
}

// 获取导出的数据
function getExportData() {
  const result: {
    category: string
    sub_categories: {
      name: string
      settings: { id: number; title: string; content: any }[]
    }[]
  }[] = []

  for (const tab of tabs.value) {
    const selectedSubCategories = tab.subCategories
      .map(sub => ({
        name: sub.name,
        settings: sub.settings
          .filter(item => item.selected)
          .map(item => ({
            id: item.id,
            title: item.title,
            content: item.content
          }))
      }))
      .filter(sub => sub.settings.length > 0)

    if (selectedSubCategories.length > 0) {
      result.push({
        category: tab.category,
        sub_categories: selectedSubCategories
      })
    }
  }

  return result
}

// 格式化日期
function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${year}${month}${day}_${hour}${minute}`
}

// 生成文件名
function generateFilename(ext: string): string {
  const dateStr = formatDate(new Date())
  return `${props.novelTitle}_${dateStr}.${ext}`
}

// 导出JSON
function exportJSON() {
  const data = getExportData()

  const exportObj = {
    novel_id: 0,
    novel_title: props.novelTitle,
    exported_at: new Date().toISOString(),
    tabs: data
  }

  const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = generateFilename('json')
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

// 生成Markdown内容
function generateMarkdown(): string {
  const data = getExportData()
  let md = `# 《${props.novelTitle}》设定集\n\n`

  for (const tab of data) {
    md += `## ${tab.category}\n\n`

    for (const sub of tab.sub_categories) {
      md += `### ${sub.name}\n\n`

      for (const item of sub.settings) {
        md += `#### ${item.title}\n`
        md += `${item.content}\n\n`
      }
    }
  }

  return md
}

// 导出Markdown
function exportMarkdown() {
  const md = generateMarkdown()
  const blob = new Blob([md], { type: 'text/markdown' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = generateFilename('md')
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

</script>

<style scoped>
.fixed {
  position: fixed;
}

.inset-0 {
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
}

.bg-black\/50 {
  background-color: rgba(0, 0, 0, 0.5);
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.justify-between {
  justify-content: space-between;
}

.justify-end {
  justify-content: flex-end;
}

.gap-2 {
  gap: 0.5rem;
}

.gap-4 {
  gap: 1rem;
}

.z-50 {
  z-index: 50;
}

.bg-white {
  background-color: white;
}

.rounded-lg {
  border-radius: 0.5rem;
}

.w-\[600px\] {
  width: 600px;
}

.max-h-\[80vh\] {
  max-height: 80vh;
}

.overflow-hidden {
  overflow: hidden;
}

.overflow-y-auto {
  overflow-y: auto;
}

.flex-col {
  flex-direction: column;
}

.p-4 {
  padding: 1rem;
}

.px-2 {
  padding-left: 0.5rem;
  padding-right: 0.5rem;
}

.px-3 {
  padding-left: 0.75rem;
  padding-right: 0.75rem;
}

.px-4 {
  padding-left: 1rem;
  padding-right: 1rem;
}

.py-1 {
  padding-top: 0.25rem;
  padding-bottom: 0.25rem;
}

.py-2 {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.mb-4 {
  margin-bottom: 1rem;
}

.ml-4 {
  margin-left: 1rem;
}

.ml-6 {
  margin-left: 1.5rem;
}

.border {
  border: 1px solid #e5e7eb;
}

.border-b {
  border-bottom: 1px solid #e5e7eb;
}

.border-t {
  border-top: 1px solid #e5e7eb;
}

.bg-gray-50 {
  background-color: #f9fafb;
}

.bg-gray-100 {
  background-color: #f3f4f6;
}

.font-bold {
  font-weight: 700;
}

.font-medium {
  font-weight: 500;
}

.text-sm {
  font-size: 0.875rem;
}

.text-xl {
  font-size: 1.25rem;
}

.text-gray-400 {
  color: #9ca3af;
}

.text-gray-600 {
  color: #4b5563;
}

.text-white {
  color: white;
}

.hover\:text-gray-600:hover {
  color: #4b5563;
}

.hover\:bg-gray-50:hover {
  background-color: #f9fafb;
}

.w-4 {
  width: 1rem;
}

.h-4 {
  height: 1rem;
}

.space-y-1 > * + * {
  margin-top: 0.25rem;
}

.space-y-2 > * + * {
  margin-top: 0.5rem;
}

.cursor-pointer {
  cursor: pointer;
}

button {
  cursor: pointer;
}

.bg-blue-500 {
  background-color: #3b82f6;
}

.bg-green-500 {
  background-color: #22c55e;
}

.rounded {
  border-radius: 0.25rem;
}
</style>
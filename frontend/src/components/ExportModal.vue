<template>
  <div v-if="show" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" @click.self="emit('close')">
    <div class="bg-white dark:bg-gray-900 rounded-lg w-[600px] max-h-[80vh] overflow-hidden flex flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
        <span class="font-['Archivo'] font-semibold text-gray-900 dark:text-white">导出《{{ novelTitle }}》设定集</span>
        <button @click="emit('close')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-xl transition-colors duration-200">×</button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-4">
        <!-- 树状选择结构 -->
        <div class="space-y-1">
          <div v-for="tab in tabs" :key="tab.category">
            <!-- Tab 行 -->
            <div class="flex items-center gap-2 py-2 border-b border-gray-100 dark:border-gray-800">
              <input
                type="checkbox"
                :checked="tab.allSelected"
                :indeterminate="tab.someSelected && !tab.allSelected"
                @change="toggleTabAll(tab, $event.target.checked)"
                class="w-4 h-4 rounded border-gray-300 dark:border-gray-600"
              />
              <span class="font-medium text-gray-800 dark:text-gray-200">{{ tab.category }}</span>
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
                    class="w-4 h-4 rounded border-gray-300 dark:border-gray-600"
                  />
                  <span class="text-sm text-gray-600 dark:text-gray-400">{{ sub.name }}</span>
                </div>
                <!-- 条目 -->
                <div class="ml-8 space-y-1">
                  <label v-for="item in sub.settings" :key="item.id" class="flex items-center gap-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 rounded transition-colors duration-200 cursor-pointer">
                    <input type="checkbox" v-model="item.selected" class="w-4 h-4 rounded border-gray-300 dark:border-gray-600" />
                    <span class="text-sm text-gray-700 dark:text-gray-300">{{ item.title }}</span>
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
      <div class="flex justify-end gap-2 p-4 border-t border-gray-200 dark:border-gray-800">
        <button @click="emit('close')" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200">取消</button>
        <button @click="exportJSON" class="px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded hover:opacity-90 transition-opacity duration-200">导出JSON</button>
        <button @click="exportMarkdown" class="px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded hover:opacity-90 transition-opacity duration-200">导出Markdown</button>
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

.z-50 {
  z-index: 50;
}

.cursor-pointer {
  cursor: pointer;
}

button {
  cursor: pointer;
}
</style>
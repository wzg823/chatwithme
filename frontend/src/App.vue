<template>
  <div class="h-screen flex font-['Space_Grotesk']">
    <!-- Left: 小说列表 -->
    <div class="w-56 border-r border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 p-4 overflow-y-auto">
      <h2 class="font-['Archivo'] font-semibold text-lg mb-4 text-gray-900 dark:text-white">我的小说</h2>
      <div v-for="novel in store.novels" :key="novel.id" class="mb-1">
        <div class="p-2 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center justify-between transition-colors duration-200" :class="store.currentNovel?.id === novel.id ? 'bg-gray-200 dark:bg-gray-800' : ''" @click="viewNovelDetail(novel)">
          <span class="flex-1 truncate text-gray-700 dark:text-gray-300">{{ novel.title }}</span>
          <button @click.stop="confirmDelete(novel)" class="text-gray-400 hover:text-red-500 ml-2 transition-colors duration-200">×</button>
        </div>
      </div>
      <button @click="createNewNovel" class="mt-4 w-full py-2 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded text-gray-500 dark:text-gray-400 hover:border-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors duration-200">+ 新建</button>
      <button @click="openConfig" class="mt-2 w-full py-2 border border-gray-200 dark:border-gray-800 rounded flex items-center justify-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors duration-200"><Settings class="w-4 h-4" />配置</button>
      <button @click="openExport" class="mt-2 w-full py-2 border border-gray-200 dark:border-gray-800 rounded flex items-center justify-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors duration-200"><Download class="w-4 h-4" />导出</button>
      <button @click="toggleDark" class="mt-2 w-full py-2 border border-gray-200 dark:border-gray-800 rounded flex items-center justify-center gap-2 hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors duration-200">
        <Sun v-if="!isDark" class="w-4 h-4" />
        <Moon v-else class="w-4 h-4" />
        <span class="ml-1">{{ isDark ? '浅色模式' : '深色模式' }}</span>
      </button>
    </div>

    <!-- Middle: 对话区 -->
    <div class="flex-1 flex flex-col">
      <div class="h-14 border-b border-gray-200 dark:border-gray-800 flex items-center px-4 justify-between bg-gray-50 dark:bg-gray-900">
        <div class="flex items-center gap-2">
          <span class="font-['Archivo'] font-medium text-gray-900 dark:text-white">{{ store.currentNovel?.title || '选择小说开始创作' }}</span>
          <span v-if="currentFlowName" class="text-gray-400">/</span>
          <span v-if="currentFlowName" class="text-gray-700 dark:text-gray-300 font-medium">{{ currentFlowName }}</span>
        </div>
        <div class="flex items-center gap-2">
          <button v-if="currentFlowName" @click="openPromptEdit" class="px-2 py-1 text-sm border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors duration-200">提示词</button>
          <button v-if="currentFlowName" @click="exitNodeChat" class="px-2 py-1 text-sm border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors duration-200">退出节点</button>
        </div>
      </div>

      <div v-if="showNovelDetail" class="flex-1 p-6 overflow-y-auto">
        <div class="mb-6 flex items-center justify-between">
          <div>
            <h2 class="font-['Archivo'] text-xl font-semibold mb-1 text-gray-900 dark:text-white">《{{ store.currentNovel?.title }}》</h2>
            <p class="text-sm text-gray-500">创建于 {{ store.currentNovel?.created_at?.split('T')[0] }}</p>
          </div>
        </div>
        <div class="grid grid-cols-3 gap-4">
          <div v-for="flow in store.novelFlows.filter(f => f.enabled)" :key="flow.id" class="h-32 border-2 border-gray-200 dark:border-gray-800 rounded-lg cursor-pointer hover:border-gray-400 dark:hover:border-gray-600 hover:shadow-md transition-all duration-300 relative" @click="enterNodeChat(flow.id)">
            <div class="font-['Archivo'] text-lg font-medium text-center flex items-center justify-center h-full text-gray-800 dark:text-gray-200">{{ flow.name }}</div>
            <button @click.stop="confirmDeleteFlow(flow.id)" class="absolute top-1 right-1 w-6 h-6 flex items-center justify-center text-gray-400 hover:text-red-500 bg-white dark:bg-gray-800 rounded transition-colors duration-200" title="删除">
              <Trash2 class="w-4 h-4" />
            </button>
          </div>
          <div class="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg h-32 flex items-center justify-center cursor-pointer hover:border-gray-400 dark:hover:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-200" @click="showAddFlowModal = true">
            <span class="text-2xl text-gray-400">+</span>
          </div>
        </div>
      </div>

      <div v-else class="flex-1 overflow-y-auto p-4" ref="messageContainer">
        <div v-for="msg in store.messages" :key="msg.id" class="mb-4 flex" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <div class="inline-block p-3 rounded-lg max-w-[80%] relative group transition-all duration-200" :class="msg.role === 'user' ? 'message-user' : 'message-assistant'">
            <div class="whitespace-pre-wrap">{{ msg.content }}</div>
            <button v-if="msg.role === 'assistant'" @click="copyMessage(msg.content)" class="absolute top-1 right-1 opacity-0 group-hover:opacity-100 px-2 py-1 text-xs bg-white dark:bg-gray-700 border rounded shadow hover:bg-gray-50 dark:hover:bg-gray-600 transition-all duration-200" title="复制">
              <Copy class="w-3 h-3" />
            </button>
          </div>
        </div>
      </div>

      <div class="border-t border-gray-200 dark:border-gray-800 p-4 bg-gray-50 dark:bg-gray-900">
        <input v-model="inputMessage" @keydown.enter="sendMessage" placeholder="输入消息..." class="w-full border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" :disabled="store.loading" />
        <div class="mt-2 flex gap-2">
          <button v-for="template in store.promptTemplates" :key="template.name" @click="useTemplate(template.content)" class="px-3 py-1 text-sm border border-gray-200 dark:border-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 transition-colors duration-200">{{ template.name }}</button>
        </div>
      </div>
    </div>

    <!-- Right: 设定集 -->
    <div class="w-[500px] border-l border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 p-4 overflow-y-auto">
      <div class="flex gap-2 mb-4 border-b border-gray-200 dark:border-gray-800">
        <button v-for="tab in ['架构', '大纲', '备忘录']" :key="tab" @click="switchSettingTab(tab)" class="px-3 py-2 text-gray-600 dark:text-gray-400 transition-colors duration-200" :class="settingTab === tab ? 'border-b-2 border-gray-900 dark:border-gray-100 text-gray-900 dark:text-white font-medium' : 'hover:text-gray-900 dark:hover:text-gray-200'">{{ tab }}</button>
      </div>

      <div class="space-y-4">
        <div v-for="sub in currentSubCategories" :key="sub">
          <div class="flex items-center justify-between">
            <button @click="toggleSubCategory(sub)" class="text-sm font-medium flex-1 text-left text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors duration-200">{{ sub }}</button>
            <button @click="deleteSubCategory(sub)" class="text-xs text-gray-400 hover:text-red-500 transition-colors duration-200">删除</button>
          </div>

          <div v-if="expandedSubCategories.has(sub)" class="space-y-2 ml-2 mt-2">
            <div v-for="setting in (store.novelSettings[store.currentNovel?.id]?.[settingTab]?.[sub] || [])" :key="setting.id" class="p-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded transition-colors duration-200">
              <div v-if="!expandedSettings.has(setting.id)" class="flex justify-between items-center">
                <span class="font-medium text-sm cursor-pointer flex-1 text-gray-800 dark:text-gray-200" @click="toggleEditSetting(setting)">{{ setting.title }}</span>
                <button @click.stop="toggleEditSetting(setting)" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200"><ChevronDown class="w-4 h-4" /></button>
              </div>

              <div v-if="expandedSettings.has(setting.id)" class="space-y-2">
                <input :value="getEditingState(setting.id, 'title', setting.title)" @change="handleTitleChange(setting.id, $event)" class="w-full border border-gray-200 dark:border-gray-700 rounded px-2 py-1 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100" placeholder="标题" />
                <textarea :value="getEditingState(setting.id, 'content', setting.content)" @change="handleContentChange(setting.id, $event)" class="w-full border border-gray-200 dark:border-gray-700 rounded px-2 py-1 text-sm bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100" rows="4" placeholder="内容"></textarea>
                <div class="flex items-center gap-2">
                  <button @click="saveSetting" class="flex-1 px-2 py-1 text-xs bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded hover:opacity-90 transition-opacity duration-200">保存</button>
                  <button @click="collapseSetting(setting.id)" class="flex-1 px-2 py-1 text-xs border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200">取消</button>
                  <button @click="confirmDeleteSetting(setting.id)" class="flex-1 px-2 py-1 text-xs text-red-500 border border-red-500 rounded hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors duration-200">删除</button>
                  <button @click="collapseSetting(setting.id)" class="p-1 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 transition-colors duration-200">
                    <ChevronUp class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <button @click="selectSubCategoryAndAdd(sub)" class="w-full py-1 text-xs border border-dashed border-gray-300 dark:border-gray-600 rounded text-gray-500 dark:text-gray-400 hover:border-gray-400 dark:hover:text-gray-300 transition-colors duration-200">+ 新增设定</button>
          </div>
        </div>

        <button @click="addNewSubCategory" class="w-full py-2 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded text-gray-500 dark:text-gray-400 hover:border-gray-400 dark:hover:text-gray-300 text-sm transition-colors duration-200">+ 新增分类</button>
      </div>

      <div v-if="showAddSetting" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div class="bg-white dark:bg-gray-900 rounded-lg p-4 w-80">
          <div class="font-['Archivo'] font-semibold mb-3 text-gray-900 dark:text-white">新增设定</div>
          <input v-model="newSettingTitle" class="w-full border border-gray-200 dark:border-gray-700 rounded px-2 py-1 mb-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" placeholder="标题" />
          <textarea v-model="newSettingContent" class="w-full border border-gray-200 dark:border-gray-700 rounded px-2 py-1 mb-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" rows="4" placeholder="内容"></textarea>
          <div class="flex justify-end gap-2">
            <button @click="showAddSetting = false" class="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200">取消</button>
            <button @click="createSetting" class="px-3 py-1 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded hover:opacity-90 transition-opacity duration-200">确定</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showConfig" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-900 rounded-lg w-[500px] max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-800">
          <span class="font-['Archivo'] font-semibold flex items-center gap-2 text-gray-900 dark:text-white"><Settings class="w-4 h-4" />系统配置</span>
          <button @click="showConfig = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200">×</button>
        </div>
        <div class="flex border-b border-gray-200 dark:border-gray-800">
          <button @click="configTab = 'api'" class="px-4 py-2 text-gray-600 dark:text-gray-400 transition-colors duration-200" :class="configTab === 'api' ? 'border-b-2 border-gray-900 dark:border-gray-100 text-gray-900 dark:text-white' : 'hover:text-gray-900 dark:hover:text-gray-200'">API配置</button>
          <button @click="configTab = 'prompt'" class="px-4 py-2 text-gray-600 dark:text-gray-400 transition-colors duration-200" :class="configTab === 'prompt' ? 'border-b-2 border-gray-900 dark:border-gray-100 text-gray-900 dark:text-white' : 'hover:text-gray-900 dark:hover:text-gray-200'">提示词模板</button>
        </div>
        <div class="p-4">
          <div v-if="configTab === 'api'">
            <div class="mb-4">
              <label class="block text-sm mb-1 text-gray-700 dark:text-gray-300">Provider</label>
              <select v-model="store.systemConfig.provider" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100">
                <option value="openai">OpenAI</option>
                <option value="deepseek">DeepSeek</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div class="mb-4">
              <label class="block text-sm mb-1 text-gray-700 dark:text-gray-300">API Key</label>
              <input v-model="store.systemConfig.apiKey" type="password" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
            </div>
            <div class="mb-4">
              <label class="block text-sm mb-1 text-gray-700 dark:text-gray-300">模型</label>
              <select v-model="store.systemConfig.model" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" :disabled="store.systemConfig.provider === 'custom'">
                <option v-for="model in store.getModelsForProvider(store.systemConfig.provider)" :key="model" :value="model">{{ model.toUpperCase() }}</option>
                <option v-if="store.systemConfig.provider === 'custom'" value="">自定义模型</option>
              </select>
            </div>
            <div v-if="store.systemConfig.provider === 'custom'" class="mb-4">
              <label class="block text-sm mb-1 text-gray-700 dark:text-gray-300">Base URL</label>
              <input v-model="store.systemConfig.baseUrl" type="text" placeholder="https://api.example.com/v1" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
            </div>
            <div v-if="store.systemConfig.provider === 'custom' && !store.getModelsForProvider(store.systemConfig.provider).includes(store.systemConfig.model)" class="mb-4">
              <label class="block text-sm mb-1 text-gray-700 dark:text-gray-300">模型名称</label>
              <input v-model="store.systemConfig.model" type="text" placeholder="e.g. claude-3-opus" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" />
            </div>
          </div>
          <div v-if="configTab === 'prompt'">
            <div class="space-y-2">
              <div v-for="template in store.promptTemplates" :key="template.name" class="p-2 border border-gray-200 dark:border-gray-700 rounded">
                <div class="font-medium text-gray-800 dark:text-gray-200">{{ template.name }}</div>
                <div class="text-sm text-gray-500">{{ template.description }}</div>
              </div>
              <div v-if="store.promptTemplates.length === 0" class="text-gray-400 text-center py-4">暂无可用模板</div>
            </div>
          </div>
        </div>
        <div class="flex justify-end gap-2 p-4 border-t border-gray-200 dark:border-gray-800">
          <button @click="showConfig = false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200">取消</button>
          <button @click="saveConfig" class="px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded hover:opacity-90 transition-opacity duration-200">保存</button>
        </div>
      </div>
    </div>

    <ExportModal
      :show="showExport"
      :novel-title="store.currentNovel?.title || ''"
      :settings="store.novelSettings[store.currentNovel?.id] || {}"
      @close="showExport = false"
    />

    <div v-if="showAddNovel" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-900 rounded-lg p-6 w-80">
        <div class="font-['Archivo'] font-semibold mb-4 text-gray-900 dark:text-white">新建小说</div>
        <input v-model="newNovelTitle" @keydown.enter="createNovel" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 mb-4 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" placeholder="小说标题" />
        <div class="flex justify-end gap-2">
          <button @click="showAddNovel = false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200">取消</button>
          <button @click="createNovel" class="px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded hover:opacity-90 transition-opacity duration-200">创建</button>
        </div>
      </div>
    </div>

    <div v-if="showAddFlowModal && store.currentNovel" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-900 rounded-lg p-6 w-96">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-['Archivo'] font-semibold text-lg text-gray-900 dark:text-white">添加创作流程</h3>
          <button @click="showAddFlowModal = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200">×</button>
        </div>
        <div>
          <input v-model="newFlowName" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 mb-2 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" placeholder="流程名称" />
          <textarea v-model="newFlowPrompt" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 mb-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" placeholder="提示词前缀" rows="3"></textarea>
          <button @click="addCustomFlow" :disabled="!newFlowName.trim()" class="w-full py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded hover:opacity-90 transition-opacity duration-200" :class="!newFlowName.trim() ? 'opacity-50 cursor-not-allowed' : ''">添加</button>
        </div>
      </div>
    </div>

    <div v-if="showPromptEdit" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-gray-900 rounded-lg p-6 w-[500px]">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-['Archivo'] font-semibold text-lg text-gray-900 dark:text-white">编辑提示词</h3>
          <button @click="showPromptEdit = false" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors duration-200">×</button>
        </div>
        <div>
          <label class="block text-sm mb-1 text-gray-700 dark:text-gray-300">提示词前缀</label>
          <textarea v-model="currentFlowPrompt" class="w-full border border-gray-200 dark:border-gray-700 rounded p-2 mb-3 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100" rows="6" placeholder="输入此流程的提示词前缀..."></textarea>
          <div class="flex justify-end gap-2">
            <button @click="showPromptEdit = false" class="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors duration-200">取消</button>
            <button @click="savePrompt" class="px-4 py-2 bg-gray-900 dark:bg-gray-100 text-white dark:text-gray-900 rounded hover:opacity-90 transition-opacity duration-200">保存</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template><script setup lang="ts">
import { ref, onMounted, nextTick, watch, computed } from 'vue'
import { Copy, Trash2, ChevronDown, ChevronUp, Settings, Download, Sun, Moon } from 'lucide-vue-next'
import ExportModal from './components/ExportModal.vue'
import { useChatStore } from './stores/chat'
import type { Novel, NovelSetting } from './stores/chat'

const store = useChatStore()
const inputMessage = ref('')
const selectedModel = ref('gpt-4')
const activeTab = ref('世界观')
const messageContainer = ref<HTMLElement | null>(null)
const isDark = ref(false)

const toggleDark = () => {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

// 监听 messages 变化，自动滚动到底部
watch(() => store.messages.length, scrollToBottom)
const promptButtons = ref([
  { name: '总结', content: '请总结以上内容要点：' },
  { name: '润色', content: '请润色以下内容：' },
  { name: '续写', content: '请续写：' },
  { name: '扩写', content: '请扩写：' }
])

onMounted(async () => {
  // 读取保存的主题设置
  const savedTheme = localStorage.getItem('theme')
  if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    isDark.value = true
    document.documentElement.classList.add('dark')
  }
  await store.fetchedNovels()
  await store.fetchSystemConfig()
  await store.fetchWritingFlows()
  selectedModel.value = store.systemConfig.model
  // 自动选择第一个小说，进入详情页
  if (store.novels.length > 0) {
    await store.selectNovel(store.novels[0])
    await store.fetchNovelFlows(store.novels[0].id)
    await store.fetchNovelSettings(store.novels[0].id, settingTab.value)
    showNovelDetail.value = true
  }
})

const createNewNovel = async () => {
  const title = prompt('请输入小说标题:')
  if (title) {
    await store.createNovel(title)
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim()) return
  await store.sendMessage(inputMessage.value)
  inputMessage.value = ''
}

const sendWithPrompt = async (btn: any) => {
  await store.sendMessage(btn.content)
}

const confirmDelete = (novel: Novel) => {
  if (confirm(`确定删除小说《${novel.title}》吗？此操作不可撤销。`)) {
    store.deleteNovel(novel.id)
  }
}

const showNovelDetail = ref(true)  // 默认显示节点选择页面，避免闪屏
const hoveringFlow = ref<string | number | null>(null)
const showAddFlowModal = ref(false)
const newFlowName = ref('')
const newFlowPrompt = ref('')
const showPromptEdit = ref(false)
const currentFlowPrompt = ref('')

const currentFlowName = computed(() => {
  if (!store.currentFlow) return ''
  const flow = store.novelFlows.find(f => f.id === Number(store.currentFlow) || f.id === store.currentFlow)
  return flow?.name || ''
})

const currentFlowPromptText = computed(() => {
  if (!store.currentFlow) return ''
  const flow = store.novelFlows.find(f => f.id === Number(store.currentFlow) || f.id === store.currentFlow)
  return flow?.prompt || ''
})

const openPromptEdit = () => {
  currentFlowPrompt.value = currentFlowPromptText.value
  showPromptEdit.value = true
}

const savePrompt = async () => {
  if (store.currentNovel && store.currentFlow) {
    await store.updateNovelFlow(store.currentNovel.id, Number(store.currentFlow), { prompt: currentFlowPrompt.value })
    showPromptEdit.value = false
  }
}

const viewNovelDetail = async (novel?: Novel) => {
  if (novel) {
    store.currentNovel = novel
  }
  if (store.currentNovel) {
    showNovelDetail.value = true
    await store.fetchNovelFlows(store.currentNovel.id)
    await store.fetchNovelSettings(store.currentNovel.id, settingTab.value)
  }
}

const confirmDeleteFlow = async (flowId: number) => {
  if (store.currentNovel && confirm('确定删除此创作流程吗？')) {
    await store.removeNovelFlow(store.currentNovel.id, flowId)
  }
}

const enterNodeChat = async (flowId: string | number) => {
  const flow = store.novelFlows.find(f => f.id === flowId)
  if (flow) {
    store.currentFlow = String(flowId)
    showNovelDetail.value = false
    const res = await fetch(`/api/novels/${store.currentNovel.id}/messages?flow_type=${flowId}`)
    store.messages = await res.json()
  }
}

const exitNodeChat = async () => {
  store.currentFlow = null
  showNovelDetail.value = true
  store.messages = []
}

const addFromTemplate = async (templateId: string) => {
  if (store.currentNovel) {
    await store.addNovelFlow(store.currentNovel.id, { name: '', from_template: templateId })
    showAddFlowModal.value = false
  }
}

const addCustomFlow = async () => {
  if (store.currentNovel && newFlowName.value.trim()) {
    await store.addNovelFlow(store.currentNovel.id, { name: newFlowName.value.trim(), prompt: newFlowPrompt.value })
    newFlowName.value = ''
    newFlowPrompt.value = ''
    showAddFlowModal.value = false
  }
}

const showConfig = ref(false)
const showExport = ref(false)
const configTab = ref('api')

// 设定集管理状态
const settingTab = ref('架构')
const settingSubCategory = ref('')
const expandedSettings = ref<Set<number>>(new Set())
const editingTitle = ref('')
const editingContent = ref('')
const showAddSetting = ref(false)
const expandedSubCategories = ref<Set<string>>(new Set())
const newSettingTitle = ref('')
const newSettingContent = ref('')

// 每个展开设定的独立编辑状态
const editingStates = ref<Map<number, { title: string; content: string }>>(new Map())

const getEditingState = (id: number, field: 'title' | 'content', defaultValue: string): string => {
  const state = editingStates.value.get(id)
  if (state && state[field] !== undefined && state[field] !== '') {
    return state[field]
  }
  return defaultValue
}

const updateEditingState = (id: number, field: 'title' | 'content', value: string) => {
  const current = editingStates.value.get(id) || { title: '', content: '' }
  editingStates.value.set(id, { ...current, [field]: value })
}

const handleTitleChange = (id: number, event: Event) => {
  const value = (event.target as HTMLInputElement).value
  updateEditingState(id, 'title', value)
}

const handleContentChange = (id: number, event: Event) => {
  const value = (event.target as HTMLTextAreaElement).value
  updateEditingState(id, 'content', value)
}

const collapseSetting = (id: number) => {
  expandedSettings.value.delete(id)
  editingStates.value.delete(id)
}

const toggleSubCategory = (sub: string) => {
  if (expandedSubCategories.value.has(sub)) {
    expandedSubCategories.value.delete(sub)
  } else {
    expandedSubCategories.value.add(sub)
  }
}

const currentSubCategories = computed(() => {
  const cat = store.novelSettings[store.currentNovel?.id]?.[settingTab.value]
  return cat ? Object.keys(cat) : []
})

const currentSettings = computed(() => {
  const cat = store.novelSettings[store.currentNovel?.id]?.[settingTab.value]
  if (!cat || !settingSubCategory.value) return []
  return cat[settingSubCategory.value] || []
})

const switchSettingTab = async (tab: string) => {
  settingTab.value = tab
  settingSubCategory.value = ''
  expandedSettings.value.clear()
  expandedSubCategories.value.clear()
  if (store.currentNovel) {
    await store.fetchNovelSettings(store.currentNovel.id, tab)
  }
}

const addNewSubCategory = async () => {
  const name = prompt('请输入新分类名称:')
  if (name && name.trim() && store.currentNovel) {
    // 自动创建一个空设定来创建分类
    await store.createNovelSetting(store.currentNovel.id, {
      category: settingTab.value,
      sub_category: name.trim(),
      title: '新设定',
      content: ''
    })
    settingSubCategory.value = name.trim()
    // 刷新数据
    await store.fetchNovelSettings(store.currentNovel.id, settingTab.value)
  }
}

const toggleEditSetting = (setting: NovelSetting) => {
  if (expandedSettings.value.has(setting.id)) {
    expandedSettings.value.delete(setting.id)
    editingStates.value.delete(setting.id)
  } else {
    expandedSettings.value.add(setting.id)
    // 初始化编辑状态
    editingStates.value.set(setting.id, {
      title: setting.title,
      content: typeof setting.content === 'string' ? setting.content : ''
    })
  }
}

const saveSetting = async () => {
  if (!store.currentNovel) return
  // 保存所有展开的设定
  for (const id of expandedSettings.value) {
    const state = editingStates.value.get(id)
    if (state) {
      await store.updateNovelSetting(store.currentNovel.id, id, {
        title: state.title,
        content: state.content
      }, settingTab.value)
    }
  }
  // 刷新数据
  await store.fetchNovelSettings(store.currentNovel.id, settingTab.value)
  // 清除展开状态
  expandedSettings.value.clear()
  editingStates.value.clear()
}

const confirmDeleteSetting = async (id: number) => {
  if (!store.currentNovel) return
  expandedSettings.value.delete(id)
  if (confirm('确定删除此设定吗？')) {
    await store.deleteNovelSetting(store.currentNovel.id, id, settingTab.value)
    // 刷新数据
    await store.fetchNovelSettings(store.currentNovel.id, settingTab.value)
  }
}

const createSetting = async () => {
  if (!store.currentNovel || !settingSubCategory.value || !newSettingTitle.value) return
  // content 直接作为字符串存储
  await store.createNovelSetting(store.currentNovel.id, {
    category: settingTab.value,
    sub_category: settingSubCategory.value,
    title: newSettingTitle.value,
    content: newSettingContent.value
  })
  showAddSetting.value = false
  newSettingTitle.value = ''
  newSettingContent.value = ''
  // 刷新数据
  await store.fetchNovelSettings(store.currentNovel.id, settingTab.value)
}

const selectSubCategoryAndAdd = async (sub: string) => {
  settingSubCategory.value = sub
  showAddSetting.value = true
}

const deleteSubCategory = async (subCategory: string) => {
  if (!store.currentNovel) return
  if (!confirm(`确定删除分类"${subCategory}"及其所有设定吗？`)) return
  const novelId = store.currentNovel.id

  const settings = store.novelSettings[novelId]?.[settingTab.value]?.[subCategory] || []
  for (const s of settings) {
    await store.deleteNovelSetting(novelId, s.id, settingTab.value)
  }
  // 先清空这本小说的该分类数据
  if (store.novelSettings[novelId]?.[settingTab.value]) {
    delete store.novelSettings[novelId][settingTab.value][subCategory]
  }
  // 重新获取所有分类（不带category参数，避免后端bug）
  await store.fetchNovelSettings(novelId)
}

const renameSubCategory = async (subCategory: string) => {
  if (!store.currentNovel) return
  const newName = prompt('请输入新分类名称:', subCategory)
  if (!newName || newName === subCategory) return

  // 更新该分类下所有设定的 sub_category
  const settings = store.novelSettings[store.currentNovel?.id]?.[settingTab.value]?.[subCategory] || []
  for (const s of settings) {
    await store.updateNovelSetting(store.currentNovel.id, s.id, {
      title: s.title,
      content: s.content,
      sub_category: newName
    }, settingTab.value)
  }
  expandedSubCategories.value.add(newName)
  // 刷新数据
  await store.fetchNovelSettings(store.currentNovel.id, settingTab.value)
}

const openConfig = async () => {
  showConfig.value = true
  await store.fetchSystemConfig()
  // TODO: 启用 prompt templates 需要后端 prompts router
  // await store.fetchPromptTemplates()
}

const openExport = async () => {
  if (store.currentNovel) {
    // 获取所有三个Tab的数据
    await store.fetchNovelSettings(store.currentNovel.id, '架构')
    await store.fetchNovelSettings(store.currentNovel.id, '大纲')
    await store.fetchNovelSettings(store.currentNovel.id, '备忘录')
  }
  showExport.value = true
}

const saveConfig = async () => {
  await store.saveSystemConfig()
  await store.saveWritingFlows()
  showConfig.value = false
}

const addFlow = () => {
  store.writingFlows.push({
    id: 'flow-' + Date.now(),
    name: '',
    prompt: '',
    enabled: true
  })
}

const removeFlow = async (idx: number) => {
  store.writingFlows.splice(idx, 1)
  // 删除后自动保存到后端
  await store.saveWritingFlows()
}

const onModelChange = () => {
  store.systemConfig.model = selectedModel.value
  store.saveSystemConfig()
}

const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    alert('已复制到剪贴板')
  } catch (err) {
    console.error('复制失败:', err)
  }
}
</script>
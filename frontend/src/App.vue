<template>
  <div class="h-screen flex">
    <!-- Left: 小说列表 -->
    <div class="w-56 border-r border-gray-200 bg-gray-50 p-4 overflow-y-auto">
      <h2 class="font-bold text-lg mb-4">📚 我的小说</h2>
      <!-- 小说列表，带流程树 -->
      <div v-for="novel in store.novels" :key="novel.id" class="mb-1">
        <div
          class="p-2 rounded cursor-pointer hover:bg-gray-100 flex items-center justify-between"
          :class="{ 'bg-blue-100': store.currentNovel?.id === novel.id && !store.currentFlow }"
          @click="toggleNovel(novel)"
        >
          <span class="flex-1 truncate">{{ novel.title }}</span>
          <button @click.stop="confirmDelete(novel)" class="text-gray-400 hover:text-red-500 ml-2">×</button>
        </div>
        <!-- 流程树 -->
        <div v-if="expandedNovel === novel.id && store.writingFlows.filter(f => f.enabled).length" class="ml-4 mt-1 space-y-1">
          <div
            v-for="flow in store.writingFlows.filter(f => f.enabled)"
            :key="flow.id"
            class="p-1.5 text-sm rounded cursor-pointer hover:bg-gray-200"
            :class="{ 'bg-blue-100': store.currentFlow === flow.id }"
            @click.stop="selectFlowForNovel(novel, flow.id)"
          >
            └ {{ flow.name }}
          </div>
        </div>
      </div>
      <button
        @click="createNewNovel"
        class="mt-4 w-full py-2 border-2 border-dashed border-gray-300 rounded text-gray-500 hover:border-blue-400 hover:text-blue-500"
      >
        + 新建
      </button>
      <button
        @click="openConfig"
        class="mt-2 w-full py-2 border rounded flex items-center justify-center gap-2 hover:bg-gray-100"
      >
        ⚙️ 配置
      </button>
    </div>

    <!-- Middle: 对话区 -->
    <div class="flex-1 flex flex-col">
      <div class="h-14 border-b border-gray-200 flex items-center px-4 justify-between">
        <span class="font-medium">{{ store.currentNovel?.title || '选择小说开始创作' }}</span>
        <div class="flex items-center gap-2">
          <button @click="toggleDark" class="p-1.5 rounded hover:bg-gray-100" title="切换深色模式">
            <Sun v-if="!isDark" class="w-5 h-5" />
            <Moon v-else class="w-5 h-5" />
          </button>
          <select v-model="selectedModel" @change="onModelChange" class="border rounded px-2 py-1">
            <option v-for="model in store.getModelsForProvider(store.systemConfig.provider)" :key="model" :value="model">{{ model.toUpperCase() }}</option>
            <option v-if="store.systemConfig.provider === 'custom'" value="">自定义</option>
          </select>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto p-4" ref="messageContainer">
        <div
          v-for="msg in store.messages"
          :key="msg.id"
          class="mb-4 flex"
          :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
        >
          <div
            class="inline-block p-3 rounded-lg max-w-[80%]"
            :class="msg.role === 'user' ? 'bg-[var(--user-msg-bg)] text-white' : 'bg-[var(--ai-msg-bg)]'"
          >
            {{ msg.content }}
          </div>
          <button
            v-if="msg.role === 'assistant'"
            @click="copyMessage(msg.content)"
            class="self-end ml-2 mb-1 text-xs text-gray-400 hover:text-gray-600 p-1 rounded hover:bg-gray-200"
            title="复制内容"
          >
            <Copy class="w-3 h-3" />
          </button>
        </div>
      </div>

      <div class="border-t border-gray-200 p-4">
        <input
          v-model="inputMessage"
          @keydown.enter="sendMessage"
          placeholder="输入消息..."
          class="w-full border rounded-lg p-3"
          :disabled="store.loading"
        />
        <div class="mt-2 flex gap-2">
          <button
            v-for="btn in promptButtons"
            :key="btn.name"
            @click="sendWithPrompt(btn)"
            class="px-3 py-1 border rounded hover:bg-gray-100"
          >
            {{ btn.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- Right: 写作辅助面板 -->
    <div class="w-[500px] border-l border-gray-200 bg-gray-50 p-4">
      <div class="flex gap-6 mb-4 border-b">
        <button
          v-for="tab in ['世界观', '角色', '大纲', '伏笔', 'AI配置']"
          :key="tab"
          @click="activeTab = tab"
          class="px-4 py-2 text-base"
          :class="activeTab === tab ? 'border-b-2 border-blue-500' : ''"
        >
          {{ tab }}
        </button>
      </div>
      <div class="text-gray-500 text-sm">
        {{ activeTab }} 内容展示区
      </div>
    </div>

    <!-- 配置弹窗 -->
    <div v-if="showConfig" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-[var(--bg-primary)] rounded-lg w-[500px] max-h-[80vh] overflow-y-auto">
        <div class="flex items-center justify-between p-4 border-b">
          <span class="font-bold">⚙️ 系统配置</span>
          <button @click="showConfig = false">✕</button>
        </div>
        <div class="flex border-b">
          <button
            @click="configTab = 'api'"
            class="px-4 py-2"
            :class="configTab === 'api' ? 'border-b-2 border-blue-500' : ''"
          >
            API配置
          </button>
          <button
            @click="configTab = 'prompt'"
            class="px-4 py-2"
            :class="configTab === 'prompt' ? 'border-b-2 border-blue-500' : ''"
          >
            提示词模板
          </button>
          <button
            @click="configTab = 'flows'"
            class="px-4 py-2"
            :class="configTab === 'flows' ? 'border-b-2 border-blue-500' : ''"
          >
            创作流程
          </button>
        </div>
        <div class="p-4">
          <div v-if="configTab === 'api'">
            <div class="mb-4">
              <label class="block text-sm mb-1">Provider</label>
              <select v-model="store.systemConfig.provider" class="w-full border rounded p-2">
                <option value="openai">OpenAI</option>
                <option value="deepseek">DeepSeek</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div class="mb-4">
              <label class="block text-sm mb-1">API Key</label>
              <input
                v-model="store.systemConfig.apiKey"
                type="password"
                class="w-full border rounded p-2"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm mb-1">模型</label>
              <select
                v-model="store.systemConfig.model"
                class="w-full border rounded p-2"
                :disabled="store.systemConfig.provider === 'custom'"
              >
                <option
                  v-for="model in store.getModelsForProvider(store.systemConfig.provider)"
                  :key="model"
                  :value="model"
                >
                  {{ model.toUpperCase() }}
                </option>
                <option v-if="store.systemConfig.provider === 'custom'" value="">
                  自定义模型
                </option>
              </select>
            </div>
            <div v-if="store.systemConfig.provider === 'custom'" class="mb-4">
              <label class="block text-sm mb-1">Base URL</label>
              <input
                v-model="store.systemConfig.baseUrl"
                type="text"
                placeholder="https://api.example.com/v1"
                class="w-full border rounded p-2"
              />
            </div>
            <div v-if="store.systemConfig.provider === 'custom' && !store.getModelsForProvider(store.systemConfig.provider).includes(store.systemConfig.model)" class="mb-4">
              <label class="block text-sm mb-1">模型名称</label>
              <input
                v-model="store.systemConfig.model"
                type="text"
                placeholder="e.g. claude-3-opus"
                class="w-full border rounded p-2"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm mb-1">Temperature: {{ store.systemConfig.temperature }}</label>
              <input
                v-model="store.systemConfig.temperature"
                type="range"
                min="0"
                max="2"
                step="0.1"
                class="w-full"
              />
            </div>
            <div class="mb-4">
              <label class="block text-sm mb-1">Max Tokens: {{ store.systemConfig.maxTokens }}</label>
              <input
                v-model="store.systemConfig.maxTokens"
                type="number"
                min="1"
                max="128000"
                class="w-full border rounded p-2"
              />
            </div>
          </div>
          <div v-if="configTab === 'prompt'">
            <div v-for="(t, idx) in store.promptTemplates" :key="idx" class="mb-4">
              <label class="block text-sm mb-1">{{ t.name }}</label>
              <textarea
                v-model="t.content"
                class="w-full border rounded p-2"
                rows="2"
              ></textarea>
            </div>
          </div>
          <div v-if="configTab === 'flows'">
            <div v-for="(flow, idx) in store.writingFlows" :key="flow.id" class="mb-3 p-2 border rounded">
              <div class="flex items-center gap-2 mb-1">
                <input
                  v-model="flow.name"
                  class="border rounded px-2 py-1 flex-1"
                  placeholder="名称"
                />
                <input
                  type="checkbox"
                  v-model="flow.enabled"
                  :id="'flow-enabled-' + flow.id"
                />
                <label :for="'flow-enabled-' + flow.id" class="text-sm">启用</label>
                <button @click="removeFlow(idx)" class="text-red-500">删除</button>
              </div>
              <textarea
                v-model="flow.prompt"
                class="w-full border rounded p-2"
                rows="2"
                placeholder="流程提示词前缀"
              ></textarea>
            </div>
            <button @click="addFlow" class="w-full py-2 border-2 border-dashed border-gray-300 rounded text-gray-500 hover:border-blue-400">
              + 新增流程
            </button>
          </div>
        </div>
        <div class="flex justify-end gap-2 p-4 border-t">
          <button @click="showConfig = false" class="px-4 py-2 border rounded">取消</button>
          <button @click="saveConfig" class="px-4 py-2 bg-blue-500 text-white rounded">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { Sun, Moon, Copy } from 'lucide-vue-next'
import { useChatStore } from './stores/chat'
import type { Novel } from './stores/chat'

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
  // 自动选择第一个小说并加载对话
  if (store.novels.length > 0) {
    await store.selectNovel(store.novels[0])
    scrollToBottom()
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

const expandedNovel = ref<number | null>(null)

const toggleNovel = async (novel: Novel) => {
  if (expandedNovel.value === novel.id) {
    expandedNovel.value = null
  } else {
    expandedNovel.value = novel.id
  }
  // Don't call any APIs - just expand and show flow selection
  // User must explicitly click a flow to enter
}

const selectFlowForNovel = async (novel: Novel, flowId: string) => {
  // 直接切换 novel 和 flow，不需要调用 selectNovel（它会循环所有接口）
  store.currentNovel = novel
  await store.selectFlow(flowId)
}

const showConfig = ref(false)
const configTab = ref('api')

const openConfig = async () => {
  showConfig.value = true
  await store.fetchSystemConfig()
  // TODO: 启用 prompt templates 需要后端 prompts router
  // await store.fetchPromptTemplates()
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

const removeFlow = (idx: number) => {
  store.writingFlows.splice(idx, 1)
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
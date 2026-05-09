<template>
  <div class="h-screen flex">
    <!-- Left: 小说列表 -->
    <div class="w-56 border-r border-gray-200 bg-gray-50 p-4">
      <h2 class="font-bold text-lg mb-4">📚 我的小说</h2>
      <div
        v-for="novel in store.novels"
        :key="novel.id"
        class="p-2 rounded cursor-pointer hover:bg-gray-100"
        :class="{ 'bg-blue-100': store.currentNovel?.id === novel.id }"
        @click="store.selectNovel(novel)"
      >
        {{ novel.title }}
      </div>
      <button
        @click="createNewNovel"
        class="mt-4 w-full py-2 border-2 border-dashed border-gray-300 rounded text-gray-500 hover:border-blue-400 hover:text-blue-500"
      >
        + 新建
      </button>
    </div>

    <!-- Middle: 对话区 -->
    <div class="flex-1 flex flex-col">
      <div class="h-14 border-b border-gray-200 flex items-center px-4 justify-between">
        <span class="font-medium">{{ store.currentNovel?.title || '选择小说开始创作' }}</span>
        <select v-model="selectedModel" class="border rounded px-2 py-1">
          <option value="gpt-4">GPT-4</option>
          <option value="claude-3">Claude 3</option>
        </select>
      </div>

      <div class="flex-1 overflow-y-auto p-4">
        <div
          v-for="msg in store.messages"
          :key="msg.id"
          class="mb-4"
          :class="msg.role === 'user' ? 'text-right' : 'text-left'"
        >
          <div
            class="inline-block p-3 rounded-lg max-w-[80%]"
            :class="msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200'"
          >
            {{ msg.content }}
          </div>
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
    <div class="w-72 border-l border-gray-200 bg-gray-50 p-4">
      <div class="flex gap-2 mb-4">
        <button
          v-for="tab in ['世界观', '角色', '大纲', '伏笔', 'AI配置']"
          :key="tab"
          @click="activeTab = tab"
          class="px-2 py-1 text-sm"
          :class="activeTab === tab ? 'border-b-2 border-blue-500' : ''"
        >
          {{ tab }}
        </button>
      </div>
      <div class="text-gray-500 text-sm">
        {{ activeTab }} 内容展示区
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChatStore } from './stores/chat'

const store = useChatStore()
const inputMessage = ref('')
const selectedModel = ref('gpt-4')
const activeTab = ref('世界观')
const promptButtons = ref([
  { name: '总结', content: '请总结以上内容要点：' },
  { name: '润色', content: '请润色以下内容：' },
  { name: '续写', content: '请续写：' },
  { name: '扩写', content: '请扩写：' }
])

onMounted(() => {
  store.fetchedNovels()
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
</script>
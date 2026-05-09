import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
}

export interface Novel {
  id: number
  title: string
  created_at: string
}

export const useChatStore = defineStore('chat', () => {
  const novels = ref<Novel[]>([])
  const currentNovel = ref<Novel | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)

  const fetchedNovels = async () => {
    const res = await axios.get('/api/novels')
    novels.value = res.data
  }

  const createNovel = async (title: string) => {
    const res = await axios.post('/api/novels', { title })
    novels.value.push(res.data)
    return res.data
  }

  const selectNovel = async (novel: Novel) => {
    currentNovel.value = novel
    const res = await axios.get('/api/novels/' + novel.id + '/messages')
    messages.value = res.data
  }

  const sendMessage = async (content: string, promptButtons: string[] = []) => {
    if (!currentNovel.value) return

    loading.value = true
    messages.value.push({ id: 0, role: 'user', content })

    try {
      const res = await axios.post('/api/chat', {
        novel_id: currentNovel.value.id,
        messages: [{ role: 'user', content }],
        prompt_buttons: promptButtons
      }, {
        responseType: 'stream'
      })

      const reader = res.data.getReader()
      const decoder = new TextDecoder()
      let assistantContent = ''

      while (true) {
        const result = await reader.read()
        if (result.done) break
        const chunk = decoder.decode(result.value)
        assistantContent += chunk
      }

      messages.value.push({ id: 0, role: 'assistant', content: assistantContent })
    } catch (e) {
      console.error(e)
    } finally {
      loading.value = false
    }
  }

  const deleteNovel = async (id: number) => {
    await axios.delete('/api/novels/' + id)
    novels.value = novels.value.filter(n => n.id !== id)
    if (currentNovel.value?.id === id) {
      currentNovel.value = null
      messages.value = []
    }
  }

  const systemConfig = ref({
    provider: 'openai',
    baseUrl: '',
    model: 'gpt-4',
    apiKey: '',
    temperature: 0.7,
    maxTokens: 4096
  })

  const promptTemplates = ref([
    { name: '总结', content: '请总结以上内容要点：' },
    { name: '润色', content: '请润色以下内容：' },
    { name: '续写', content: '请续写：' },
    { name: '扩写', content: '请扩写：' }
  ])

  const providerTemplates = {
    openai: {
      base_url: 'https://api.openai.com/v1',
      models: ['gpt-4', 'gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo']
    },
    deepseek: {
      base_url: 'https://api.deepseek.com',
      models: ['deepseek-chat']
    },
    custom: {
      base_url: '',
      models: []
    }
  }

  const fetchSystemConfig = async () => {
    const res = await axios.get('/api/model-configs')
    if (res.data.length > 0) {
      const config = res.data[0]
      const provider = config.provider || 'openai'
      systemConfig.value = {
        provider: provider,
        baseUrl: config.base_url || providerTemplates[provider]?.base_url || '',
        model: config.model || 'gpt-4',
        apiKey: config.api_key || '',
        temperature: config.temperature || 0.7,
        maxTokens: config.max_tokens || 4096
      }
    }
  }

  const saveSystemConfig = async () => {
    await axios.post('/api/model-configs', {
      provider: systemConfig.value.provider,
      base_url: systemConfig.value.baseUrl,
      model: systemConfig.value.model,
      api_key: systemConfig.value.apiKey,
      temperature: systemConfig.value.temperature,
      max_tokens: systemConfig.value.maxTokens
    })
  }

  const fetchPromptTemplates = async () => {
    const res = await axios.get('/api/prompt-buttons')
    promptTemplates.value = res.data.map((b: any) => ({ name: b.name, content: b.content }))
  }

  const savePromptTemplates = async () => {
    for (const t of promptTemplates.value) {
      await axios.post('/api/prompt-buttons', {
        name: t.name,
        button_type: 'prompt',
        content: t.content,
        category: 'default'
      })
    }
  }

  const getModelsForProvider = (provider: string) => {
    return providerTemplates[provider]?.models || []
  }

  return {
    novels,
    currentNovel,
    messages,
    loading,
    fetchedNovels,
    createNovel,
    selectNovel,
    sendMessage,
    deleteNovel,
    systemConfig,
    promptTemplates,
    fetchSystemConfig,
    saveSystemConfig,
    fetchPromptTemplates,
    savePromptTemplates,
    getModelsForProvider,
    providerTemplates
  }
})
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

export interface WritingFlow {
  id: string
  name: string
  prompt: string
  enabled: boolean
}

export const useChatStore = defineStore('chat', () => {
  const novels = ref<Novel[]>([])
  const currentNovel = ref<Novel | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const sessionTokens = ref(0)

  const writingFlows = ref<WritingFlow[]>([
    { id: 'outline', name: '大纲', prompt: '请帮我设计小说大纲：', enabled: true },
    { id: 'volume', name: '卷纲', prompt: '请帮我设计这一卷的卷纲：', enabled: true },
    { id: 'body', name: '正文', prompt: '请续写以下内容：', enabled: true }
  ])
  const currentFlow = ref<string | null>(null)

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

    // 如果选择了流程，添加流程提示词前缀
    let finalContent = content
    if (currentFlow.value) {
      const flow = writingFlows.value.find(f => f.id === currentFlow.value)
      if (flow?.prompt) {
        finalContent = flow.prompt + '\n' + content
      }
    }

    loading.value = true
    messages.value.push({ id: 0, role: 'user', content: finalContent })

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          novel_id: currentNovel.value.id,
          messages: [{ role: 'user', content: finalContent }],
          prompt_buttons: promptButtons
        })
      })

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`)
      }

      if (!res.body) {
        throw new Error('No response body')
      }

      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let assistantContent = ''

      while (true) {
        const result = await reader.read()
        if (result.done) break
        const chunk = decoder.decode(result.value)
        // 按行分割处理 SSE 数据
        const lines = chunk.split('\n')
        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed) continue

          let jsonStr = trimmed
          // 移除 "data: " 前缀
          if (jsonStr.startsWith('data: ')) {
            jsonStr = jsonStr.slice(6)
          }

          if (jsonStr === '[DONE]') continue
          if (!jsonStr.startsWith('{')) continue

          try {
            const data = JSON.parse(jsonStr)
            const usage = data.usage
            if (usage) {
              const prompt_tokens = usage.prompt_tokens || 0
              const completion_tokens = usage.completion_tokens || 0
              const total_tokens = usage.total_tokens || (prompt_tokens + completion_tokens)
              sessionTokens.value += total_tokens
            }
            const choices = data.choices
            if (choices && choices.length > 0) {
              const delta = choices[0].delta
              // 只提取字符串 content
              const content = typeof delta?.content === 'string' ? delta.content : ''
              if (content) {
                assistantContent += content
              }
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }

      messages.value.push({ id: 0, role: 'assistant', content: assistantContent })
      // 保存 AI 回复到数据库
      if (currentNovel.value && assistantContent) {
        try {
          await axios.post(`/api/novels/${currentNovel.value.id}/messages`, {
            role: 'assistant',
            content: assistantContent
          })
        } catch (e) {
          console.error('Failed to save assistant message:', e)
        }
      }
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

  const updateNovelTitle = async (id: number, title: string) => {
    await axios.put('/api/novels/' + id, { title })
    const novel = novels.value.find(n => n.id === id)
    if (novel) {
      novel.title = title
    }
    if (currentNovel.value?.id === id) {
      currentNovel.value.title = title
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
        // 优先使用保存的 base_url，否则使用模板默认值
        baseUrl: config.base_url || providerTemplates[provider]?.base_url || '',
        model: config.model || providerTemplates[provider]?.models?.[0] || 'gpt-4',
        apiKey: config.api_key || '',
        temperature: config.temperature ?? 0.7,
        maxTokens: config.max_tokens || 4096
      }
    }
  }

  const saveSystemConfig = async () => {
    // 更新 id=1 的配置（默认配置）
    await axios.put('/api/model-configs/1', {
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

  const fetchWritingFlows = async () => {
    const res = await axios.get('/api/model-configs')
    if (res.data.length > 0) {
      const config = res.data[0]
      const templates = config.prompt_templates
      if (templates) {
        try {
          const obj = JSON.parse(templates)
          if (obj.writing_flows) {
            writingFlows.value = obj.writing_flows
          }
        } catch (e) {}
      }
    }
  }

  const saveWritingFlows = async () => {
    const res = await axios.get('/api/model-configs')
    if (res.data.length > 0) {
      const config = res.data[0]
      const templates = JSON.stringify({ writing_flows: writingFlows.value })
      await axios.put('/api/model-configs/1', {
        ...config,
        prompt_templates: templates
      })
    }
  }

  const selectFlow = async (flowId: string | null) => {
    currentFlow.value = flowId
    if (currentNovel.value) {
      const res = await axios.get(`/api/novels/${currentNovel.value.id}/messages?flow_type=${flowId || ''}`)
      messages.value = res.data
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
    sessionTokens,
    fetchedNovels,
    createNovel,
    selectNovel,
    sendMessage,
    deleteNovel,
    updateNovelTitle,
    systemConfig,
    promptTemplates,
    fetchSystemConfig,
    saveSystemConfig,
    fetchPromptTemplates,
    savePromptTemplates,
    getModelsForProvider,
    providerTemplates,
    writingFlows,
    currentFlow,
    fetchWritingFlows,
    saveWritingFlows,
    selectFlow
  }
})
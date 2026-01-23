// API service for AI Investment Advisor
import axios from 'axios'
import type { Skill, FileInfo, Holdings, ApiKeyConfig, ConfigFile } from '../types'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
})

// 长时间操作使用更长的超时
const longApi = axios.create({
  baseURL: API_BASE,
  timeout: 300000,  // 5分钟，用于同步等耗时操作
})

// Skills API
export async function getSkills(): Promise<Skill[]> {
  const { data } = await api.get('/skills')
  return data.skills
}

export async function getSkill(name: string): Promise<Skill> {
  const { data } = await api.get(`/skills/${name}`)
  return data
}

// Holdings API
export async function getHoldings(): Promise<Holdings> {
  const { data } = await api.get('/holdings')
  return data
}

export async function getHoldingsSummary() {
  const { data } = await api.get('/holdings/summary')
  return data
}

// Files API
export async function listFiles(type?: string, limit = 20, offset = 0): Promise<{ files: FileInfo[]; total: number }> {
  const params: Record<string, string | number> = { limit, offset }
  if (type) params.type = type
  const { data } = await api.get('/files', { params })
  return data
}

export async function getFileContent(path: string): Promise<{ name: string; content: string; type: string; updated_at: string }> {
  const { data } = await api.get('/files/content', { params: { path } })
  return data
}

export async function getRecentFiles(limit = 5): Promise<FileInfo[]> {
  const { data } = await api.get('/files/recent', { params: { limit } })
  return data.files
}

// Config API
export async function getConfig(name: string): Promise<ConfigFile> {
  const { data } = await api.get(`/config/${name}`)
  return data
}

export async function updateConfig(name: string, content: string) {
  const { data } = await api.put(`/config/${name}`, { content })
  return data
}

export async function listConfigs() {
  const { data } = await api.get('/config/list')
  return data.configs
}

// API Keys API
export async function getApiKeys(): Promise<ApiKeyConfig> {
  const { data } = await api.get('/apikeys')
  return data
}

export async function updateApiKeys(config: Partial<ApiKeyConfig>) {
  const { data } = await api.put('/apikeys', config)
  return data
}

// Yuque Sync API (deprecated, kept for compatibility)
export async function syncToYuque(files?: string[], force = false) {
  const { data } = await api.post('/sync/yuque', { files, force })
  return data
}

export async function getYuqueStatus() {
  const { data } = await api.get('/sync/yuque/status')
  return data
}

// Notion Sync API
export async function syncToNotion(files?: string[], force = false) {
  const { data } = await longApi.post('/sync/notion', { files, force })
  return data
}

export async function syncAllToNotion(options?: {
  include_config?: boolean
  include_daily?: boolean
  include_brief?: boolean
  include_analysis?: boolean
  include_scan?: boolean
  include_records?: boolean
  include_committee?: boolean
}) {
  const { data } = await longApi.post('/sync/notion/all', options || {})
  return data
}

export async function getNotionStatus() {
  const { data } = await api.get('/sync/notion/status')
  return data
}

// Notion Config API
export async function getNotionConfig() {
  const { data } = await api.get('/sync/notion/config')
  return data
}

export async function updateNotionConfig(config: { api_key: string; page_id: string }) {
  const { data } = await api.put('/sync/notion/config', config)
  return data
}

export async function testNotionConnection() {
  const { data } = await api.post('/sync/notion/test')
  return data
}

// Command execution with SSE (GET-based, not currently used)
export function executeCommand(
  command: string,
  args = '',
  timeout = 300,
  onMessage: (event: MessageEvent) => void,
  onError: (error: Event) => void
): EventSource {
  // Use fetch + ReadableStream for POST with SSE
  const eventSource = new EventSource(`${API_BASE}/command/stream?command=${encodeURIComponent(command)}&args=${encodeURIComponent(args)}&timeout=${timeout}`)

  eventSource.addEventListener('output', onMessage)
  eventSource.addEventListener('error', onError)

  return eventSource
}

// Alternative: use fetch for POST-based SSE
export async function executeCommandPost(
  command: string,
  args = '',
  timeout = 300,
  onEvent: (event: Record<string, unknown>) => void
): Promise<void> {
  const response = await fetch(`${API_BASE}/command`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ command, args, timeout }),
  })

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // Parse SSE events
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    let currentData = ''

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        // Event type (currently unused, data is self-describing)
      } else if (line.startsWith('data: ')) {
        currentData = line.slice(6)
      } else if (line === '' && currentData) {
        try {
          const parsed = JSON.parse(currentData)
          onEvent(parsed)
        } catch {
          // Ignore parse errors
        }
        currentData = ''
      }
    }
  }
}

// Cancel running command
export async function cancelCommand() {
  const { data } = await api.post('/command/cancel')
  return data
}

// Get command status
export async function getCommandStatus() {
  const { data } = await api.get('/command/status')
  return data
}

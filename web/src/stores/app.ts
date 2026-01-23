import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { Skill, FileInfo, TerminalEvent } from '../types'
import * as api from '../api'

const TERMINAL_HISTORY_KEY = 'terminal_history'
const MAX_HISTORY_SIZE = 500 // 最多保存500条事件

// 从 localStorage 加载历史
function loadHistoryFromStorage(): TerminalEvent[] {
  try {
    const saved = localStorage.getItem(TERMINAL_HISTORY_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('Failed to load terminal history:', e)
  }
  return []
}

// 保存历史到 localStorage
function saveHistoryToStorage(history: TerminalEvent[]) {
  try {
    // 只保存最近的记录
    const toSave = history.slice(-MAX_HISTORY_SIZE)
    localStorage.setItem(TERMINAL_HISTORY_KEY, JSON.stringify(toSave))
  } catch (e) {
    console.error('Failed to save terminal history:', e)
  }
}

export const useAppStore = defineStore('app', () => {
  // State
  const skills = ref<Skill[]>([])
  const recentFiles = ref<FileInfo[]>([])
  const terminalHistory = ref<TerminalEvent[]>(loadHistoryFromStorage())
  const isExecuting = ref(false)
  const currentCommand = ref('')

  // 监听历史变化，自动保存
  watch(terminalHistory, (newHistory) => {
    saveHistoryToStorage(newHistory)
  }, { deep: true })

  // Actions
  async function loadSkills() {
    try {
      skills.value = await api.getSkills()
    } catch (error) {
      console.error('Failed to load skills:', error)
    }
  }

  async function loadRecentFiles() {
    try {
      recentFiles.value = await api.getRecentFiles(5)
    } catch (error) {
      console.error('Failed to load recent files:', error)
    }
  }

  function addTerminalEvent(event: TerminalEvent) {
    terminalHistory.value.push(event)
    // 如果超过最大限制，删除最早的记录
    if (terminalHistory.value.length > MAX_HISTORY_SIZE) {
      terminalHistory.value = terminalHistory.value.slice(-MAX_HISTORY_SIZE)
    }
  }

  function clearTerminal() {
    terminalHistory.value = []
    localStorage.removeItem(TERMINAL_HISTORY_KEY)
  }

  async function executeCommand(command: string, args = '') {
    if (isExecuting.value) {
      console.warn('A command is already running')
      return
    }

    isExecuting.value = true
    currentCommand.value = command

    // Add command to history
    addTerminalEvent({
      type: 'text',
      content: `\n$ ${command}${args ? ' ' + args : ''}\n`,
    })

    try {
      await api.executeCommandPost(command, args, 1800, (event) => {
        const termEvent = event as unknown as TerminalEvent
        addTerminalEvent(termEvent)

        if (termEvent.type === 'done' || termEvent.type === 'error') {
          isExecuting.value = false
          currentCommand.value = ''
        }
      })
    } catch (error) {
      addTerminalEvent({
        type: 'error',
        message: String(error),
      })
      isExecuting.value = false
      currentCommand.value = ''
    }

    // Refresh recent files after command completes
    loadRecentFiles()
  }

  async function cancelExecution() {
    if (!isExecuting.value) return

    try {
      await api.cancelCommand()
      addTerminalEvent({
        type: 'text',
        content: '\n[命令已取消]\n',
      })
    } catch (error) {
      console.error('Failed to cancel:', error)
    }

    isExecuting.value = false
    currentCommand.value = ''
  }

  return {
    skills,
    recentFiles,
    terminalHistory,
    isExecuting,
    currentCommand,
    loadSkills,
    loadRecentFiles,
    addTerminalEvent,
    clearTerminal,
    executeCommand,
    cancelExecution,
  }
})

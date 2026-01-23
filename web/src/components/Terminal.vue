<template>
  <div class="terminal-container">
    <div ref="terminalRef" class="terminal"></div>
    <!-- 等待动画覆盖层 -->
    <div v-if="isWaiting" class="waiting-overlay">
      <div class="waiting-content">
        <div class="spinner"></div>
        <div class="waiting-text">{{ waitingText }}</div>
        <div class="waiting-dots">{{ dots }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { Terminal } from '@xterm/xterm'
import { FitAddon } from '@xterm/addon-fit'
import '@xterm/xterm/css/xterm.css'
import type { TerminalEvent } from '../types'

const props = defineProps<{
  events: TerminalEvent[]
  isExecuting?: boolean
}>()

const terminalRef = ref<HTMLDivElement>()
let terminal: Terminal | null = null
let fitAddon: FitAddon | null = null
let processedIndex = 0

// 等待动画状态
const isWaiting = ref(false)
const waitingText = ref('Claude 正在思考')
const dots = ref('')
let dotsInterval: ReturnType<typeof setInterval> | null = null
let lastEventTime = 0

// 动画：更新等待文字的点
function startDotsAnimation() {
  if (dotsInterval) return
  dotsInterval = setInterval(() => {
    dots.value = dots.value.length >= 3 ? '' : dots.value + '.'
  }, 500)
}

function stopDotsAnimation() {
  if (dotsInterval) {
    clearInterval(dotsInterval)
    dotsInterval = null
  }
  dots.value = ''
}

// 监听执行状态
watch(() => props.isExecuting, (executing) => {
  if (executing) {
    // 开始执行时，延迟显示等待动画（如果3秒内没有输出）
    lastEventTime = Date.now()
    setTimeout(() => {
      if (props.isExecuting && Date.now() - lastEventTime > 2500) {
        isWaiting.value = true
        startDotsAnimation()
      }
    }, 3000)
  } else {
    isWaiting.value = false
    stopDotsAnimation()
  }
})

onMounted(() => {
  if (!terminalRef.value) return

  terminal = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: 'Menlo, Monaco, "Courier New", monospace',
    theme: {
      background: '#1e1e1e',
      foreground: '#d4d4d4',
      cursor: '#d4d4d4',
      selectionBackground: '#264f78',
      black: '#000000',
      red: '#cd3131',
      green: '#0dbc79',
      yellow: '#e5e510',
      blue: '#2472c8',
      magenta: '#bc3fbc',
      cyan: '#11a8cd',
      white: '#e5e5e5',
    },
    convertEol: true,
    scrollback: 10000,
  })

  fitAddon = new FitAddon()
  terminal.loadAddon(fitAddon)
  terminal.open(terminalRef.value)

  // Fit terminal to container
  setTimeout(() => fitAddon?.fit(), 0)

  // Handle resize
  const resizeObserver = new ResizeObserver(() => {
    fitAddon?.fit()
  })
  resizeObserver.observe(terminalRef.value)

  // Welcome message
  terminal.writeln('\x1b[36m╔══════════════════════════════════════════════════╗\x1b[0m')
  terminal.writeln('\x1b[36m║\x1b[0m   \x1b[1;33mAI Investment Advisor\x1b[0m                          \x1b[36m║\x1b[0m')
  terminal.writeln('\x1b[36m║\x1b[0m   输入命令开始，如 /brief, /scan, /analyze       \x1b[36m║\x1b[0m')
  terminal.writeln('\x1b[36m╚══════════════════════════════════════════════════╝\x1b[0m')
  terminal.writeln('')

  // 渲染已有的历史记录
  if (props.events.length > 0) {
    terminal.writeln('\x1b[90m--- 历史记录 ---\x1b[0m')
    for (const event of props.events) {
      renderEvent(event)
    }
    processedIndex = props.events.length
    terminal.writeln('\x1b[90m--- 历史结束 ---\x1b[0m\n')
  }

  onUnmounted(() => {
    resizeObserver.disconnect()
    terminal?.dispose()
    stopDotsAnimation()
  })
})

// Watch for new events and render them
watch(
  () => props.events.length,
  () => {
    if (!terminal) return

    // 有新事件，更新时间戳并隐藏等待动画
    lastEventTime = Date.now()
    isWaiting.value = false

    // Process new events
    while (processedIndex < props.events.length) {
      const event = props.events[processedIndex]
      if (event) {
        renderEvent(event)
      }
      processedIndex++
    }
  }
)

function renderEvent(event: TerminalEvent) {
  if (!terminal) return

  switch (event.type) {
    case 'system':
      // 显示系统初始化信息
      terminal.writeln('\x1b[90m[系统初始化完成]\x1b[0m')
      break

    case 'text':
      if (event.content) {
        // 直接输出文本，保留换行
        terminal.write(event.content)
      }
      break

    case 'raw':
      // 原始输出
      if (event.content) {
        terminal.writeln(`\x1b[90m${event.content}\x1b[0m`)
      }
      break

    case 'tool_start':
      terminal.writeln(`\n\x1b[35m▶ [${event.tool}]\x1b[0m`)
      if (event.input) {
        const inputStr = typeof event.input === 'string'
          ? event.input
          : JSON.stringify(event.input, null, 2)
        // 显示更多工具输入内容
        if (inputStr.length < 500) {
          terminal.writeln(`\x1b[90m${inputStr}\x1b[0m`)
        } else {
          terminal.writeln(`\x1b[90m${inputStr.substring(0, 500)}...\x1b[0m`)
        }
      }
      break

    case 'tool_result':
      // 显示更多工具结果
      if (event.result) {
        const result = String(event.result)
        if (result.length < 2000) {
          terminal.writeln(`\x1b[32m${result}\x1b[0m`)
        } else {
          terminal.writeln(`\x1b[32m${result.substring(0, 2000)}...\x1b[0m`)
        }
      }
      break

    case 'final':
      // 最终结果
      if (event.content) {
        terminal.writeln(`\n\x1b[36m${event.content}\x1b[0m`)
      }
      break

    case 'done':
      if (event.status === 'success') {
        terminal.writeln('\n\x1b[32m✓ 完成\x1b[0m\n')
      } else {
        terminal.writeln(`\n\x1b[33m⚠ 完成 (exit: ${event.exit_code})\x1b[0m\n`)
      }
      break

    case 'error':
      terminal.writeln(`\n\x1b[31m✗ 错误: ${event.message}\x1b[0m\n`)
      break

    default:
      // 其他未知类型，显示原始 JSON
      terminal.writeln(`\x1b[90m[${event.type}] ${JSON.stringify(event).substring(0, 200)}\x1b[0m`)
  }
}

// Expose clear method
defineExpose({
  clear() {
    terminal?.clear()
    processedIndex = 0
  },
})
</script>

<style scoped>
.terminal-container {
  width: 100%;
  height: 100%;
  background: #1e1e1e;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.terminal {
  width: 100%;
  height: 100%;
  padding: 8px;
}

/* 等待动画覆盖层 */
.waiting-overlay {
  position: absolute;
  bottom: 60px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(30, 30, 30, 0.95);
  border: 1px solid #404040;
  border-radius: 8px;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 10;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.waiting-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #404040;
  border-top-color: #4fc1ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.waiting-text {
  color: #d4d4d4;
  font-size: 14px;
}

.waiting-dots {
  color: #4fc1ff;
  font-size: 14px;
  width: 20px;
}
</style>

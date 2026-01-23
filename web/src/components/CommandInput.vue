<template>
  <div class="command-input">
    <div class="input-wrapper">
      <span class="prompt">$</span>
      <input
        v-model="inputValue"
        type="text"
        placeholder="输入命令，如 /brief, /scan NVDA, /analyze 比亚迪"
        :disabled="isExecuting"
        @keydown.enter="handleSubmit"
        @keydown.up="historyUp"
        @keydown.down="historyDown"
        @keydown.tab.prevent="handleAutocomplete"
        ref="inputRef"
      />
      <button
        v-if="isExecuting"
        class="cancel-btn"
        @click="$emit('cancel')"
        title="取消执行"
      >
        ■
      </button>
      <button
        v-else
        class="send-btn"
        @click="handleSubmit"
        :disabled="!inputValue.trim()"
        title="执行命令"
      >
        ▶
      </button>
    </div>

    <div v-if="showSuggestions && suggestions.length" class="suggestions">
      <div
        v-for="(suggestion, index) in suggestions"
        :key="suggestion.command"
        class="suggestion-item"
        :class="{ active: index === selectedSuggestion }"
        @click="selectSuggestion(suggestion)"
      >
        <span class="command">{{ suggestion.command }}</span>
        <span class="description">{{ suggestion.description }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { Skill } from '../types'

const props = defineProps<{
  skills: Skill[]
  isExecuting: boolean
}>()

const emit = defineEmits<{
  (e: 'execute', command: string): void
  (e: 'cancel'): void
}>()

const inputValue = ref('')
const inputRef = ref<HTMLInputElement>()
const commandHistory = ref<string[]>([])
const historyIndex = ref(-1)
const showSuggestions = ref(false)
const selectedSuggestion = ref(0)

const suggestions = computed(() => {
  if (!inputValue.value.startsWith('/')) return []

  const query = inputValue.value.toLowerCase()
  return props.skills
    .filter((s) => s.command.toLowerCase().includes(query) || s.triggers.some((t) => t.toLowerCase().includes(query)))
    .slice(0, 5)
})

watch(inputValue, () => {
  showSuggestions.value = inputValue.value.startsWith('/')
  selectedSuggestion.value = 0
})

function handleSubmit() {
  const command = inputValue.value.trim()
  if (!command || props.isExecuting) return

  commandHistory.value.unshift(command)
  historyIndex.value = -1
  emit('execute', command)
  inputValue.value = ''
  showSuggestions.value = false
}

function historyUp() {
  if (commandHistory.value.length === 0) return
  if (historyIndex.value < commandHistory.value.length - 1) {
    historyIndex.value++
    inputValue.value = commandHistory.value[historyIndex.value] ?? ''
  }
}

function historyDown() {
  if (historyIndex.value > 0) {
    historyIndex.value--
    inputValue.value = commandHistory.value[historyIndex.value] ?? ''
  } else if (historyIndex.value === 0) {
    historyIndex.value = -1
    inputValue.value = ''
  }
}

function handleAutocomplete() {
  const suggestion = suggestions.value[selectedSuggestion.value]
  if (suggestion) {
    selectSuggestion(suggestion)
  }
}

function selectSuggestion(skill: Skill) {
  inputValue.value = skill.command + ' '
  showSuggestions.value = false
  inputRef.value?.focus()
}

defineExpose({
  focus() {
    inputRef.value?.focus()
  },
})
</script>

<style scoped>
.command-input {
  position: relative;
  padding: 12px 16px;
  background: #2d2d2d;
  border-top: 1px solid #404040;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #1e1e1e;
  border-radius: 8px;
  padding: 0 12px;
}

.prompt {
  color: #0dbc79;
  font-weight: bold;
  font-family: monospace;
}

input {
  flex: 1;
  padding: 12px 0;
  background: transparent;
  border: none;
  color: #d4d4d4;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  outline: none;
}

input::placeholder {
  color: #6a6a6a;
}

input:disabled {
  opacity: 0.6;
}

.send-btn,
.cancel-btn {
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn {
  background: #0dbc79;
  color: white;
}

.send-btn:hover:not(:disabled) {
  background: #0a9d66;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn {
  background: #cd3131;
  color: white;
}

.cancel-btn:hover {
  background: #b62c2c;
}

.suggestions {
  position: absolute;
  bottom: 100%;
  left: 16px;
  right: 16px;
  background: #252526;
  border: 1px solid #404040;
  border-radius: 8px;
  margin-bottom: 8px;
  max-height: 200px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 10px 12px;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suggestion-item:hover,
.suggestion-item.active {
  background: #2a2d2e;
}

.suggestion-item .command {
  color: #4fc1ff;
  font-family: monospace;
}

.suggestion-item .description {
  color: #858585;
  font-size: 12px;
}
</style>

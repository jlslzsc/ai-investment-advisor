<template>
  <div class="home">
    <div class="terminal-area">
      <Terminal ref="terminalRef" :events="terminalHistory" :is-executing="isExecuting" />
    </div>
    <CommandInput
      :skills="skills"
      :is-executing="isExecuting"
      @execute="executeCommand"
      @cancel="cancelExecution"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAppStore } from '../stores/app'
import Terminal from '../components/Terminal.vue'
import CommandInput from '../components/CommandInput.vue'

const store = useAppStore()

const skills = computed(() => store.skills)
const terminalHistory = computed(() => store.terminalHistory)
const isExecuting = computed(() => store.isExecuting)

onMounted(() => {
  store.loadSkills()
  store.loadRecentFiles()
})

function executeCommand(command: string) {
  // Parse command and arguments
  const parts = command.match(/^(\/\S+)?\s*(.*)?$/)
  if (parts) {
    const cmd = parts[1] || command
    const args = parts[2] || ''
    store.executeCommand(cmd, args)
  } else {
    store.executeCommand(command)
  }
}

function cancelExecution() {
  store.cancelExecution()
}
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e1e1e;
}

.terminal-area {
  flex: 1;
  overflow: hidden;
  padding: 8px;
}
</style>

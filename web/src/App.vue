<template>
  <div class="app-layout">
    <Sidebar
      :skills="skills"
      :recent-files="recentFiles"
      :is-executing="isExecuting"
      @execute="executeFromSidebar"
    />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from './stores/app'
import Sidebar from './components/Sidebar.vue'

const store = useAppStore()
const router = useRouter()

const skills = computed(() => store.skills)
const recentFiles = computed(() => store.recentFiles)
const isExecuting = computed(() => store.isExecuting)

onMounted(() => {
  store.loadSkills()
  store.loadRecentFiles()
})

function executeFromSidebar(command: string) {
  // Navigate to home first if not there
  if (router.currentRoute.value.name !== 'home') {
    router.push('/')
  }
  // Execute command
  store.executeCommand(command)
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
  overflow: hidden;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background: #1e1e1e;
  color: #d4d4d4;
}

.app-layout {
  display: flex;
  height: 100%;
  width: 100%;
}

.main-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>

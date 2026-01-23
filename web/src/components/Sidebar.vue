<template>
  <aside class="sidebar">
    <div class="logo">
      <h1>AI Advisor</h1>
    </div>

    <nav class="nav">
      <router-link to="/" class="nav-item" active-class="active">
        <span class="icon">⌘</span>
        终端
      </router-link>
      <router-link to="/files" class="nav-item" active-class="active">
        <span class="icon">📄</span>
        报告
      </router-link>
      <router-link to="/settings" class="nav-item" active-class="active">
        <span class="icon">⚙</span>
        设置
      </router-link>
    </nav>

    <div class="section">
      <h3>快捷命令</h3>
      <div class="skill-list">
        <button
          v-for="skill in skills"
          :key="skill.name"
          class="skill-btn"
          @click="$emit('execute', skill.command)"
        >
          <span class="skill-name">{{ skill.command }}</span>
          <span class="skill-desc">{{ skill.description }}</span>
        </button>
      </div>
    </div>

    <div class="section" v-if="recentFiles.length">
      <h3>最近文件</h3>
      <div class="recent-files">
        <router-link
          v-for="file in recentFiles"
          :key="file.path"
          :to="`/files/${encodeURIComponent(file.path)}`"
          class="file-item"
        >
          <span class="file-type" :class="file.type">{{ getTypeIcon(file.type) }}</span>
          <span class="file-name">{{ file.name }}</span>
        </router-link>
      </div>
    </div>

    <div class="footer">
      <div class="status" :class="{ executing: isExecuting }">
        {{ isExecuting ? '执行中...' : '就绪' }}
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import type { Skill, FileInfo } from '../types'

defineProps<{
  skills: Skill[]
  recentFiles: FileInfo[]
  isExecuting: boolean
}>()

defineEmits<{
  (e: 'execute', command: string): void
}>()

function getTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    brief: '📊',
    analysis: '📈',
    trade: '💰',
    review: '📝',
    committee: '🤝',
  }
  return icons[type] || '📄'
}
</script>

<style scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background: #252526;
  border-right: 1px solid #404040;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.logo {
  padding: 16px;
  border-bottom: 1px solid #404040;
}

.logo h1 {
  margin: 0;
  font-size: 18px;
  color: #ffffff;
  font-weight: 600;
}

.nav {
  padding: 12px 8px;
  border-bottom: 1px solid #404040;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  color: #cccccc;
  text-decoration: none;
  border-radius: 6px;
  margin-bottom: 4px;
  transition: background 0.2s;
}

.nav-item:hover {
  background: #2a2d2e;
}

.nav-item.active {
  background: #37373d;
  color: #ffffff;
}

.nav-item .icon {
  font-size: 16px;
}

.section {
  padding: 12px;
  border-bottom: 1px solid #404040;
  flex-shrink: 0;
}

.section h3 {
  margin: 0 0 10px 0;
  font-size: 12px;
  color: #858585;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.skill-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.skill-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  padding: 8px 10px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  text-align: left;
  transition: background 0.2s;
}

.skill-btn:hover {
  background: #2a2d2e;
}

.skill-name {
  color: #4fc1ff;
  font-family: monospace;
  font-size: 13px;
}

.skill-desc {
  color: #858585;
  font-size: 11px;
  margin-top: 2px;
}

.recent-files {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  color: #cccccc;
  text-decoration: none;
  border-radius: 6px;
  transition: background 0.2s;
}

.file-item:hover {
  background: #2a2d2e;
}

.file-type {
  font-size: 14px;
}

.file-name {
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.footer {
  margin-top: auto;
  padding: 12px 16px;
  border-top: 1px solid #404040;
}

.status {
  font-size: 12px;
  color: #0dbc79;
}

.status.executing {
  color: #e5e510;
}
</style>

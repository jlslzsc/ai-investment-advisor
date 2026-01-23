<template>
  <div class="files-view">
    <header class="page-header">
      <h1>报告列表</h1>
      <div class="filter-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.value"
          class="tab"
          :class="{ active: activeTab === tab.value }"
          @click="activeTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
    </header>

    <div class="file-list">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="files.length === 0" class="empty">暂无文件</div>
      <router-link
        v-else
        v-for="file in files"
        :key="file.path"
        :to="`/files/${encodeURIComponent(file.path)}`"
        class="file-card"
      >
        <div class="file-icon">{{ getTypeIcon(file.type) }}</div>
        <div class="file-info">
          <div class="file-name">{{ file.name }}</div>
          <div class="file-meta">
            <span class="file-type-badge" :class="file.type">{{ getTypeLabel(file.type) }}</span>
            <span class="file-date">{{ formatDate(file.modified_at) }}</span>
          </div>
        </div>
      </router-link>
    </div>

    <div v-if="hasMore" class="load-more">
      <button class="btn" @click="loadMore" :disabled="loading">
        加载更多
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import * as api from '../api'
import type { FileInfo } from '../types'

const tabs = [
  { label: '全部', value: '' },
  { label: '简报', value: 'brief' },
  { label: '分析', value: 'analysis' },
  { label: '扫描', value: 'scan' },
  { label: '交易', value: 'trade' },
  { label: '复盘', value: 'review' },
  { label: '委员会', value: 'committee' },
]

const activeTab = ref('')
const files = ref<FileInfo[]>([])
const loading = ref(false)
const total = ref(0)
const limit = 20
const offset = ref(0)

const hasMore = ref(false)

onMounted(() => {
  loadFiles()
})

watch(activeTab, () => {
  offset.value = 0
  files.value = []
  loadFiles()
})

async function loadFiles() {
  loading.value = true
  try {
    const result = await api.listFiles(activeTab.value || undefined, limit, offset.value)
    files.value = result.files
    total.value = result.total
    hasMore.value = files.value.length < total.value
  } catch (error) {
    console.error('Failed to load files:', error)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  offset.value += limit
  loading.value = true
  try {
    const result = await api.listFiles(activeTab.value || undefined, limit, offset.value)
    files.value = [...files.value, ...result.files]
    hasMore.value = files.value.length < total.value
  } catch (error) {
    console.error('Failed to load more files:', error)
  } finally {
    loading.value = false
  }
}

function getTypeIcon(type: string): string {
  const icons: Record<string, string> = {
    brief: '📊',
    analysis: '📈',
    scan: '🔍',
    trade: '💰',
    review: '📝',
    committee: '🤝',
  }
  return icons[type] || '📄'
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    brief: '简报',
    analysis: '分析',
    scan: '扫描',
    trade: '交易',
    review: '复盘',
    committee: '委员会',
  }
  return labels[type] || type
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
    minute: 'numeric',
  })
}
</script>

<style scoped>
.files-view {
  height: 100%;
  overflow: auto;
  background: #1e1e1e;
}

.page-header {
  padding: 20px 24px;
  border-bottom: 1px solid #404040;
}

.page-header h1 {
  margin: 0 0 16px 0;
  font-size: 24px;
  color: #ffffff;
}

.filter-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tab {
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #404040;
  border-radius: 20px;
  color: #cccccc;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.tab:hover {
  background: #2a2d2e;
}

.tab.active {
  background: #0078d4;
  border-color: #0078d4;
  color: #ffffff;
}

.file-list {
  padding: 24px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.loading,
.empty {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
  color: #858585;
}

.file-card {
  display: flex;
  gap: 16px;
  padding: 16px;
  background: #252526;
  border-radius: 8px;
  text-decoration: none;
  transition: background 0.2s;
}

.file-card:hover {
  background: #2a2d2e;
}

.file-icon {
  font-size: 32px;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  color: #ffffff;
  font-size: 15px;
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-type-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  background: #3c3c3c;
  color: #cccccc;
}

.file-type-badge.brief {
  background: #1e4d3d;
  color: #0dbc79;
}

.file-type-badge.analysis {
  background: #1e3a5f;
  color: #4fc1ff;
}

.file-type-badge.scan {
  background: #3d3d1e;
  color: #e5bc10;
}

.file-type-badge.trade {
  background: #4d3d1e;
  color: #e5e510;
}

.file-type-badge.review {
  background: #3d1e4d;
  color: #bc3fbc;
}

.file-type-badge.committee {
  background: #1e4d4d;
  color: #11a8cd;
}

.file-date {
  color: #858585;
  font-size: 12px;
}

.load-more {
  display: flex;
  justify-content: center;
  padding: 24px;
}

.btn {
  padding: 10px 24px;
  background: #3c3c3c;
  border: none;
  border-radius: 6px;
  color: #ffffff;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn:hover:not(:disabled) {
  background: #4a4a4a;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

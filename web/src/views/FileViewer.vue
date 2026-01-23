<template>
  <div class="file-viewer">
    <header class="page-header">
      <router-link to="/files" class="back-btn">← 返回</router-link>
      <div class="file-title">
        <span class="file-icon">{{ getTypeIcon(fileData?.type) }}</span>
        <h1>{{ fileData?.name || '加载中...' }}</h1>
      </div>
      <div class="file-meta" v-if="fileData">
        <span class="file-type-badge" :class="fileData.type">{{ getTypeLabel(fileData.type) }}</span>
        <span class="file-date">更新于 {{ fileData.updated_at }}</span>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="content-wrapper">
      <div class="markdown-content" v-html="renderedContent"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { marked } from 'marked'
import * as api from '../api'

const route = useRoute()

interface FileData {
  name: string
  content: string
  type: string
  updated_at: string
}

const fileData = ref<FileData | null>(null)
const loading = ref(true)
const error = ref('')

const renderedContent = computed(() => {
  if (!fileData.value?.content) return ''
  return marked(fileData.value.content)
})

onMounted(() => {
  loadFile()
})

watch(() => route.params.path, () => {
  loadFile()
})

async function loadFile() {
  const path = route.params.path as string
  if (!path) {
    error.value = '文件路径无效'
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''

  try {
    const data = await api.getFileContent(decodeURIComponent(path))
    fileData.value = {
      name: data.name || path.split('/').pop() || '',
      content: data.content,
      type: data.type,
      updated_at: data.updated_at,
    }
  } catch (err) {
    error.value = '加载文件失败: ' + String(err)
  } finally {
    loading.value = false
  }
}

function getTypeIcon(type?: string): string {
  const icons: Record<string, string> = {
    brief: '📊',
    analysis: '📈',
    trade: '💰',
    review: '📝',
    committee: '🤝',
  }
  return icons[type || ''] || '📄'
}

function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    brief: '简报',
    analysis: '分析',
    trade: '交易',
    review: '复盘',
    committee: '委员会',
  }
  return labels[type] || type
}
</script>

<style scoped>
.file-viewer {
  height: 100%;
  overflow: auto;
  background: #1e1e1e;
}

.page-header {
  padding: 20px 24px;
  border-bottom: 1px solid #404040;
}

.back-btn {
  display: inline-block;
  margin-bottom: 12px;
  color: #4fc1ff;
  text-decoration: none;
  font-size: 14px;
}

.back-btn:hover {
  text-decoration: underline;
}

.file-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 28px;
}

.file-title h1 {
  margin: 0;
  font-size: 22px;
  color: #ffffff;
}

.file-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
}

.file-type-badge {
  padding: 4px 10px;
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
  font-size: 13px;
}

.loading,
.error {
  padding: 40px;
  text-align: center;
  color: #858585;
}

.error {
  color: #cd3131;
}

.content-wrapper {
  padding: 24px;
  max-width: 900px;
}

.markdown-content {
  color: #d4d4d4;
  font-size: 15px;
  line-height: 1.7;
}

.markdown-content :deep(h1),
.markdown-content :deep(h2),
.markdown-content :deep(h3) {
  color: #ffffff;
  margin-top: 1.5em;
  margin-bottom: 0.5em;
}

.markdown-content :deep(h1) {
  font-size: 1.8em;
  border-bottom: 1px solid #404040;
  padding-bottom: 0.3em;
}

.markdown-content :deep(h2) {
  font-size: 1.4em;
}

.markdown-content :deep(h3) {
  font-size: 1.2em;
}

.markdown-content :deep(p) {
  margin: 1em 0;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 1em 0;
  padding-left: 2em;
}

.markdown-content :deep(li) {
  margin: 0.5em 0;
}

.markdown-content :deep(code) {
  background: #2d2d2d;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

.markdown-content :deep(pre) {
  background: #2d2d2d;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: transparent;
  padding: 0;
}

.markdown-content :deep(blockquote) {
  border-left: 4px solid #404040;
  margin: 1em 0;
  padding-left: 1em;
  color: #858585;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  border: 1px solid #404040;
  padding: 8px 12px;
  text-align: left;
}

.markdown-content :deep(th) {
  background: #2d2d2d;
}

.markdown-content :deep(a) {
  color: #4fc1ff;
  text-decoration: none;
}

.markdown-content :deep(a:hover) {
  text-decoration: underline;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid #404040;
  margin: 2em 0;
}
</style>

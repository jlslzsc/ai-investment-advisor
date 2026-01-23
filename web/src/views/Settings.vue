<template>
  <div class="settings">
    <header class="page-header">
      <h1>设置</h1>
    </header>

    <div class="settings-content">
      <!-- API Keys Section -->
      <section class="settings-section">
        <h2>API 密钥配置</h2>
        <p class="section-desc">配置数据获取所需的 API 密钥</p>

        <div class="form-group">
          <label>Tushare Token</label>
          <div class="input-with-toggle">
            <input
              :type="showTushareToken ? 'text' : 'password'"
              v-model="apiKeys.tushare_token_full"
              placeholder="输入 Tushare Token"
            />
            <button class="toggle-btn" @click="showTushareToken = !showTushareToken">
              {{ showTushareToken ? '🙈' : '👁' }}
            </button>
          </div>
          <span class="hint">用于获取 A 股市场数据</span>
        </div>

        <div class="form-group">
          <label>FMP API Key</label>
          <div class="input-with-toggle">
            <input
              :type="showFmpKey ? 'text' : 'password'"
              v-model="apiKeys.fmp_api_key_full"
              placeholder="输入 FMP API Key"
            />
            <button class="toggle-btn" @click="showFmpKey = !showFmpKey">
              {{ showFmpKey ? '🙈' : '👁' }}
            </button>
          </div>
          <span class="hint">用于获取美股市场数据</span>
        </div>

        <div class="form-row">
          <div class="form-group small">
            <label>请求超时（秒）</label>
            <input type="number" v-model.number="apiKeys.request_timeout" min="1" max="60" />
          </div>
          <div class="form-group small">
            <label>最大重试次数</label>
            <input type="number" v-model.number="apiKeys.max_retries" min="0" max="10" />
          </div>
          <div class="form-group small">
            <label>重试延迟（秒）</label>
            <input type="number" v-model.number="apiKeys.retry_delay" min="0" max="10" />
          </div>
        </div>

        <div class="actions">
          <button class="btn primary" @click="saveApiKeys" :disabled="saving">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <span v-if="saveMessage" class="save-message" :class="{ error: saveError }">
            {{ saveMessage }}
          </span>
        </div>
      </section>

      <!-- Notion Sync Section -->
      <section class="settings-section">
        <h2>Notion 同步</h2>
        <p class="section-desc">将报告同步到 Notion 页面</p>

        <div class="form-group">
          <label>Notion API Key</label>
          <div class="input-with-toggle">
            <input
              :type="showNotionKey ? 'text' : 'password'"
              v-model="notionConfig.api_key"
              placeholder="输入 Notion Integration Token"
            />
            <button class="toggle-btn" @click="showNotionKey = !showNotionKey">
              {{ showNotionKey ? '🙈' : '👁' }}
            </button>
          </div>
          <span class="hint">在 <a href="https://www.notion.so/my-integrations" target="_blank">Notion Integrations</a> 创建</span>
        </div>

        <div class="form-group">
          <label>Notion Page ID</label>
          <input
            type="text"
            v-model="notionConfig.page_id"
            placeholder="输入目标页面 ID（32位）"
          />
          <span class="hint">从 Notion 页面 URL 中获取，如 notion.so/xxx-<b>2f14745dd11880c5a5dcc781a5f39d76</b></span>
        </div>

        <div class="actions" style="margin-bottom: 20px;">
          <button class="btn primary" @click="saveNotionConfig" :disabled="savingNotion">
            {{ savingNotion ? '保存中...' : '保存 Notion 配置' }}
          </button>
          <button class="btn" @click="testNotionConnection" :disabled="testingNotion">
            {{ testingNotion ? '测试中...' : '测试连接' }}
          </button>
        </div>

        <div class="notion-status">
          <span class="status-label">连接状态：</span>
          <span class="status-value" :class="{ connected: notionStatus.connected }">
            {{ notionStatus.connected ? '已连接' : '未连接' }}
          </span>
          <span v-if="notionStatus.page_title" class="repo-name">
            {{ notionStatus.page_title }}
          </span>
        </div>

        <div v-if="notionConfigMessage" class="save-message" :class="{ error: notionConfigError }" style="margin-bottom: 16px;">
          {{ notionConfigMessage }}
        </div>

        <div class="sync-options">
          <label class="checkbox-item">
            <input type="checkbox" v-model="notionSyncOptions.include_config" />
            <span>配置文件 (Config)</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="notionSyncOptions.include_daily" />
            <span>每日简报 (Daily)</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="notionSyncOptions.include_brief" />
            <span>持仓分析 (Brief)</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="notionSyncOptions.include_analysis" />
            <span>个股分析 (Analysis)</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="notionSyncOptions.include_scan" />
            <span>市场扫描 (Scan)</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="notionSyncOptions.include_records" />
            <span>交易记录 (Records)</span>
          </label>
          <label class="checkbox-item">
            <input type="checkbox" v-model="notionSyncOptions.include_committee" />
            <span>投委会 (Committee)</span>
          </label>
        </div>

        <div class="actions">
          <button class="btn primary" @click="syncAllToNotion" :disabled="notionSyncing">
            {{ notionSyncing ? '同步中...' : '同步到 Notion' }}
          </button>
          <span v-if="notionSyncMessage" class="save-message" :class="{ error: notionSyncError }">
            {{ notionSyncMessage }}
          </span>
        </div>
      </section>

      <!-- Yuque Sync Section (deprecated) -->
<!--      <section class="settings-section">-->
<!--        <h2>语雀同步</h2>-->
<!--        <p class="section-desc">将报告同步到语雀知识库</p>-->

<!--        <div class="yuque-status">-->
<!--          <span class="status-label">连接状态：</span>-->
<!--          <span class="status-value" :class="{ connected: yuqueStatus.connected }">-->
<!--            {{ yuqueStatus.connected ? '已连接' : '未连接' }}-->
<!--          </span>-->
<!--          <span v-if="yuqueStatus.repo_name" class="repo-name">-->
<!--            {{ yuqueStatus.repo_name }}-->
<!--          </span>-->
<!--        </div>-->

<!--        <div class="actions">-->
<!--          <button class="btn" @click="syncAllToYuque" :disabled="syncing">-->
<!--            {{ syncing ? '同步中...' : '同步所有报告' }}-->
<!--          </button>-->
<!--          <span v-if="syncMessage" class="save-message" :class="{ error: syncError }">-->
<!--            {{ syncMessage }}-->
<!--          </span>-->
<!--        </div>-->
<!--      </section>-->

      <!-- Config Files Section -->
      <section class="settings-section">
        <h2>配置文件</h2>
        <p class="section-desc">管理持仓、关注列表等配置</p>

        <div class="config-list">
          <div
            v-for="config in configs"
            :key="config.name"
            class="config-item"
            @click="openConfig(config.name)"
          >
            <span class="config-name">{{ config.name }}.md</span>
            <span class="config-status" :class="{ exists: config.exists }">
              {{ config.exists ? '已配置' : '未配置' }}
            </span>
          </div>
        </div>
      </section>
    </div>

    <!-- Config Editor Modal -->
    <div v-if="editingConfig" class="modal-overlay" @click.self="editingConfig = null">
      <div class="modal">
        <header class="modal-header">
          <h3>编辑 {{ editingConfig.name }}.md</h3>
          <button class="close-btn" @click="editingConfig = null">×</button>
        </header>
        <div class="modal-body">
          <textarea
            v-model="editingConfig.content"
            class="config-editor"
            placeholder="配置内容..."
          ></textarea>
        </div>
        <footer class="modal-footer">
          <button class="btn" @click="editingConfig = null">取消</button>
          <button class="btn primary" @click="saveConfig">保存</button>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import * as api from '../api'
import type { ApiKeyConfig } from '../types'

// Notion sync state
const notionStatus = reactive({
  connected: false,
  page_title: '',
  integration_name: '',
})
const notionConfig = reactive({
  api_key: '',
  page_id: '',
})
const showNotionKey = ref(false)
const savingNotion = ref(false)
const testingNotion = ref(false)
const notionConfigMessage = ref('')
const notionConfigError = ref(false)
const notionSyncing = ref(false)
const notionSyncMessage = ref('')
const notionSyncError = ref(false)
const notionSyncOptions = reactive({
  include_config: true,
  include_daily: true,
  include_brief: true,
  include_analysis: true,
  include_scan: true,
  include_records: true,
  include_committee: true,
})

const apiKeys = reactive<ApiKeyConfig>({
  tushare_token: '',
  tushare_token_full: '',
  fmp_api_key: '',
  fmp_api_key_full: '',
  request_timeout: 10,
  max_retries: 3,
  retry_delay: 1,
})

const showTushareToken = ref(false)
const showFmpKey = ref(false)
const saving = ref(false)
const saveMessage = ref('')
const saveError = ref(false)

const configs = ref<{ name: string; exists: boolean }[]>([])
const editingConfig = ref<{ name: string; content: string } | null>(null)

onMounted(async () => {
  await loadApiKeys()
  await loadNotionConfig()
  await loadNotionStatus()
  await loadConfigs()
})

async function loadApiKeys() {
  try {
    const data = await api.getApiKeys()
    Object.assign(apiKeys, data)
  } catch (error) {
    console.error('Failed to load API keys:', error)
  }
}

async function saveApiKeys() {
  saving.value = true
  saveMessage.value = ''
  saveError.value = false

  try {
    await api.updateApiKeys({
      tushare_token: apiKeys.tushare_token_full,
      fmp_api_key: apiKeys.fmp_api_key_full,
      request_timeout: apiKeys.request_timeout,
      max_retries: apiKeys.max_retries,
      retry_delay: apiKeys.retry_delay,
    })
    saveMessage.value = '保存成功'
  } catch (error) {
    saveError.value = true
    saveMessage.value = '保存失败: ' + String(error)
  } finally {
    saving.value = false
  }
}

async function loadNotionStatus() {
  try {
    const data = await api.getNotionStatus()
    notionStatus.connected = data.connected
    notionStatus.page_title = data.page_title || ''
    notionStatus.integration_name = data.integration_name || ''
  } catch (error) {
    console.error('Failed to load Notion status:', error)
  }
}

async function loadNotionConfig() {
  try {
    const data = await api.getNotionConfig()
    notionConfig.api_key = data.api_key || ''
    notionConfig.page_id = data.page_id || ''
  } catch (error) {
    console.error('Failed to load Notion config:', error)
  }
}

async function saveNotionConfig() {
  savingNotion.value = true
  notionConfigMessage.value = ''
  notionConfigError.value = false

  try {
    await api.updateNotionConfig({
      api_key: notionConfig.api_key,
      page_id: notionConfig.page_id,
    })
    notionConfigMessage.value = '配置已保存'
    // 重新加载状态
    await loadNotionStatus()
  } catch (error) {
    notionConfigError.value = true
    notionConfigMessage.value = '保存失败: ' + String(error)
  } finally {
    savingNotion.value = false
  }
}

async function testNotionConnection() {
  testingNotion.value = true
  notionConfigMessage.value = ''
  notionConfigError.value = false

  try {
    const result = await api.testNotionConnection()
    if (result.connected) {
      notionConfigMessage.value = `连接成功: ${result.page_title}`
      notionStatus.connected = true
      notionStatus.page_title = result.page_title
    } else {
      notionConfigError.value = true
      notionConfigMessage.value = '连接失败: ' + (result.message || '未知错误')
    }
  } catch (error) {
    notionConfigError.value = true
    notionConfigMessage.value = '测试失败: ' + String(error)
  } finally {
    testingNotion.value = false
  }
}

async function syncAllToNotion() {
  notionSyncing.value = true
  notionSyncMessage.value = ''
  notionSyncError.value = false

  try {
    const result = await api.syncAllToNotion(notionSyncOptions)
    notionSyncMessage.value = `同步完成: ${result.total_synced} 成功, ${result.total_failed} 失败`
    if (result.total_failed > 0) {
      notionSyncError.value = true
    }
  } catch (error) {
    notionSyncError.value = true
    notionSyncMessage.value = '同步失败: ' + String(error)
  } finally {
    notionSyncing.value = false
  }
}

async function loadConfigs() {
  try {
    configs.value = await api.listConfigs()
  } catch (error) {
    console.error('Failed to load configs:', error)
  }
}

async function openConfig(name: string) {
  try {
    const config = await api.getConfig(name)
    editingConfig.value = {
      name: config.name,
      content: config.content,
    }
  } catch (error) {
    console.error('Failed to load config:', error)
  }
}

async function saveConfig() {
  if (!editingConfig.value) return

  try {
    await api.updateConfig(editingConfig.value.name, editingConfig.value.content)
    editingConfig.value = null
    await loadConfigs()
  } catch (error) {
    console.error('Failed to save config:', error)
  }
}
</script>

<style scoped>
.settings {
  height: 100%;
  overflow: auto;
  background: #1e1e1e;
}

.page-header {
  padding: 20px 24px;
  border-bottom: 1px solid #404040;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #ffffff;
}

.settings-content {
  padding: 24px;
  max-width: 800px;
}

.settings-section {
  background: #252526;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
}

.settings-section h2 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #ffffff;
}

.section-desc {
  margin: 0 0 20px 0;
  color: #858585;
  font-size: 14px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  color: #cccccc;
  font-size: 14px;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  background: #1e1e1e;
  border: 1px solid #404040;
  border-radius: 6px;
  color: #d4d4d4;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group textarea:focus {
  border-color: #0078d4;
}

.form-group .hint {
  display: block;
  margin-top: 4px;
  color: #6a6a6a;
  font-size: 12px;
}

.input-with-toggle {
  position: relative;
  display: flex;
  align-items: center;
}

.input-with-toggle input {
  padding-right: 40px;
}

.toggle-btn {
  position: absolute;
  right: 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 4px;
}

.form-row {
  display: flex;
  gap: 16px;
}

.form-group.small {
  flex: 1;
}

.form-group.small input {
  width: 100%;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.btn {
  padding: 10px 20px;
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

.btn.primary {
  background: #0078d4;
}

.btn.primary:hover:not(:disabled) {
  background: #106ebe;
}

.save-message {
  font-size: 14px;
  color: #0dbc79;
}

.save-message.error {
  color: #cd3131;
}

.yuque-status,
.notion-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #1e1e1e;
  border-radius: 6px;
  margin-bottom: 16px;
}

.sync-options {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
  margin-bottom: 16px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #1e1e1e;
  border-radius: 6px;
  cursor: pointer;
  color: #cccccc;
  font-size: 14px;
}

.checkbox-item:hover {
  background: #2a2d2e;
}

.checkbox-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.status-label {
  color: #858585;
}

.status-value {
  color: #cd3131;
}

.status-value.connected {
  color: #0dbc79;
}

.repo-name {
  color: #4fc1ff;
  margin-left: auto;
}

.config-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #1e1e1e;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.config-item:hover {
  background: #2a2d2e;
}

.config-name {
  color: #4fc1ff;
  font-family: monospace;
}

.config-status {
  font-size: 12px;
  color: #858585;
}

.config-status.exists {
  color: #0dbc79;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  background: #252526;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #404040;
}

.modal-header h3 {
  margin: 0;
  color: #ffffff;
}

.close-btn {
  background: transparent;
  border: none;
  color: #858585;
  font-size: 24px;
  cursor: pointer;
}

.close-btn:hover {
  color: #ffffff;
}

.modal-body {
  flex: 1;
  padding: 20px;
  overflow: auto;
}

.config-editor {
  width: 100%;
  height: 400px;
  font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
  resize: vertical;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #404040;
}
</style>

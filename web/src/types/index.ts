// Types for the AI Investment Advisor frontend

export interface Skill {
  name: string
  command: string
  description: string
  triggers: string[]
  example: string
}

export interface TerminalEvent {
  type: 'text' | 'tool_start' | 'tool_result' | 'done' | 'error' | 'system' | 'raw' | 'final' | string
  content?: string
  tool?: string
  input?: Record<string, unknown>
  result?: string
  status?: string
  exit_code?: number
  message?: string
  subtype?: string
}

export interface FileInfo {
  path: string
  name: string
  type: string
  size: number
  created_at: string
  modified_at: string
}

export interface HoldingItem {
  code: string
  name: string
  shares?: number
  cost?: number
}

export interface Holdings {
  a_stock: HoldingItem[]
  funds: HoldingItem[]
  us_stock: HoldingItem[]
  hk_stock: HoldingItem[]
  updated_at: string
}

export interface ApiKeyConfig {
  tushare_token: string
  tushare_token_full: string
  fmp_api_key: string
  fmp_api_key_full: string
  request_timeout: number
  max_retries: number
  retry_delay: number
}

export interface ConfigFile {
  name: string
  content: string
  updated_at: string
}

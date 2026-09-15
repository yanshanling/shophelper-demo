export interface KbCategory {
  id: number
  name: string
  name_en: string
  description: string
  icon: string
  sort_order: number
  enabled: boolean
  item_count: number
  updated_at?: string
}

export interface KbItem {
  id: number
  category_id: number
  category_name: string
  title_zh: string
  title_en: string
  answer_zh: string
  answer_en: string
  keywords_zh: string
  keywords_en: string
  status: string
  hit_count: number
  updated_at?: string
}

export interface SearchTestResult {
  query: string
  language: string
  matched_count: number
  best: null | {
    item_id: number
    title: string
    category_name: string
    score: number
    hit_keywords: string[]
    answer: string
  }
  results: {
    item_id: number
    title: string
    category_name: string
    score: number
    hit_keywords: string[]
    answer: string
  }[]
}

export interface PromptTemplate {
  id: number
  name: string
  scene: string
  content: string
  variables: string
  version: number
  is_default: boolean
  enabled: boolean
  note: string
  updated_at?: string
}

export interface PromptVersion {
  id: number
  prompt_id: number
  version: number
  content: string
  note: string
  operator: string
  created_at?: string
}

export interface ModelConfig {
  id: number
  name: string
  provider: string
  base_url: string
  api_key: string
  model_name: string
  temperature: number
  max_tokens: number
  top_p: number
  route_lang: string
  is_default: boolean
  enabled: boolean
  remark: string
  last_test_status: string
  last_test_at?: string
  updated_at?: string
}

export interface TraceStep {
  step: string
  detail: string
  icon: string
}

export interface ChatResult {
  reply: string
  language: string
  intent: string
  intent_name: string
  confidence: number
  safety: { level: string; action: string; auto_reply: string | null }
  matched_item_id: number | null
  source: string
  trace: TraceStep[]
}

export interface DashboardStats {
  kb: { total: number; published: number; draft: number; categories: number; total_hits: number }
  prompts: { total: number; enabled: number }
  models: { total: number; enabled: number }
  chats: { total: number; pending_review: number }
  intent_distribution: { name: string; value: number }[]
  language_distribution: { name: string; value: number }[]
  safety_distribution: { name: string; value: number }[]
  category_distribution: { name: string; value: number }[]
  top_items: { id: number; title: string; category: string; hit_count: number }[]
  recent_changes: {
    id: number
    entity_type: string
    entity_id: number
    entity_name: string
    action: string
    operator: string
    created_at?: string
  }[]
}

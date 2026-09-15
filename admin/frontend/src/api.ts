import axios from 'axios'
import type {
  ChatResult,
  DashboardStats,
  KbCategory,
  KbItem,
  ModelConfig,
  PromptTemplate,
  PromptVersion,
  SearchTestResult,
} from './types'

export const http = axios.create({ baseURL: '/', timeout: 20000 })

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err?.response?.data?.detail
    err.message = typeof detail === 'string' ? detail : err.message || '请求失败'
    return Promise.reject(err)
  },
)

/* ── 概览 ── */
export const getDashboard = () => http.get<DashboardStats>('/api/dashboard/stats').then((r) => r.data)

/* ── 知识库 ── */
export const listCategories = () => http.get<KbCategory[]>('/api/kb/categories').then((r) => r.data)
export const createCategory = (data: Partial<KbCategory>) =>
  http.post<KbCategory>('/api/kb/categories', data).then((r) => r.data)
export const updateCategory = (id: number, data: Partial<KbCategory>) =>
  http.put<KbCategory>(`/api/kb/categories/${id}`, data).then((r) => r.data)
export const deleteCategory = (id: number) => http.delete(`/api/kb/categories/${id}`).then((r) => r.data)

export const listItems = (params: {
  category_id?: number
  keyword?: string
  status?: string
  page?: number
  page_size?: number
}) =>
  http
    .get<{ total: number; page: number; page_size: number; items: KbItem[] }>('/api/kb/items', { params })
    .then((r) => r.data)
export const createItem = (data: Partial<KbItem>) =>
  http.post<KbItem>('/api/kb/items', data).then((r) => r.data)
export const updateItem = (id: number, data: Partial<KbItem>) =>
  http.put<KbItem>(`/api/kb/items/${id}`, data).then((r) => r.data)
export const deleteItem = (id: number) => http.delete(`/api/kb/items/${id}`).then((r) => r.data)
export const searchTest = (query: string, lang = 'auto') =>
  http.post<SearchTestResult>('/api/kb/search-test', { query, lang }).then((r) => r.data)

/* ── Prompt ── */
export const listPrompts = () => http.get<PromptTemplate[]>('/api/prompts').then((r) => r.data)
export const createPrompt = (data: Partial<PromptTemplate>) =>
  http.post<PromptTemplate>('/api/prompts', data).then((r) => r.data)
export const updatePrompt = (id: number, data: Partial<PromptTemplate>) =>
  http.put<PromptTemplate>(`/api/prompts/${id}`, data).then((r) => r.data)
export const deletePrompt = (id: number) => http.delete(`/api/prompts/${id}`).then((r) => r.data)
export const listPromptVersions = (id: number) =>
  http.get<PromptVersion[]>(`/api/prompts/${id}/versions`).then((r) => r.data)
export const rollbackPrompt = (id: number, versionId: number) =>
  http.post<PromptTemplate>(`/api/prompts/${id}/rollback/${versionId}`).then((r) => r.data)
export const setDefaultPrompt = (id: number) =>
  http.post<PromptTemplate>(`/api/prompts/${id}/set-default`).then((r) => r.data)
export const renderPrompt = (id: number, variables: Record<string, string>) =>
  http.post<{ rendered: string }>(`/api/prompts/${id}/render`, { variables }).then((r) => r.data)

/* ── 模型 ── */
export const listModels = () => http.get<ModelConfig[]>('/api/models').then((r) => r.data)
export const createModel = (data: Partial<ModelConfig>) =>
  http.post<ModelConfig>('/api/models', data).then((r) => r.data)
export const updateModel = (id: number, data: Partial<ModelConfig>) =>
  http.put<ModelConfig>(`/api/models/${id}`, data).then((r) => r.data)
export const deleteModel = (id: number) => http.delete(`/api/models/${id}`).then((r) => r.data)
export const setDefaultModel = (id: number) =>
  http.post<ModelConfig>(`/api/models/${id}/set-default`).then((r) => r.data)
export const testModel = (id: number) =>
  http
    .post<{ success: boolean; latency_ms: number; message: string }>(`/api/models/${id}/test`)
    .then((r) => r.data)

/* ── 测试台 ── */
export const getScenarios = () =>
  http.get<{ label: string; text: string; intent: string }[]>('/api/playground/scenarios').then((r) => r.data)
export const chat = (message: string) =>
  http.post<ChatResult>('/api/playground/chat', { message }).then((r) => r.data)

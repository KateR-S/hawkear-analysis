import client from './client'
import type { Touch, Performance, SingleAnalysis, FullAnalysis, BellCharacteristic } from '../types'

export const auth = {
  login: async (username: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const res = await client.post<{ access_token: string; token_type: string }>('/auth/login', form)
    return res.data
  },
  register: async (username: string, email: string, password: string) => {
    const res = await client.post('/auth/register', { username, email, password })
    return res.data
  },
}

export const touches = {
  list: async () => {
    const res = await client.get<Touch[]>('/touches/')
    return res.data
  },
  get: async (id: number) => {
    const res = await client.get<Touch>(`/touches/${id}`)
    return res.data
  },
  create: async (name: string, description: string) => {
    const res = await client.post<Touch>('/touches/', { name, description })
    return res.data
  },
  update: async (id: number, data: { name?: string; description?: string }) => {
    const res = await client.put<Touch>(`/touches/${id}`, data)
    return res.data
  },
  delete: async (id: number) => {
    await client.delete(`/touches/${id}`)
  },
  uploadMethod: async (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await client.post<Touch>(`/touches/${id}/method`, form)
    return res.data
  },
}

export const performances = {
  list: async (touchId: number) => {
    const res = await client.get<Performance[]>(`/touches/${touchId}/performances`)
    return res.data
  },
  create: async (touchId: number, label: string, file: File, orderIndex?: number) => {
    const form = new FormData()
    form.append('label', label)
    form.append('file', file)
    if (orderIndex !== undefined) form.append('order_index', String(orderIndex))
    const res = await client.post<Performance>(`/touches/${touchId}/performances`, form)
    return res.data
  },
  update: async (touchId: number, id: number, data: { label?: string; order_index?: number }) => {
    const res = await client.put<Performance>(`/touches/${touchId}/performances/${id}`, data)
    return res.data
  },
  delete: async (touchId: number, id: number) => {
    await client.delete(`/touches/${touchId}/performances/${id}`)
  },
  reorder: async (touchId: number, items: { id: number; order_index: number }[]) => {
    const res = await client.patch<Performance[]>(`/touches/${touchId}/performances/reorder`, items)
    return res.data
  },
}

export const analysis = {
  getFull: async (touchId: number) => {
    const res = await client.get<FullAnalysis>(`/touches/${touchId}/analysis`)
    return res.data
  },
  getSingle: async (touchId: number, perfId: number) => {
    const res = await client.get<SingleAnalysis>(`/touches/${touchId}/analysis/${perfId}`)
    return res.data
  },
  getRounds: async (touchId: number, perfId: number) => {
    const res = await client.get(`/touches/${touchId}/analysis/${perfId}/rounds`)
    return res.data
  },
  getCharacteristics: async (touchId: number, perfId: number) => {
    const res = await client.get<Record<string, BellCharacteristic>>(`/touches/${touchId}/analysis/${perfId}/characteristics`)
    return res.data
  },
}

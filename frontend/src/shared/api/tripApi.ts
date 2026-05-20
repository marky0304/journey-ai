import type { ClarifyRequest, ClarifyResponse, PlanRequest, SwapRequest, SwapResponse, TaskStatusResponse, Trip, WeatherResponse, LearnListResponse, LearnHistoryListResponse, LearnAnalyzeResult, ChatRequest, ChatResponse, TripSessionGroup, ContextData } from '@/types/api'
import { apiClient } from './client'

export const tripApi = {
  clarifyTrip: (data: ClarifyRequest) =>
    apiClient.post<ClarifyResponse>('/trip/clarify', data).then((r) => r.data),

  createTrip: (data: PlanRequest) =>
    apiClient.post<{ task_id: string }>('/trip/plan', data).then((r) => r.data),

  getPlanningStatus: (taskId: string) =>
    apiClient.get<TaskStatusResponse>(`/trip/planning/${taskId}`).then((r) => r.data),

  getTrip: (tripId: string) =>
    apiClient.get<Trip>(`/trip/${tripId}`).then((r) => r.data),

  getWeather: (tripId: string) =>
    apiClient.get<WeatherResponse>(`/trip/${tripId}/weather`).then((r) => r.data),

  swapActivity: (tripId: string, data: SwapRequest) =>
    apiClient.post<SwapResponse>(`/trip/${tripId}/swap`, data).then((r) => r.data),

  cancelTask: (taskId: string) =>
    apiClient.post<{ success: boolean }>(`/trip/${taskId}/cancel`).then((r) => r.data),

  chat: {
    getContext: (tripId: string) =>
      apiClient.get<ContextData>(`/v1/chat/context?tripId=${tripId}`).then((r) => r.data),

    send: (data: ChatRequest, signal?: AbortSignal) =>
      apiClient.post<ChatResponse>('/v1/chat/send', data, { signal }).then((r) => r.data),

    getHistory: () =>
      apiClient.get<{ groups: TripSessionGroup[] }>('/v1/chat/history').then((r) => r.data),

    getSession: (sessionId: string) =>
      apiClient.get<{ session_id: string; trip_name: string; messages: { role: string; content: string }[] }>(`/v1/chat/session/${sessionId}`).then((r) => r.data),

    restoreSession: (data: { trip_id: string; original_session_id: string }) =>
      apiClient.post<{ new_session_id: string; messages: { role: string; content: string }[] }>('/v1/chat/restore', data).then((r) => r.data),

    deleteSession: (sessionId: string) =>
      apiClient.delete(`/v1/chat/session/${sessionId}`),

    closeSession: (sessionId: string) =>
      apiClient.post('/v1/chat/session/close', { session_id: sessionId }),
  },

  learn: {
    analyze: (url: string) =>
      apiClient.post<LearnAnalyzeResult>('/learn/analyze', { url }).then((r) => r.data),

    listRecent: () =>
      apiClient.get<LearnHistoryListResponse>('/learn/recent').then((r) => r.data),

    listHistory: () =>
      apiClient.get<LearnHistoryListResponse>('/learn/history').then((r) => r.data),

    deleteHistory: (id: string) =>
      apiClient.delete(`/learn/history/${id}`),

    // legacy
    listItems: () =>
      apiClient.get<LearnListResponse>('/learn/items').then((r) => r.data),

    deleteItem: (id: string) =>
      apiClient.delete(`/learn/items/${id}`),
  },
}

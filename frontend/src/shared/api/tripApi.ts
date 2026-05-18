import type { PlanRequest, TaskStatusResponse, Trip } from '@/types/api'
import { apiClient } from './client'

export const tripApi = {
  createTrip: (data: PlanRequest) =>
    apiClient.post<{ task_id: string }>('/trip/plan', data).then((r) => r.data),

  getPlanningStatus: (taskId: string) =>
    apiClient.get<TaskStatusResponse>(`/trip/planning/${taskId}`).then((r) => r.data),

  getTrip: (tripId: string) =>
    apiClient.get<Trip>(`/trip/${tripId}`).then((r) => r.data),

  cancelTask: (taskId: string) =>
    apiClient.post<{ success: boolean }>(`/trip/${taskId}/cancel`).then((r) => r.data),
}

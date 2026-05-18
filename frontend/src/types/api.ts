export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type AgentStatus = 'idle' | 'working' | 'done' | 'error'
export type AgentType = 'coordinator' | 'transport' | 'accommodation' | 'attraction' | 'dining' | 'strategy'

export interface GeoPoint {
  lat: number
  lng: number
}

export interface Activity {
  id: string
  type: 'transport' | 'attraction' | 'dining' | 'hotel'
  name: string
  start_time: string
  end_time: string
  duration: number
  location?: GeoPoint
  description?: string
  tips?: string
  image_url?: string
}

export interface DayPlan {
  day_index: number
  date: string
  activities: Activity[]
}

export interface Trip {
  id: string
  destination: string
  dates: { start: string; end: string }
  budget: { min: number; max: number; currency: string }
  preferences: string[]
  travel_style: string
  days: DayPlan[]
  summary: { total_cost: number; attraction_count: number }
}

export interface AgentInfo {
  name: string
  status: AgentStatus
}

export interface TaskStatusResponse {
  task_id: string
  status: TaskStatus
  progress: number
  agents: AgentInfo[]
  trip_id?: string
  error_message?: string
}

export interface PlanRequest {
  destination: string
  start_date: string
  end_date: string
  budget_min: number
  budget_max: number
  currency: string
  preferences: string[]
  travel_style: string
}

export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'
export type AgentStatus = 'idle' | 'working' | 'done' | 'error'
export type AgentType = 'coordinator' | 'transport' | 'accommodation' | 'attraction' | 'dining' | 'strategy'
export type TravelStyle = 'relaxed' | 'balanced' | 'compact'

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
  travel_style: TravelStyle
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
  start_location: string
  destination: string
  start_date: string
  end_date: string
  budget_min: number
  budget_max: number
  currency: string
  preferences: string[]
  travel_style: TravelStyle
}

export interface SwapRequest {
  day_index: number
  activity_id: string
  type: string
  name: string
  destination: string
  preferences: string[]
  context?: string
}

export interface SwapResponse extends Activity {
  reason: string
}

export interface ClarifyRequest {
  start_location?: string
  destination?: string
  start_date?: string
  end_date?: string
  budget_min?: number
  budget_max?: number
  currency?: string
  preferences?: string[]
  travel_style?: string
  messages: { role: string; content: string }[]
}

export interface ClarifyResponse {
  done: boolean
  message: string
  questions_asked: number
  start_location?: string
  destination?: string
  start_date?: string
  end_date?: string
  budget_min?: number
  budget_max?: number
  currency?: string
  preferences?: string[]
  travel_style?: string
}

export interface WeatherDay {
  date: string
  temp_max: number
  temp_min: number
  text_day: string
  text_night: string
  humidity: number
  wind_dir: string
  wind_scale: string
}

export interface WeatherInfo {
  city: string
  forecast: WeatherDay[]
}

export interface OutfitSuggestion {
  date: string
  suggestion: string
}

export interface WeatherResponse {
  weather: WeatherInfo | null
  outfits: OutfitSuggestion[]
}

export interface KnowledgePoint {
  point: string
  category: string
}

export interface LearnItem {
  id: string
  url: string
  platform: string
  title: string
  summary: string
  knowledge_points: KnowledgePoint[]
  tags: string[]
  location?: string | null
  practical_info?: {
    transport?: string | null
    tickets?: string | null
    hours?: string | null
    tips?: string | null
  } | null
  quality_score: number
  status: string
  created_at: string
  merged_at?: string | null
}

export interface LearnListResponse {
  items: LearnItem[]
  total: number
}

export interface LearnHistoryItem {
  id: string
  url: string
  platform: string
  title: string
  summary: string
  knowledge_points: KnowledgePoint[]
  tags: string[]
  location?: string | null
  quality_score: number
  learned_at: string
}

export interface LearnHistoryListResponse {
  items: LearnHistoryItem[]
  total: number
}

export interface LearnAnalyzeResult {
  history: LearnHistoryItem
  knowledge_points: KnowledgePoint[]
  summary: string
  practical_info?: {
    transport?: string | null
    tickets?: string | null
    hours?: string | null
    tips?: string | null
  } | null
}

export interface GlobalKnowledgeItem {
  id: string
  title: string
  summary: string
  knowledge_points: KnowledgePoint[]
  tags: string[]
  location?: string | null
  practical_info?: Record<string, unknown> | null
  quality_score: number
  merged_count: number
  updated_at: string
}

export interface GlobalKnowledgeListResponse {
  items: GlobalKnowledgeItem[]
  total: number
}

export interface ChatRequest {
  trip_id: string
  session_id: string
  message: string
}

export interface ChatResponse {
  reply: string
  suggestions: string[]
}

export interface SessionItem {
  session_id: string
  first_message: string
  message_count: number
  started_at: string
  last_active_at: string
}

export interface TripSessionGroup {
  trip_id: string
  trip_name: string
  is_current_trip: boolean
  sessions: SessionItem[]
}

export interface PreferenceItem {
  id: string
  category: string
  content: string
  confidence: number
}

export interface ContextData {
  trip_meta: Record<string, unknown> | null
  suggested_questions: string[]
}

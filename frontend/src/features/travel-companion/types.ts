import type { TripPhase } from '@/shared/stores/useTripStore'

export interface Outfit {
  hat: string | null
  handheld: string | null
  color: string
}

export type Mood = 'idle' | 'happy' | 'thinking' | 'excited'

export interface BubbleMessage {
  id: string
  text: string
  mood: Mood
}

export interface Position {
  x: number
  y: number
}

export type AnimationState = 'idle' | 'walking' | 'jumping' | 'sitting'

export type PageContext = 'home' | 'plan' | 'planning' | 'trip' | 'settings' | 'unknown'

export type ExpressionName =
  | 'Idle'
  | 'Sullen'
  | 'Speechless'
  | 'Amaze'
  | 'Doubt'
  | 'Sunglasses'
  | 'Bag'
  | 'Loading'
  | 'StarEye'
  | 'HighlightOff'
  | 'RunningOff'
  | 'TongueOut'

export interface CompanionContent {
  phrases: string[]
  expression: ExpressionName
  clickTips: string[]
}

export type PhaseContentMap = Record<TripPhase, CompanionContent>

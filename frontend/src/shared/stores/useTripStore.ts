import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Trip, TaskStatus, AgentInfo } from '@/types/api'

export type TripPhase = 'no_plan' | 'planning' | 'plan_generated' | 'trip_active'

interface PlanningState {
  taskId: string | null
  status: TaskStatus
  progress: number
  agents: AgentInfo[]
  errorMessage?: string
}

const INITIAL_PLANNING: PlanningState = {
  taskId: null,
  status: 'pending',
  progress: 0,
  agents: [],
}

interface TripStore {
  currentTaskId: string | null
  currentTrip: Trip | null
  tripActive: boolean
  planning: PlanningState
  setTaskId: (id: string) => void
  setTrip: (trip: Trip) => void
  setTripActive: () => void
  resetTripActive: () => void
  reset: () => void
  startPlanning: (taskId: string) => void
  updatePlanningProgress: (status: TaskStatus, progress: number, agents: AgentInfo[], errorMessage?: string) => void
  clearPlanning: () => void
}

export function getPhase(trip: Trip | null, tripActive: boolean, planningTaskId: string | null): TripPhase {
  if (tripActive && trip) return 'trip_active'
  if (trip && !tripActive) return 'plan_generated'
  if (planningTaskId && !trip) return 'planning'
  return 'no_plan'
}

export const useTripStore = create<TripStore>()(
  persist(
    (set) => ({
      currentTaskId: null,
      currentTrip: null,
      tripActive: false,
      planning: INITIAL_PLANNING,
      setTaskId: (id) => set({ currentTaskId: id }),
      setTrip: (trip) => set({ currentTrip: trip }),
      setTripActive: () => set({ tripActive: true }),
      resetTripActive: () => set({ tripActive: false }),
      reset: () => set({ currentTaskId: null, currentTrip: null, tripActive: false, planning: INITIAL_PLANNING }),
      startPlanning: (taskId) =>
        set({ planning: { taskId, status: 'pending', progress: 0, agents: [] } }),
      updatePlanningProgress: (status, progress, agents, errorMessage) =>
        set((state) => ({
          planning: { ...state.planning, status, progress, agents, errorMessage },
        })),
      clearPlanning: () => set({ planning: INITIAL_PLANNING }),
    }),
    { name: 'trip-store' }
  )
)

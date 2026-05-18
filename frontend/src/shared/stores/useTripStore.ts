import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Trip } from '@/types/api'

interface TripStore {
  currentTaskId: string | null
  currentTrip: Trip | null
  setTaskId: (id: string) => void
  setTrip: (trip: Trip) => void
  reset: () => void
}

export const useTripStore = create<TripStore>()(
  persist(
    (set) => ({
      currentTaskId: null,
      currentTrip: null,
      setTaskId: (id) => set({ currentTaskId: id }),
      setTrip: (trip) => set({ currentTrip: trip }),
      reset: () => set({ currentTaskId: null, currentTrip: null }),
    }),
    { name: 'trip-store' }
  )
)

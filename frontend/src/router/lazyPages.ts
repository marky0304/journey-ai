import { lazy } from 'react'

export const HomePage = lazy(() => import('@/features/home/HomePage'))
export const PlanInputPage = lazy(() => import('@/features/plan-input/PlanInputPage'))
export const PlanningPage = lazy(() => import('@/features/planning/PlanningPage'))
export const TripResultPage = lazy(() => import('@/features/trip-result/TripResultPage'))
export const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
export const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

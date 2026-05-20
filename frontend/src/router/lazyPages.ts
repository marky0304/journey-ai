import { lazy } from 'react'

export const HomePage = lazy(() => import('@/features/home/HomePage'))
export const PlanInputPage = lazy(() => import('@/features/plan-input/PlanInputPage'))
export const PlanningPage = lazy(() => import('@/features/planning/PlanningPage'))
export const TripResultPage = lazy(() => import('@/features/trip-result/TripResultPage'))
export const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
export const InspirePage = lazy(() => import('@/features/inspire/InspirePage'))
export const LoginPage = lazy(() => import('@/features/auth/LoginPage'))
export const KnowledgePage = lazy(() => import('@/features/knowledge/KnowledgePage'))
export const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

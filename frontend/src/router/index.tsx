import { Suspense } from 'react'
import {
  createBrowserRouter,
  RouterProvider as ReactRouterProvider,
} from 'react-router-dom'

import { AppLayout } from '@/shared/components/layout/AppLayout'
import { LoadingPage } from '@/shared/components/ui/LoadingPage'
import { ProtectedRoute } from './guards'

import { ROUTES } from './routes'
import {
  HomePage,
  PlanInputPage,
  PlanningPage,
  TripResultPage,
  SettingsPage,
  InspirePage,
  LoginPage,
  KnowledgePage,
  NotFoundPage,
} from './lazyPages'

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.home, element: <HomePage /> },
      {
        path: ROUTES.plan,
        element: <ProtectedRoute><PlanInputPage /></ProtectedRoute>,
      },
      {
        path: ROUTES.planning,
        element: <ProtectedRoute><PlanningPage /></ProtectedRoute>,
      },
      {
        path: ROUTES.trip,
        element: <ProtectedRoute><TripResultPage /></ProtectedRoute>,
      },
      {
        path: ROUTES.settings,
        element: <ProtectedRoute><SettingsPage /></ProtectedRoute>,
      },
      {
        path: ROUTES.inspire,
        element: <ProtectedRoute><InspirePage /></ProtectedRoute>,
      },
      {
        path: ROUTES.knowledge,
        element: <ProtectedRoute><KnowledgePage /></ProtectedRoute>,
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
  {
    path: ROUTES.login,
    element: <LoginPage />,
  },
])

export function RouterProvider() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <ReactRouterProvider router={router} />
    </Suspense>
  )
}

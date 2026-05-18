import { Suspense } from 'react'
import {
  createBrowserRouter,
  RouterProvider as ReactRouterProvider,
} from 'react-router-dom'

import { AppLayout } from '@/shared/components/layout/AppLayout'
import { LoadingPage } from '@/shared/components/ui/LoadingPage'

import { ROUTES } from './routes'
import {
  HomePage,
  PlanInputPage,
  PlanningPage,
  TripResultPage,
  SettingsPage,
  NotFoundPage,
} from './lazyPages'

const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: ROUTES.home, element: <HomePage /> },
      { path: ROUTES.plan, element: <PlanInputPage /> },
      { path: ROUTES.planning, element: <PlanningPage /> },
      { path: ROUTES.trip, element: <TripResultPage /> },
      { path: ROUTES.settings, element: <SettingsPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

export function RouterProvider() {
  return (
    <Suspense fallback={<LoadingPage />}>
      <ReactRouterProvider router={router} />
    </Suspense>
  )
}

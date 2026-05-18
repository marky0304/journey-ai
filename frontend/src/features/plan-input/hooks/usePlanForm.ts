import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { tripApi } from '@/shared/api/tripApi'
import { useTripStore } from '@/shared/stores/useTripStore'
import type { PlanRequest } from '@/types/api'

const INITIAL: PlanRequest = {
  destination: '',
  start_date: '',
  end_date: '',
  budget_min: 0,
  budget_max: 50000,
  currency: 'CNY',
  preferences: [],
  travel_style: 'balanced',
}

export function usePlanForm() {
  const [form, setForm] = useState<PlanRequest>(INITIAL)
  const navigate = useNavigate()
  const setTaskId = useTripStore((s) => s.setTaskId)

  const mutation = useMutation({
    mutationFn: tripApi.createTrip,
    onSuccess: (data) => {
      setTaskId(data.task_id)
      navigate(`/planning/${data.task_id}`)
    },
    onError: () => toast.error('创建规划失败，请重试'),
  })

  return {
    form,
    setForm,
    submit: () => mutation.mutate(form),
    isLoading: mutation.isPending,
  }
}

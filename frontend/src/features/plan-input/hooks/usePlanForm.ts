import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { tripApi } from '@/shared/api/tripApi'
import { useTripStore } from '@/shared/stores/useTripStore'
import type { PlanRequest } from '@/types/api'

const INITIAL: PlanRequest = {
  start_location: '',
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
  const startPlanning = useTripStore((s) => s.startPlanning)

  const createMutation = useMutation({
    mutationFn: tripApi.createTrip,
    onSuccess: (data) => {
      setTaskId(data.task_id)
      startPlanning(data.task_id)
      navigate(`/planning/${data.task_id}`)
    },
    onError: () => toast.error('创建规划失败，请重试'),
  })

  const doCreateTrip = useCallback(
    (plan: PlanRequest) => {
      createMutation.mutate(plan)
    },
    [createMutation.mutate],
  )

  const submit = useCallback(async () => {
    if (!form.start_location || !form.start_location.trim()) {
      toast.error('请输入你的出发城市')
      return
    }
    if (!/^[一-龥a-zA-Z]{2,20}$/.test(form.start_location.trim())) {
      toast.error('出发城市格式不正确，请输入中文或英文城市名')
      return
    }
    if (!form.destination || !form.start_date || !form.end_date) {
      toast.error('请填写目的地和日期')
      return
    }
    doCreateTrip(form)
  }, [form, doCreateTrip])

  return {
    form,
    setForm,
    submit,
    isLoading: createMutation.isPending,
    clarifyOpen: false,
    clarifyQuestion: '',
    clarifyLoading: false,
    onClarifyAnswer: () => {},
    onClarifySkip: () => {},
  }
}

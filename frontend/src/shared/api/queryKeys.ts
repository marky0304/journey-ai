export const queryKeys = {
  planningTask: (taskId: string) => ['planningTask', taskId] as const,
  tripResult: (tripId: string) => ['tripResult', tripId] as const,
}

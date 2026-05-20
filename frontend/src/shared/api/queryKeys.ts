export const queryKeys = {
  planningTask: (taskId: string) => ['planningTask', taskId] as const,
  tripResult: (tripId: string) => ['tripResult', tripId] as const,
  tripWeather: (tripId: string) => ['tripWeather', tripId] as const,
  learnItems: ['learnItems'] as const,
  learnHistory: ['learnHistory'] as const,
  learnRecent: ['learnRecent'] as const,
  chatContext: (tripId: string) => ['chatContext', tripId] as const,
  chatHistory: ['chatHistory'] as const,
  chatSession: (sessionId: string) => ['chatSession', sessionId] as const,
}

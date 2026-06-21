const API_BASE = 'http://127.0.0.1:8790'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `HTTP ${response.status}`)
  }

  return response.json()
}

export const api = {
  getSettingsDiagnostics: () => request('/settings/diagnostics'),
  getLlmSettings: () => request('/llm/settings'),
  getLlmHealth: () => request('/llm/health'),
  listCollectors: () => request('/collectors'),
  collectSignals: (payload) => request('/signals/collect', { method: 'POST', body: JSON.stringify(payload) }),
  getSchedulerStatus: () => request('/scheduler/status'),
  listSchedulerJobs: () => request('/scheduler/jobs'),
  updateSchedulerJob: (id, payload) => request(`/scheduler/jobs/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  runSchedulerJob: (id) => request(`/scheduler/jobs/${id}/run`, { method: 'POST' }),
  listSchedulerRuns: (limit = 30) => request(`/scheduler/runs?limit=${encodeURIComponent(limit)}`),
  listSignals: () => request('/signals'),
  createSignal: (payload) => request('/signals', { method: 'POST', body: JSON.stringify(payload) }),
  listIdeas: (status = '') => request(status ? `/ideas?status=${encodeURIComponent(status)}` : '/ideas'),
  createIdea: (payload) => request('/ideas', { method: 'POST', body: JSON.stringify(payload) }),
  generateIdeas: (payload) => request('/ideas/generate', { method: 'POST', body: JSON.stringify(payload) }),
  updateIdea: (id, payload) => request(`/ideas/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  listReviews: (ideaId) => request(`/ideas/${ideaId}/reviews`),
  runAntiRationalReview: (ideaId) => request(`/ideas/${ideaId}/anti-rational-review`, { method: 'POST' }),
  refreshScores: (ideaId) => request(`/ideas/${ideaId}/refresh-scores`, { method: 'POST' }),
  getRenameSuggestions: (ideaId) => request(`/ideas/${ideaId}/rename-suggestions`),
  getCommercialSmell: (ideaId) => request(`/ideas/${ideaId}/commercial-smell`),
  listExperiments: (ideaId) => request(`/ideas/${ideaId}/experiments`),
  getMvpDraft: (ideaId) => request(`/ideas/${ideaId}/mvp-draft`),
  exportTaskPackage: (ideaId) => request(`/ideas/${ideaId}/export-task-package`, { method: 'POST' }),
  listExports: (ideaId) => request(`/ideas/${ideaId}/exports`),
  getSimilarIdeas: (ideaId) => request(`/ideas/${ideaId}/similar`),
  listIdeaFamilies: () => request('/idea-families'),
  listReviveSuggestions: () => request('/graveyard/revive-suggestions'),
  listIdeaEvents: (ideaId) => request(`/ideas/${ideaId}/events`),
  createIdeaEvent: (payload) => request('/idea-events', { method: 'POST', body: JSON.stringify(payload) }),
  mergeIdeas: (payload) => request('/ideas/merge', { method: 'POST', body: JSON.stringify(payload) }),
  createPrototypeWorkspace: (ideaId, payload) => request(`/ideas/${ideaId}/prototype-workspace`, { method: 'POST', body: JSON.stringify(payload) }),
  listPrototypeWorkspaces: (ideaId) => request(`/ideas/${ideaId}/prototype-workspaces`),
  createPrototypeRun: (payload) => request('/prototype-runs', { method: 'POST', body: JSON.stringify(payload) }),
  listPrototypeRuns: (ideaId) => request(`/ideas/${ideaId}/prototype-runs`),
  updatePrototypeRun: (runId, payload) => request(`/prototype-runs/${runId}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  createRepoExperiment: (ideaId, payload) => request(`/ideas/${ideaId}/repo-experiments`, { method: 'POST', body: JSON.stringify(payload) }),
  listRepoExperiments: (ideaId) => request(`/ideas/${ideaId}/repo-experiments`),
  getRepoExperiment: (experimentId) => request(`/repo-experiments/${experimentId}`),
  getTasteProfile: () => request('/taste/profile'),
  createTasteFeedback: (payload) => request('/taste/feedback', { method: 'POST', body: JSON.stringify(payload) }),
  getTasteFit: (ideaId) => request(`/ideas/${ideaId}/taste-fit`),
  applyTasteScore: (ideaId) => request(`/ideas/${ideaId}/apply-taste-score`, { method: 'POST' }),
  listTasteRecommendations: (limit = 10) => request(`/taste/recommendations?limit=${encodeURIComponent(limit)}`),
}





<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from './api'

const tabs = ['today', 'collectors', 'signals', 'generator', 'ideas', 'reviews', 'export', 'prototype', 'repoexp', 'evolution', 'taste', 'graveyard']
const activeTab = ref('today')
const signals = ref([])
const collectors = ref([])
const collectedSignals = ref([])
const ideas = ref([])
const selectedIdea = ref(null)
const generatedIdeas = ref([])
const selectedReviews = ref([])
const renameSuggestions = ref([])
const commercialSmell = ref(null)
const reviewing = ref(false)
const exporting = ref(false)
const mvpDraft = ref(null)
const selectedExports = ref([])
const similarItems = ref([])
const ideaFamilies = ref([])
const reviveSuggestions = ref([])
const ideaEvents = ref([])
const merging = ref(false)
const creatingWorkspace = ref(false)
const creatingRun = ref(false)
const prototypeWorkspaces = ref([])
const prototypeRuns = ref([])
const repoExperiments = ref([])
const creatingRepoExperiment = ref(false)
const tasteProfile = ref(null)
const tasteRecommendations = ref([])
const selectedTasteFit = ref(null)
const tasteFeedbackNote = ref('')
const error = ref('')
const loading = ref(false)
const generating = ref(false)
const collecting = ref(false)
const statusFilter = ref('all')

const BOARD_STATUSES = [
  { key: 'new', label: '新生' },
  { key: 'saved', label: '收藏' },
  { key: 'deep_dive', label: '深入研究' },
  { key: 'mvp_draft', label: 'MVP 草案' },
  { key: 'prototype_ready', label: '可進 Prototype' },
  { key: 'prototype', label: 'Prototype 中' },
]

const DEAD_STATUSES = ['dead', 'rejected']

const STATUS_LABELS = {
  new: '新生',
  saved: '收藏',
  rejected: '淘汰',
  deep_dive: '深入研究',
  mvp_draft: 'MVP 草案',
  prototype_ready: '可進 Prototype',
  prototype: 'Prototype 中',
  dead: '墳場',
  revive_candidate: '復活候選',
  merged: '已合併',
}

const signalForm = ref({
  title: '',
  source_type: 'manual',
  source_url: '',
  summary: '',
  raw_text: '',
  tags_text: '',
  weirdness: 5,
  pain_signal: 5,
})

const collectorForm = ref({
  query: 'AI developer tools agent repo setup build test',
  sources: ['github', 'hacker_news', 'arxiv'],
  limit_per_source: 5,
  save: true,
})

const generationForm = ref({
  raw_text: `GitHub Next Discovery Agent：自動在容器裡 setup/build/test GitHub repositories。\nOpenHands：開源 AI coding agent，可以在 sandbox 裡操作 repo。\nRailpack：自動偵測 repo 技術棧並 build container。\n我不想做普通 SaaS，希望題目要怪、有畫面感、可以一週 prototype。`,
  selected_signal_ids: [],
  count: 10,
  save: true,
})

const ideaForm = ref({
  name: '',
  one_liner: '',
  weird_angle: '',
  real_pain: '',
  first_screen: '',
  mvp: '',
  source_signal_ids_text: '',
})

const graveyardForm = ref({
  rejection_reason: '',
  revival_condition: '',
  status_note: '',
})

const eventForm = ref({
  event_type: 'note',
  title: '',
  note: '',
})

const workspaceForm = ref({
  worker: 'manual',
  title: '',
  notes: '',
  overwrite: false,
})

const repoExperimentForm = ref({
  repo_url: 'https://github.com/SWE-agent/mini-swe-agent',
  title: 'Repo Setup/Build/Test Probe',
  run_mode: 'inspect_only',
  timeout_seconds: 180,
  notes: '',
})

const runForm = ref({
  workspace_id: '',
  title: 'Prototype Run',
  worker: 'manual',
  status: 'planned',
  goal: '',
  summary: '',
  changed_files_text: '',
  test_commands_text: '',
  result: '',
  next_step: '',
})

const statusCounts = computed(() => {
  const counts = {}
  for (const idea of ideas.value) counts[idea.status] = (counts[idea.status] || 0) + 1
  return counts
})

const activeIdeas = computed(() => ideas.value.filter((idea) => !DEAD_STATUSES.includes(idea.status)))
const graveyardIdeas = computed(() => ideas.value.filter((idea) => DEAD_STATUSES.includes(idea.status)))
const reviveIdeas = computed(() => ideas.value.filter((idea) => idea.status === 'revive_candidate'))

const ideaGroups = computed(() => {
  const groups = Object.fromEntries(BOARD_STATUSES.map((status) => [status.key, []]))
  for (const idea of activeIdeas.value) {
    if (groups[idea.status]) groups[idea.status].push(idea)
    else groups.new.push(idea)
  }
  return groups
})

const filteredIdeas = computed(() => {
  if (statusFilter.value === 'all') return activeIdeas.value
  return activeIdeas.value.filter((idea) => idea.status === statusFilter.value)
})

const topIdeas = computed(() => ideas.value.slice(0, 5))
const recentSignals = computed(() => signals.value.slice(0, 5))

const favoriteGenerated = computed(() => {
  return generatedIdeas.value
    .slice()
    .sort((a, b) => scoreTotal(b) - scoreTotal(a))
    .slice(0, 3)
})

function tabLabel(tab) {
  if (tab === 'today') return 'Today'
  if (tab === 'collectors') return '自動素材'
  if (tab === 'signals') return 'Signal Inbox'
  if (tab === 'generator') return '怪題產生器'
  if (tab === 'reviews') return '反合理審查'
  if (tab === 'export') return 'MVP 輸出'
  if (tab === 'prototype') return 'Prototype'
  if (tab === 'repoexp') return 'Repo 實驗'
  if (tab === 'evolution') return '題目演化'
  if (tab === 'taste') return '個人品味'
  if (tab === 'graveyard') return '墳場'
  return 'Idea Board'
}

function statusLabel(status) {
  return STATUS_LABELS[status] || status
}

function scoreTotal(idea) {
  const scores = idea?.scores || {}
  return Object.values(scores).reduce((sum, value) => sum + Number(value || 0), 0)
}

const SCORE_LABELS = {
  surprise: '驚喜',
  weirdness: '怪味',
  memorability: '記憶',
  visual_imagination: '畫面',
  real_pain: '痛點',
  mvp_feasibility: '可做',
  differentiation: '差異',
  personal_fit: '適配',
  anti_saas: '反SaaS',
  revival_potential: '復活',
}

function scoreText(idea) {
  const scores = idea?.scores || {}
  const keys = ['surprise', 'weirdness', 'memorability', 'real_pain', 'mvp_feasibility', 'anti_saas']
  return keys
    .filter((key) => scores[key])
    .map((key) => `${SCORE_LABELS[key]} ${scores[key]}`)
    .join(' / ')
}

function scoreEntries(idea) {
  const scores = idea?.scores || {}
  return Object.entries(SCORE_LABELS).map(([key, label]) => ({ key, label, value: Number(scores[key] || 0) }))
}

function flagLabel(flag) {
  const labels = {
    too_saas: '太像 SaaS',
    dashboard_smell: '太像 dashboard / 控制台',
    platform_smell: '太像 platform / marketplace',
    workflow_smell: '太像 workflow / automation',
    generic_ai_tool: '太像 AI assistant / copilot',
    productivity_smell: '太像生產力 / 團隊協作工具',
    name_too_plain: '名字太普通',
    missing_weird_angle: '缺少怪味描述',
    missing_real_pain: '缺少真痛點',
    missing_mvp: '缺少 MVP',
  }
  return labels[flag] || flag
}

function formatDate(value) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleString()
  } catch {
    return value
  }
}

async function refreshAll() {
  loading.value = true
  error.value = ''
  try {
    const [collectorItems, signalItems, ideaItems] = await Promise.all([api.listCollectors(), api.listSignals(), api.listIdeas()])
    collectors.value = collectorItems
    signals.value = signalItems
    ideas.value = ideaItems
    if (selectedIdea.value) {
      selectedIdea.value = ideaItems.find((item) => item.id === selectedIdea.value.id) || null
      syncGraveyardForm(selectedIdea.value)
      if (selectedIdea.value) await loadPrototypeMeta(selectedIdea.value)
    }
    await loadEvolutionDashboard(false)
    await loadTasteDashboard(false)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}


async function runCollectors() {
  error.value = ''
  collecting.value = true
  try {
    const response = await api.collectSignals({
      query: collectorForm.value.query,
      sources: collectorForm.value.sources,
      limit_per_source: Number(collectorForm.value.limit_per_source),
      save: collectorForm.value.save,
    })
    collectedSignals.value = response.signals || []
    if (response.errors?.length) {
      error.value = response.errors.map((item) => `${item.source}: ${item.error}`).join(' / ')
    }
    await refreshAll()
    activeTab.value = 'collectors'
  } catch (err) {
    error.value = err.message
  } finally {
    collecting.value = false
  }
}

async function submitSignal() {
  error.value = ''
  try {
    const tags = signalForm.value.tags_text
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean)
    await api.createSignal({
      title: signalForm.value.title,
      source_type: signalForm.value.source_type,
      source_url: signalForm.value.source_url || null,
      summary: signalForm.value.summary,
      raw_text: signalForm.value.raw_text,
      tags,
      weirdness: Number(signalForm.value.weirdness),
      pain_signal: Number(signalForm.value.pain_signal),
    })
    signalForm.value = {
      title: '',
      source_type: 'manual',
      source_url: '',
      summary: '',
      raw_text: '',
      tags_text: '',
      weirdness: 5,
      pain_signal: 5,
    }
    await refreshAll()
  } catch (err) {
    error.value = err.message
  }
}

async function generateIdeas() {
  error.value = ''
  generating.value = true
  try {
    const response = await api.generateIdeas({
      raw_text: generationForm.value.raw_text,
      signal_ids: generationForm.value.selected_signal_ids,
      count: Number(generationForm.value.count),
      save: generationForm.value.save,
    })
    generatedIdeas.value = response.ideas
    await refreshAll()
    activeTab.value = 'generator'
  } catch (err) {
    error.value = err.message
  } finally {
    generating.value = false
  }
}

async function saveGeneratedIdea(idea) {
  error.value = ''
  try {
    const saved = await api.createIdea({
      name: idea.name,
      one_liner: idea.one_liner,
      weird_angle: idea.weird_angle,
      real_pain: idea.real_pain,
      first_screen: idea.first_screen,
      mvp: idea.mvp,
      status: idea.status || 'new',
      source_signal_ids: idea.source_signal_ids || [],
      scores: idea.scores || {},
    })
    selectedIdea.value = saved
    syncGraveyardForm(saved)
    await refreshAll()
  } catch (err) {
    error.value = err.message
  }
}

async function submitIdea() {
  error.value = ''
  try {
    const sourceSignalIds = ideaForm.value.source_signal_ids_text
      .split(',')
      .map((id) => id.trim())
      .filter(Boolean)
    const idea = await api.createIdea({
      name: ideaForm.value.name,
      one_liner: ideaForm.value.one_liner,
      weird_angle: ideaForm.value.weird_angle,
      real_pain: ideaForm.value.real_pain,
      first_screen: ideaForm.value.first_screen,
      mvp: ideaForm.value.mvp,
      source_signal_ids: sourceSignalIds,
      scores: {},
    })
    ideaForm.value = {
      name: '',
      one_liner: '',
      weird_angle: '',
      real_pain: '',
      first_screen: '',
      mvp: '',
      source_signal_ids_text: '',
    }
    selectedIdea.value = idea
    syncGraveyardForm(idea)
    activeTab.value = 'ideas'
    await refreshAll()
  } catch (err) {
    error.value = err.message
  }
}

async function setIdeaStatus(idea, status, extra = {}) {
  error.value = ''
  try {
    const updated = await api.updateIdea(idea.id, { status, ...extra })
    selectedIdea.value = updated
    syncGraveyardForm(updated)
    await refreshAll()
  } catch (err) {
    error.value = err.message
  }
}

function selectIdea(idea) {
  selectedIdea.value = idea
  syncGraveyardForm(idea)
  loadIdeaMeta(idea)
}

async function loadIdeaMeta(idea) {
  if (!idea?.id) return
  try {
    const [reviews, smell, exports, similar, events, workspaces, runs, repoRuns, tasteFit] = await Promise.all([
      api.listReviews(idea.id),
      api.getCommercialSmell(idea.id),
      api.listExports(idea.id),
      api.getSimilarIdeas(idea.id),
      api.listIdeaEvents(idea.id),
      api.listPrototypeWorkspaces(idea.id),
      api.listPrototypeRuns(idea.id),
      api.listRepoExperiments(idea.id),
      api.getTasteFit(idea.id),
    ])
    selectedReviews.value = reviews
    commercialSmell.value = smell
    selectedExports.value = exports
    similarItems.value = similar.items || []
    ideaEvents.value = events || []
    prototypeWorkspaces.value = workspaces || []
    prototypeRuns.value = runs || []
    repoExperiments.value = repoRuns || []
    selectedTasteFit.value = tasteFit || null
  } catch (err) {
    selectedReviews.value = []
    selectedExports.value = []
    similarItems.value = []
    ideaEvents.value = []
    commercialSmell.value = null
    prototypeWorkspaces.value = []
    prototypeRuns.value = []
    repoExperiments.value = []
    selectedTasteFit.value = null
  }
}

async function runReview() {
  if (!selectedIdea.value) return
  error.value = ''
  reviewing.value = true
  try {
    const response = await api.runAntiRationalReview(selectedIdea.value.id)
    selectedIdea.value = response.idea
    selectedReviews.value = [response.review, ...selectedReviews.value]
    renameSuggestions.value = response.suggestions || []
    commercialSmell.value = { idea_id: selectedIdea.value.id, flags: response.flags || [], labels: (response.flags || []).map(flagLabel), severity: Math.min(10, (response.flags || []).length * 2) }
    await refreshAll()
  } catch (err) {
    error.value = err.message
  } finally {
    reviewing.value = false
  }
}

async function refreshIdeaScores() {
  if (!selectedIdea.value) return
  error.value = ''
  try {
    const response = await api.refreshScores(selectedIdea.value.id)
    selectedIdea.value = response.idea
    await refreshAll()
  } catch (err) {
    error.value = err.message
  }
}

async function loadRenameSuggestions() {
  if (!selectedIdea.value) return
  error.value = ''
  try {
    const response = await api.getRenameSuggestions(selectedIdea.value.id)
    renameSuggestions.value = response.suggestions || []
  } catch (err) {
    error.value = err.message
  }
}

async function applyRenameSuggestion(name) {
  if (!selectedIdea.value) return
  const updated = await api.updateIdea(selectedIdea.value.id, { name })
  selectedIdea.value = updated
  await refreshAll()
}

async function loadMvpDraft() {
  if (!selectedIdea.value) return
  error.value = ''
  try {
    mvpDraft.value = await api.getMvpDraft(selectedIdea.value.id)
    activeTab.value = 'export'
  } catch (err) {
    error.value = err.message
  }
}

async function exportTaskPackage() {
  if (!selectedIdea.value) return
  error.value = ''
  exporting.value = true
  try {
    const response = await api.exportTaskPackage(selectedIdea.value.id)
    selectedExports.value = [response.export_record, ...selectedExports.value]
    mvpDraft.value = await api.getMvpDraft(selectedIdea.value.id)
    await refreshAll()
    activeTab.value = 'export'
  } catch (err) {
    error.value = err.message
  } finally {
    exporting.value = false
  }
}

async function loadPrototypeMeta(idea = selectedIdea.value) {
  if (!idea?.id) return
  try {
    const [workspaces, runs] = await Promise.all([
      api.listPrototypeWorkspaces(idea.id),
      api.listPrototypeRuns(idea.id),
      api.listRepoExperiments(idea.id),
      api.getTasteFit(idea.id),
    ])
    prototypeWorkspaces.value = workspaces || []
    prototypeRuns.value = runs || []
    if (!runForm.value.workspace_id && workspaces?.length) runForm.value.workspace_id = workspaces[0].id
  } catch (err) {
    prototypeWorkspaces.value = []
    prototypeRuns.value = []
  }
}

async function createWorkspace() {
  if (!selectedIdea.value) return
  error.value = ''
  creatingWorkspace.value = true
  try {
    const response = await api.createPrototypeWorkspace(selectedIdea.value.id, {
      worker: workspaceForm.value.worker,
      title: workspaceForm.value.title,
      notes: workspaceForm.value.notes,
      overwrite: workspaceForm.value.overwrite,
    })
    selectedIdea.value = response.idea
    prototypeWorkspaces.value = [response.workspace, ...prototypeWorkspaces.value]
    runForm.value.workspace_id = response.workspace.id
    await refreshAll()
    await loadPrototypeMeta(selectedIdea.value)
    activeTab.value = 'prototype'
  } catch (err) {
    error.value = err.message
  } finally {
    creatingWorkspace.value = false
  }
}

async function createPrototypeRun() {
  if (!selectedIdea.value) return
  error.value = ''
  creatingRun.value = true
  try {
    const changedFiles = runForm.value.changed_files_text.split('\n').map((item) => item.trim()).filter(Boolean)
    const testCommands = runForm.value.test_commands_text.split('\n').map((item) => item.trim()).filter(Boolean)
    const response = await api.createPrototypeRun({
      idea_id: selectedIdea.value.id,
      workspace_id: runForm.value.workspace_id || null,
      title: runForm.value.title || 'Prototype Run',
      worker: runForm.value.worker,
      status: runForm.value.status,
      goal: runForm.value.goal,
      summary: runForm.value.summary,
      changed_files: changedFiles,
      test_commands: testCommands,
      result: runForm.value.result,
      next_step: runForm.value.next_step,
    })
    selectedIdea.value = response.idea || selectedIdea.value
    prototypeRuns.value = [response.run, ...prototypeRuns.value]
    runForm.value = {
      workspace_id: runForm.value.workspace_id,
      title: 'Prototype Run',
      worker: runForm.value.worker,
      status: 'planned',
      goal: '',
      summary: '',
      changed_files_text: '',
      test_commands_text: '',
      result: '',
      next_step: '',
    }
    await refreshAll()
    await loadPrototypeMeta(selectedIdea.value)
    activeTab.value = 'prototype'
  } catch (err) {
    error.value = err.message
  } finally {
    creatingRun.value = false
  }
}



async function createRepoExperiment() {
  if (!selectedIdea.value) return
  error.value = ''
  creatingRepoExperiment.value = true
  try {
    const response = await api.createRepoExperiment(selectedIdea.value.id, {
      repo_url: repoExperimentForm.value.repo_url,
      title: repoExperimentForm.value.title || 'Repo Setup/Build/Test Probe',
      run_mode: repoExperimentForm.value.run_mode,
      timeout_seconds: Number(repoExperimentForm.value.timeout_seconds || 180),
      notes: repoExperimentForm.value.notes,
    })
    selectedIdea.value = response.idea || selectedIdea.value
    repoExperiments.value = [response.experiment, ...repoExperiments.value]
    await refreshAll()
    await loadIdeaMeta(selectedIdea.value)
    activeTab.value = 'repoexp'
  } catch (err) {
    error.value = err.message
  } finally {
    creatingRepoExperiment.value = false
  }
}

function syncGraveyardForm(idea) {
  graveyardForm.value = {
    rejection_reason: idea?.rejection_reason || '',
    revival_condition: idea?.revival_condition || '',
    status_note: idea?.status_note || '',
  }
}

async function saveGraveyardNote() {
  if (!selectedIdea.value) return
  await setIdeaStatus(selectedIdea.value, selectedIdea.value.status, {
    rejection_reason: graveyardForm.value.rejection_reason,
    revival_condition: graveyardForm.value.revival_condition,
    status_note: graveyardForm.value.status_note,
  })
}

async function sendToGraveyard(status = 'dead') {
  if (!selectedIdea.value) return
  await setIdeaStatus(selectedIdea.value, status, {
    rejection_reason: graveyardForm.value.rejection_reason || '尚未填寫死因',
    revival_condition: graveyardForm.value.revival_condition,
    status_note: graveyardForm.value.status_note,
  })
  activeTab.value = 'graveyard'
}

async function reviveIdea(idea) {
  await setIdeaStatus(idea, 'revive_candidate', {
    status_note: idea.status_note || '從墳場標記為復活候選。',
  })
  activeTab.value = 'graveyard'
}


async function loadEvolutionDashboard(showTab = true) {
  try {
    const [families, revives] = await Promise.all([
      api.listIdeaFamilies(),
      api.listReviveSuggestions(),
    ])
    ideaFamilies.value = families.families || []
    reviveSuggestions.value = revives.items || []
    if (showTab) activeTab.value = 'evolution'
  } catch (err) {
    // Do not block normal refresh if evolution heuristics fail.
    if (showTab) error.value = err.message
  }
}

async function mergeFamily(family, option = null) {
  error.value = ''
  merging.value = true
  try {
    const response = await api.mergeIdeas({
      idea_ids: family.idea_ids,
      name: option?.name || family.family_name,
      mark_sources_merged: true,
    })
    selectedIdea.value = response.merged_idea
    syncGraveyardForm(response.merged_idea)
    await refreshAll()
    await loadIdeaMeta(response.merged_idea)
    activeTab.value = 'ideas'
  } catch (err) {
    error.value = err.message
  } finally {
    merging.value = false
  }
}

async function createEvent() {
  if (!selectedIdea.value) return
  error.value = ''
  try {
    await api.createIdeaEvent({
      idea_id: selectedIdea.value.id,
      event_type: eventForm.value.event_type,
      title: eventForm.value.title,
      note: eventForm.value.note,
      related_idea_ids: [],
      metadata: {},
    })
    eventForm.value = { event_type: 'note', title: '', note: '' }
    ideaEvents.value = await api.listIdeaEvents(selectedIdea.value.id)
  } catch (err) {
    error.value = err.message
  }
}


async function loadTasteDashboard(showTab = true) {
  try {
    const [profile, recommendations] = await Promise.all([
      api.getTasteProfile(),
      api.listTasteRecommendations(12),
    ])
    tasteProfile.value = profile
    tasteRecommendations.value = recommendations.items || []
    if (showTab) activeTab.value = 'taste'
  } catch (err) {
    if (showTab) error.value = err.message
  }
}

async function loadTasteFit() {
  if (!selectedIdea.value) return
  error.value = ''
  try {
    selectedTasteFit.value = await api.getTasteFit(selectedIdea.value.id)
    activeTab.value = 'taste'
  } catch (err) {
    error.value = err.message
  }
}

async function giveTasteFeedback(action) {
  if (!selectedIdea.value) return
  error.value = ''
  try {
    const response = await api.createTasteFeedback({
      idea_id: selectedIdea.value.id,
      action,
      note: tasteFeedbackNote.value,
    })
    selectedTasteFit.value = response.fit || selectedTasteFit.value
    tasteProfile.value = response.profile || tasteProfile.value
    tasteFeedbackNote.value = ''
    await loadTasteDashboard(false)
  } catch (err) {
    error.value = err.message
  }
}

async function applyTasteScoreToIdea() {
  if (!selectedIdea.value) return
  error.value = ''
  try {
    selectedIdea.value = await api.applyTasteScore(selectedIdea.value.id)
    await refreshAll()
    await loadTasteFit()
  } catch (err) {
    error.value = err.message
  }
}

async function moveBackToBoard(idea, status = 'saved') {
  await setIdeaStatus(idea, status, {
    status_note: idea.status_note || '從墳場移回看板。',
  })
  activeTab.value = 'ideas'
}

onMounted(refreshAll)
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">怪</div>
        <div>
          <h1>怪題研究所</h1>
          <p>Phase 6 題目演化</p>
        </div>
      </div>

      <button
        v-for="tab in tabs"
        :key="tab"
        class="nav-button"
        :class="{ active: activeTab === tab }"
        @click="activeTab = tab"
      >
        {{ tabLabel(tab) }}
      </button>
    </aside>

    <main class="main-panel">
      <div class="topbar">
        <div>
          <h2 v-if="activeTab === 'today'">今日狀態</h2>
          <h2 v-else-if="activeTab === 'collectors'">自動素材收集</h2>
          <h2 v-else-if="activeTab === 'signals'">素材收集箱</h2>
          <h2 v-else-if="activeTab === 'generator'">怪題產生器</h2>
          <h2 v-else-if="activeTab === 'reviews'">反合理審查</h2>
          <h2 v-else-if="activeTab === 'export'">MVP 收斂與任務包輸出</h2>
          <h2 v-else-if="activeTab === 'prototype'">Prototype Workspace 與 Run Ledger</h2>
          <h2 v-else-if="activeTab === 'repoexp'">Repo Setup / Build / Test 實驗</h2>
          <h2 v-else-if="activeTab === 'evolution'">題目演化、合併與復活</h2>
          <h2 v-else-if="activeTab === 'taste'">個人品味學習</h2>
          <h2 v-else-if="activeTab === 'graveyard'">墳場</h2>
          <h2 v-else>題目看板</h2>
          <p>Phase 9：從收藏、淘汰、深挖、Prototype 與明確回饋中學習你的品味，推薦更像你的怪題。</p>
        </div>
        <button class="ghost" @click="refreshAll">重新整理</button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading" class="muted">讀取中...</p>

      <section v-if="activeTab === 'today'" class="grid two">
        <div class="card">
          <h3>統計</h3>
          <div class="stat-row"><span>素材</span><strong>{{ signals.length }}</strong></div>
          <div class="stat-row"><span>全部題目</span><strong>{{ ideas.length }}</strong></div>
          <div class="stat-row"><span>活題目</span><strong>{{ activeIdeas.length }}</strong></div>
          <div class="stat-row"><span>墳場</span><strong>{{ graveyardIdeas.length }}</strong></div>
        </div>

        <div class="card">
          <h3>狀態分布</h3>
          <div class="status-grid">
            <div v-for="(label, status) in STATUS_LABELS" :key="status" class="status-count">
              <span>{{ label }}</span>
              <strong>{{ statusCounts[status] || 0 }}</strong>
            </div>
          </div>
        </div>

        <div class="card wide">
          <h3>最近題目</h3>
          <div v-if="!topIdeas.length" class="empty">尚無題目。</div>
          <button v-for="idea in topIdeas" :key="idea.id" class="list-item" @click="selectIdea(idea); activeTab='ideas'">
            <strong>{{ idea.name }}</strong>
            <span>{{ idea.one_liner || '沒有一句話描述' }}</span>
            <em>{{ statusLabel(idea.status) }}</em>
          </button>
        </div>

        <div class="card wide">
          <h3>最近素材</h3>
          <div v-if="!recentSignals.length" class="empty">尚無素材。</div>
          <div v-for="signal in recentSignals" :key="signal.id" class="signal-line">
            <strong>{{ signal.title }}</strong>
            <span>{{ signal.summary }}</span>
          </div>
        </div>
      </section>


      <section v-if="activeTab === 'collectors'" class="grid two">
        <form class="card form" @submit.prevent="runCollectors">
          <h3>自動收集素材</h3>
          <p class="muted">Phase 5 會從線上來源抓訊號並存進 Signal Inbox。若網路或來源失敗，後端會改用內建 fallback 種子素材，避免流程中斷。</p>
          <label>搜尋主題<textarea v-model="collectorForm.query" rows="3" /></label>

          <div class="signal-picker">
            <h4>來源</h4>
            <label v-for="collector in collectors" :key="collector.key" class="checkbox-line">
              <input type="checkbox" :value="collector.key" v-model="collectorForm.sources" />
              <span><strong>{{ collector.label }}</strong> — {{ collector.description }}</span>
            </label>
          </div>

          <div class="split">
            <label>每個來源最多幾則<input v-model="collectorForm.limit_per_source" type="number" min="1" max="10" /></label>
            <label class="checkbox-inline"><input v-model="collectorForm.save" type="checkbox" />收集後自動存入素材箱</label>
          </div>
          <button type="submit" :disabled="collecting">{{ collecting ? '收集中...' : '收集素材' }}</button>
        </form>

        <div class="card">
          <h3>收集結果</h3>
          <div v-if="!collectedSignals.length" class="empty">尚未執行收集。</div>
          <article v-for="signal in collectedSignals" :key="signal.id || signal.title" class="signal-card">
            <div class="mini-id">{{ signal.id || 'preview' }} · {{ signal.source_type }}</div>
            <strong>{{ signal.title }}</strong>
            <p>{{ signal.summary }}</p>
            <a v-if="signal.source_url" :href="signal.source_url" target="_blank" rel="noreferrer">開啟來源</a>
            <div class="chips"><span v-for="tag in signal.tags" :key="tag">{{ tag }}</span></div>
          </article>
        </div>
      </section>

      <section v-if="activeTab === 'signals'" class="grid two">
        <form class="card form" @submit.prevent="submitSignal">
          <h3>新增素材</h3>
          <label>標題<input v-model="signalForm.title" required /></label>
          <label>來源類型<input v-model="signalForm.source_type" /></label>
          <label>URL<input v-model="signalForm.source_url" /></label>
          <label>摘要<textarea v-model="signalForm.summary" rows="3" /></label>
          <label>原文 / 備註<textarea v-model="signalForm.raw_text" rows="6" /></label>
          <label>標籤，用逗號分隔<input v-model="signalForm.tags_text" /></label>
          <div class="split">
            <label>怪味<input v-model="signalForm.weirdness" type="number" min="1" max="10" /></label>
            <label>痛點<input v-model="signalForm.pain_signal" type="number" min="1" max="10" /></label>
          </div>
          <button type="submit">儲存素材</button>
        </form>

        <div class="card">
          <h3>素材列表</h3>
          <div v-if="!signals.length" class="empty">尚無素材。</div>
          <div v-for="signal in signals" :key="signal.id" class="signal-card">
            <div class="mini-id">{{ signal.id }}</div>
            <strong>{{ signal.title }}</strong>
            <p>{{ signal.summary }}</p>
            <div class="chips"><span v-for="tag in signal.tags" :key="tag">{{ tag }}</span></div>
          </div>
        </div>
      </section>

      <section v-if="activeTab === 'generator'" class="generator-layout">
        <form class="card form" @submit.prevent="generateIdeas">
          <h3>用素材產生怪題</h3>
          <p class="muted">第一版先用內建「反商業化模板」產生題目，不需要 API key。Phase 3 會補上反合理審查與完整分數。</p>
          <label>直接貼素材<textarea v-model="generationForm.raw_text" rows="10" /></label>

          <div class="signal-picker">
            <h4>也可以勾選素材箱裡的素材</h4>
            <div v-if="!signals.length" class="empty">尚無可勾選素材。</div>
            <label v-for="signal in signals" :key="signal.id" class="checkbox-line">
              <input type="checkbox" :value="signal.id" v-model="generationForm.selected_signal_ids" />
              <span>{{ signal.title }}</span>
            </label>
          </div>

          <div class="split">
            <label>產生數量<input v-model="generationForm.count" type="number" min="1" max="10" /></label>
            <label class="checkbox-inline"><input v-model="generationForm.save" type="checkbox" />產生後自動存入題目庫</label>
          </div>
          <button type="submit" :disabled="generating">{{ generating ? '產生中...' : '產生怪題卡' }}</button>
        </form>

        <div class="generated-list">
          <div class="card"><h3>產生結果</h3><div v-if="!generatedIdeas.length" class="empty">尚未產生怪題。</div></div>
          <article v-for="idea in generatedIdeas" :key="idea.id || idea.name" class="idea-result card">
            <div class="idea-result-head">
              <div><div class="mini-id">{{ idea.id || '尚未儲存' }}</div><h3>{{ idea.name }}</h3></div>
              <button v-if="!idea.id" class="ghost small" @click="saveGeneratedIdea(idea)">存入題目庫</button>
              <button v-else class="ghost small" @click="selectIdea(idea); activeTab='ideas'">查看</button>
            </div>
            <p class="one-liner">{{ idea.one_liner }}</p>
            <div class="score-line">{{ scoreText(idea) }}</div>
            <h4>怪在哪裡</h4><p>{{ idea.weird_angle }}</p>
            <h4>背後真痛點</h4><p>{{ idea.real_pain }}</p>
            <h4>第一個畫面</h4><p>{{ idea.first_screen }}</p>
            <h4>MVP 初稿</h4><p>{{ idea.mvp }}</p>
          </article>
        </div>
      </section>

      <section v-if="activeTab === 'ideas'" class="ideas-layout">
        <div class="left-column">
          <form class="card form" @submit.prevent="submitIdea">
            <h3>手動新增怪題</h3>
            <label>名字<input v-model="ideaForm.name" required /></label>
            <label>一句話<input v-model="ideaForm.one_liner" /></label>
            <label>怪在哪裡<textarea v-model="ideaForm.weird_angle" rows="2" /></label>
            <label>背後真痛點<textarea v-model="ideaForm.real_pain" rows="2" /></label>
            <label>第一個畫面<textarea v-model="ideaForm.first_screen" rows="2" /></label>
            <label>MVP 初稿<textarea v-model="ideaForm.mvp" rows="3" /></label>
            <label>來源素材 ID，用逗號分隔<input v-model="ideaForm.source_signal_ids_text" /></label>
            <button type="submit">儲存題目</button>
          </form>

          <div class="card board-toolbar">
            <h3>題目狀態篩選</h3>
            <div class="status-actions">
              <button :class="{ active: statusFilter === 'all' }" @click="statusFilter='all'">全部活題目</button>
              <button v-for="status in BOARD_STATUSES" :key="status.key" :class="{ active: statusFilter === status.key }" @click="statusFilter=status.key">
                {{ status.label }} {{ statusCounts[status.key] || 0 }}
              </button>
            </div>
          </div>

          <div class="board">
            <div v-for="status in BOARD_STATUSES" :key="status.key" class="board-column">
              <h3>{{ status.label }} <span>{{ ideaGroups[status.key]?.length || 0 }}</span></h3>
              <button v-for="idea in ideaGroups[status.key]" :key="idea.id" class="idea-card" @click="selectIdea(idea)">
                <strong>{{ idea.name }}</strong>
                <span>{{ idea.one_liner || '沒有一句話描述' }}</span>
              </button>
            </div>
          </div>

          <div class="card">
            <h3>列表檢視</h3>
            <div v-if="!filteredIdeas.length" class="empty">沒有符合篩選的題目。</div>
            <button v-for="idea in filteredIdeas" :key="idea.id" class="list-item" @click="selectIdea(idea)">
              <strong>{{ idea.name }}</strong>
              <span>{{ idea.one_liner }}</span>
              <em>{{ statusLabel(idea.status) }} · {{ formatDate(idea.updated_at) }}</em>
            </button>
          </div>
        </div>

        <aside class="detail card" v-if="selectedIdea">
          <div class="mini-id">{{ selectedIdea.id }}</div>
          <h3>{{ selectedIdea.name }}</h3>
          <p class="one-liner">{{ selectedIdea.one_liner }}</p>
          <div class="score-line">{{ scoreText(selectedIdea) || '尚無分數' }}</div>
          <div class="status-pill">{{ statusLabel(selectedIdea.status) }}</div>

          <h4>Phase 9 個人品味</h4>
          <div v-if="selectedTasteFit" class="smell-box">
            <strong>適配分：{{ selectedTasteFit.score }}/100</strong>
            <p>{{ selectedTasteFit.verdict }}</p>
            <div v-if="selectedTasteFit.reasons?.length" class="chips"><span v-for="reason in selectedTasteFit.reasons" :key="reason">{{ reason }}</span></div>
            <div v-if="selectedTasteFit.warnings?.length" class="chips danger-chips"><span v-for="warning in selectedTasteFit.warnings" :key="warning">{{ warning }}</span></div>
          </div>
          <div class="status-actions">
            <button @click="loadTasteFit">計算品味適配</button>
            <button @click="giveTasteFeedback('love')">超喜歡</button>
            <button @click="giveTasteFeedback('too_boring')">太無聊</button>
            <button @click="giveTasteFeedback('too_saas')">太 SaaS</button>
            <button @click="applyTasteScoreToIdea">寫入 personal_fit</button>
          </div>
          <input v-model="tasteFeedbackNote" placeholder="可選：補充這張題目為什麼對味 / 不對味" />

          <h4>Phase 3 審查</h4>
          <div class="status-actions">
            <button @click="runReview" :disabled="reviewing">{{ reviewing ? '審查中...' : '跑反合理審查' }}</button>
            <button @click="refreshIdeaScores">重算分數</button>
            <button @click="loadRenameSuggestions">產生改名</button>
            <button class="ghost" @click="activeTab='reviews'">到審查中心</button>
          </div>

          <div v-if="commercialSmell" class="smell-box">
            <strong>商業味嚴重度：{{ commercialSmell.severity }}/10</strong>
            <div v-if="commercialSmell.flags?.length" class="chips danger-chips">
              <span v-for="flag in commercialSmell.flags" :key="flag">{{ flagLabel(flag) }}</span>
            </div>
            <p v-else class="muted">目前沒有明顯普通 SaaS 味。</p>
          </div>

          <div v-if="renameSuggestions.length" class="rename-box">
            <h4>改名建議</h4>
            <button v-for="name in renameSuggestions" :key="name" class="name-chip" @click="applyRenameSuggestion(name)">{{ name }}</button>
          </div>

          <h4>怪在哪裡</h4><p>{{ selectedIdea.weird_angle || '尚未填寫' }}</p>
          <h4>背後真痛點</h4><p>{{ selectedIdea.real_pain || '尚未填寫' }}</p>
          <h4>第一個畫面</h4><p>{{ selectedIdea.first_screen || '尚未填寫' }}</p>
          <h4>MVP 初稿</h4><p>{{ selectedIdea.mvp || '尚未填寫' }}</p>

          <h4>Phase 4 MVP / 任務包</h4>
          <div class="status-actions">
            <button @click="loadMvpDraft">收斂 MVP</button>
            <button @click="exportTaskPackage" :disabled="exporting">{{ exporting ? '輸出中...' : '輸出 Prototype 任務包' }}</button>
            <button class="ghost" @click="activeTab='export'; loadMvpDraft()">到 MVP 輸出</button>
            <button class="ghost" @click="loadEvolutionDashboard(true)">到題目演化</button>
          </div>

          <h4>完整評分</h4>
          <div class="score-grid">
            <div v-for="item in scoreEntries(selectedIdea)" :key="item.key" class="score-cell">
              <span>{{ item.label }}</span>
              <strong>{{ item.value || '-' }}</strong>
            </div>
          </div>

          <h4>最近審查紀錄</h4>
          <div v-if="!selectedReviews.length" class="empty">尚無審查紀錄。</div>
          <article v-for="review in selectedReviews.slice(0, 2)" :key="review.id" class="review-mini">
            <strong>{{ review.passes ? '通過' : '未通過' }} · {{ review.review_type }}</strong>
            <p>{{ review.comment }}</p>
          </article>


          <h4>Phase 6 相似題目</h4>
          <div v-if="!similarItems.length" class="empty">目前沒有明顯相似題目。</div>
          <article v-for="item in similarItems.slice(0, 3)" :key="item.idea.id" class="review-mini">
            <strong>{{ item.idea.name }} · 相似 {{ Math.round(item.score * 100) }}%</strong>
            <p>{{ item.idea.one_liner }}</p>
            <small>{{ item.reasons.join(' / ') }}</small>
            <div class="status-actions"><button @click="selectIdea(item.idea)">查看</button></div>
          </article>

          <h4>演化紀錄</h4>
          <form class="inline-form" @submit.prevent="createEvent">
            <input v-model="eventForm.title" placeholder="事件標題，例如：改名 / 合併 / 復活理由" />
            <textarea v-model="eventForm.note" rows="2" placeholder="紀錄這張題目為什麼變化" />
            <button type="submit">新增紀錄</button>
          </form>
          <div v-if="!ideaEvents.length" class="empty">尚無演化紀錄。</div>
          <article v-for="event in ideaEvents.slice(0, 3)" :key="event.id" class="review-mini">
            <strong>{{ event.title || event.event_type }}</strong>
            <p>{{ event.note }}</p>
            <small>{{ formatDate(event.created_at) }}</small>
          </article>

          <h4>狀態流轉</h4>
          <div class="status-actions">
            <button @click="setIdeaStatus(selectedIdea, 'saved')">收藏</button>
            <button @click="setIdeaStatus(selectedIdea, 'deep_dive')">深入</button>
            <button @click="setIdeaStatus(selectedIdea, 'mvp_draft')">MVP</button>
            <button @click="setIdeaStatus(selectedIdea, 'prototype_ready')">可 Prototype</button>
            <button @click="setIdeaStatus(selectedIdea, 'prototype')">Prototype 中</button>
          </div>

          <h4>淘汰 / 墳場紀錄</h4>
          <label>死因 / 淘汰原因<textarea v-model="graveyardForm.rejection_reason" rows="3" placeholder="例如：太像 SaaS、只是 prompt、沒有真痛點..." /></label>
          <label>復活條件<textarea v-model="graveyardForm.revival_condition" rows="3" placeholder="例如：如果 repo runner 做出來，這個題目可復活..." /></label>
          <label>狀態備註<textarea v-model="graveyardForm.status_note" rows="2" /></label>
          <div class="status-actions danger-zone">
            <button @click="saveGraveyardNote">只儲存備註</button>
            <button @click="sendToGraveyard('rejected')">淘汰</button>
            <button @click="sendToGraveyard('dead')">丟進墳場</button>
          </div>
        </aside>
      </section>

      <section v-if="activeTab === 'reviews'" class="reviews-layout">
        <div class="card">
          <h3>反合理審查中心</h3>
          <p class="muted">Phase 3 的目的不是判斷商業價值，而是殺掉太合理、太像 SaaS、太像 dashboard 的題目。</p>
          <div v-if="!selectedIdea" class="empty">先在 Idea Board 選一張題目。</div>
          <template v-else>
            <div class="mini-id">{{ selectedIdea.id }}</div>
            <h2>{{ selectedIdea.name }}</h2>
            <p class="one-liner">{{ selectedIdea.one_liner }}</p>
            <div class="status-actions">
              <button @click="runReview" :disabled="reviewing">{{ reviewing ? '審查中...' : '跑反合理審查' }}</button>
              <button @click="refreshIdeaScores">重算分數</button>
              <button @click="loadRenameSuggestions">產生改名建議</button>
            </div>
          </template>
        </div>

        <div class="card" v-if="selectedIdea">
          <h3>完整評分</h3>
          <div class="score-grid large">
            <div v-for="item in scoreEntries(selectedIdea)" :key="item.key" class="score-cell">
              <span>{{ item.label }}</span>
              <strong>{{ item.value || '-' }}</strong>
            </div>
          </div>
        </div>

        <div class="card" v-if="selectedIdea">
          <h3>商業味偵測</h3>
          <div v-if="commercialSmell">
            <div class="stat-row"><span>嚴重度</span><strong>{{ commercialSmell.severity }}/10</strong></div>
            <div v-if="commercialSmell.flags?.length" class="chips danger-chips">
              <span v-for="flag in commercialSmell.flags" :key="flag">{{ flagLabel(flag) }}</span>
            </div>
            <p v-else class="muted">沒有明顯商業味。這不代表題目一定好，只代表它沒有落入常見無聊形狀。</p>
          </div>
        </div>

        <div class="card" v-if="selectedIdea">
          <h3>改名建議</h3>
          <p class="muted">當題目太像「AI xxx platform」時，先改成有畫面、有怪味的名字。</p>
          <div v-if="!renameSuggestions.length" class="empty">尚無改名建議。按上方「產生改名建議」。</div>
          <div class="rename-list">
            <button v-for="name in renameSuggestions" :key="name" class="name-chip" @click="applyRenameSuggestion(name)">{{ name }}</button>
          </div>
        </div>

        <div class="card wide" v-if="selectedIdea">
          <h3>審查紀錄</h3>
          <div v-if="!selectedReviews.length" class="empty">尚無審查紀錄。</div>
          <article v-for="review in selectedReviews" :key="review.id" class="review-card">
            <div class="review-head">
              <strong>{{ review.passes ? '通過' : '未通過' }}</strong>
              <span>{{ formatDate(review.created_at) }}</span>
            </div>
            <p>{{ review.comment }}</p>
            <div v-if="review.flags?.length" class="chips danger-chips">
              <span v-for="flag in review.flags" :key="flag">{{ flagLabel(flag) }}</span>
            </div>
            <div v-if="review.suggestions?.length" class="rename-list">
              <button v-for="name in review.suggestions" :key="name" class="name-chip" @click="applyRenameSuggestion(name)">{{ name }}</button>
            </div>
          </article>
        </div>
      </section>



      <section v-if="activeTab === 'export'" class="grid two">
        <div class="card wide">
          <h3>MVP 收斂與任務包輸出</h3>
          <p class="muted">先在 Idea Board 選一張題目，再產生 MVP 草案或輸出任務包。</p>
          <div v-if="!selectedIdea" class="empty">尚未選取題目。</div>
          <template v-else>
            <div class="mini-id">{{ selectedIdea.id }}</div>
            <h2>{{ selectedIdea.name }}</h2>
            <p class="one-liner">{{ selectedIdea.one_liner }}</p>
            <div class="status-actions">
              <button @click="loadMvpDraft">重新收斂 MVP</button>
              <button @click="exportTaskPackage" :disabled="exporting">{{ exporting ? '輸出中...' : '輸出 Prototype 任務包' }}</button>
            </div>
          </template>
        </div>

        <div class="card wide" v-if="mvpDraft">
          <h3>MVP 草案</h3>
          <pre class="markdown-preview">{{ mvpDraft.markdown }}</pre>
        </div>

        <div class="card wide" v-if="selectedIdea">
          <h3>輸出紀錄</h3>
          <div v-if="!selectedExports.length" class="empty">尚無輸出紀錄。</div>
          <article v-for="item in selectedExports" :key="item.id" class="review-card">
            <div class="review-head"><strong>{{ item.export_type }}</strong><span>{{ formatDate(item.created_at) }}</span></div>
            <p>{{ item.path }}</p>
          </article>
        </div>
      </section>



      <section v-if="activeTab === 'prototype'" class="grid two">
        <div class="card wide">
          <h3>Phase 7 Prototype Workspace</h3>
          <p class="muted">這裡把題目卡轉成真正可以交給 Codex / OpenCode / 人類實作的 workspace。它會建立 docs、prompts、runs、logs、src 等資料夾，並把結果回寫到題目生命週期。</p>
          <div v-if="!selectedIdea" class="empty">先在 Idea Board 選一張題目。</div>
          <template v-else>
            <div class="mini-id">{{ selectedIdea.id }}</div>
            <h2>{{ selectedIdea.name }}</h2>
            <p class="one-liner">{{ selectedIdea.one_liner }}</p>
          </template>
        </div>

        <form class="card form" v-if="selectedIdea" @submit.prevent="createWorkspace">
          <h3>建立 Workspace</h3>
          <label>Worker
            <select v-model="workspaceForm.worker">
              <option value="manual">Manual</option>
              <option value="codex">Codex</option>
              <option value="opencode">OpenCode</option>
            </select>
          </label>
          <label>標題<input v-model="workspaceForm.title" placeholder="不填則自動使用題目名稱" /></label>
          <label>備註<textarea v-model="workspaceForm.notes" rows="3" placeholder="這次 prototype 的邊界或注意事項" /></label>
          <label class="checkbox-inline"><input v-model="workspaceForm.overwrite" type="checkbox" />覆寫既有 docs/prompts 檔案</label>
          <button type="submit" :disabled="creatingWorkspace">{{ creatingWorkspace ? '建立中...' : '建立 Prototype Workspace' }}</button>
        </form>

        <div class="card" v-if="selectedIdea">
          <h3>Workspace 列表</h3>
          <div v-if="!prototypeWorkspaces.length" class="empty">尚無 workspace。</div>
          <article v-for="workspace in prototypeWorkspaces" :key="workspace.id" class="review-card">
            <div class="review-head"><strong>{{ workspace.title }}</strong><span>{{ workspace.worker }}</span></div>
            <p>{{ workspace.directory }}</p>
            <small>{{ formatDate(workspace.created_at) }}</small>
            <div class="status-actions">
              <button class="ghost small" @click="runForm.workspace_id = workspace.id">選為 Run 目標</button>
            </div>
          </article>
        </div>

        <form class="card form" v-if="selectedIdea" @submit.prevent="createPrototypeRun">
          <h3>新增 Prototype Run</h3>
          <label>Workspace
            <select v-model="runForm.workspace_id">
              <option value="">不指定 workspace</option>
              <option v-for="workspace in prototypeWorkspaces" :key="workspace.id" :value="workspace.id">{{ workspace.title }} — {{ workspace.worker }}</option>
            </select>
          </label>
          <div class="split">
            <label>Worker
              <select v-model="runForm.worker">
                <option value="manual">Manual</option>
                <option value="codex">Codex</option>
                <option value="opencode">OpenCode</option>
              </select>
            </label>
            <label>狀態
              <select v-model="runForm.status">
                <option value="planned">planned</option>
                <option value="running">running</option>
                <option value="passed">passed</option>
                <option value="failed">failed</option>
                <option value="blocked">blocked</option>
                <option value="needs_rethink">needs_rethink</option>
              </select>
            </label>
          </div>
          <label>標題<input v-model="runForm.title" /></label>
          <label>目標<textarea v-model="runForm.goal" rows="2" /></label>
          <label>摘要<textarea v-model="runForm.summary" rows="3" /></label>
          <label>修改檔案，一行一個<textarea v-model="runForm.changed_files_text" rows="3" /></label>
          <label>測試指令，一行一個<textarea v-model="runForm.test_commands_text" rows="3" /></label>
          <label>結果<textarea v-model="runForm.result" rows="3" /></label>
          <label>下一步<textarea v-model="runForm.next_step" rows="2" /></label>
          <button type="submit" :disabled="creatingRun">{{ creatingRun ? '新增中...' : '新增 Prototype Run' }}</button>
        </form>

        <div class="card wide" v-if="selectedIdea">
          <h3>Prototype Run Ledger</h3>
          <div v-if="!prototypeRuns.length" class="empty">尚無 prototype run。</div>
          <article v-for="run in prototypeRuns" :key="run.id" class="review-card">
            <div class="review-head"><strong>{{ run.title }}</strong><span>{{ run.worker }} / {{ run.status }}</span></div>
            <p>{{ run.summary || run.goal || '尚無摘要' }}</p>
            <div v-if="run.changed_files?.length" class="chips"><span v-for="file in run.changed_files" :key="file">{{ file }}</span></div>
            <small v-if="run.report_path">Run report：{{ run.report_path }}</small>
            <small>{{ formatDate(run.created_at) }}</small>
          </article>
        </div>
      </section>


      <section v-if="activeTab === 'repoexp'" class="grid two">
        <div class="card wide">
          <h3>Phase 8 Repo Setup / Build / Test 實驗</h3>
          <p class="muted">這裡用來驗證題目背後的 repo 假設。第一版預設 inspect_only：clone repo、偵測 Dockerfile / devcontainer / package.json / pyproject / Makefile / GitHub Actions，產生 setup/build/test report。local_execute 會在本機 workspace 執行推斷指令，請只在可拋棄 VM 裡使用。</p>
          <div v-if="!selectedIdea" class="empty">先在 Idea Board 選一張題目。</div>
          <template v-else>
            <div class="mini-id">{{ selectedIdea.id }}</div>
            <h2>{{ selectedIdea.name }}</h2>
            <p class="one-liner">{{ selectedIdea.one_liner }}</p>
          </template>
        </div>

        <form class="card form" v-if="selectedIdea" @submit.prevent="createRepoExperiment">
          <h3>新增 Repo Probe</h3>
          <label>GitHub Repo URL<input v-model="repoExperimentForm.repo_url" placeholder="https://github.com/org/repo" /></label>
          <label>標題<input v-model="repoExperimentForm.title" /></label>
          <div class="split">
            <label>Run Mode
              <select v-model="repoExperimentForm.run_mode">
                <option value="inspect_only">inspect_only：只 clone + 靜態偵測</option>
                <option value="local_dry_run">local_dry_run：列出本機指令但不執行</option>
                <option value="local_execute">local_execute：執行推斷指令，僅限可拋棄 VM</option>
              </select>
            </label>
            <label>Timeout 秒<input v-model="repoExperimentForm.timeout_seconds" type="number" min="30" max="1800" /></label>
          </div>
          <label>備註<textarea v-model="repoExperimentForm.notes" rows="3" placeholder="這次想驗證什麼？例如 README 是否可信、是否能推斷 Node build/test 指令。" /></label>
          <button type="submit" :disabled="creatingRepoExperiment">{{ creatingRepoExperiment ? '執行中...' : '執行 Repo Probe' }}</button>
        </form>

        <div class="card wide" v-if="selectedIdea">
          <h3>Repo 實驗紀錄</h3>
          <div v-if="!repoExperiments.length" class="empty">尚無 repo 實驗。</div>
          <article v-for="exp in repoExperiments" :key="exp.id" class="review-card">
            <div class="review-head"><strong>{{ exp.title }}</strong><span>{{ exp.status }} / {{ exp.run_mode }}</span></div>
            <p><strong>{{ exp.repo_url }}</strong></p>
            <p>{{ exp.summary || '尚無摘要' }}</p>
            <div v-if="exp.detected_stack?.length" class="chips"><span v-for="stack in exp.detected_stack" :key="stack">{{ stack }}</span></div>
            <h4>推斷 setup</h4>
            <ul><li v-for="cmd in exp.setup_commands" :key="cmd"><code>{{ cmd }}</code></li></ul>
            <h4>推斷 build / test</h4>
            <ul>
              <li v-for="cmd in exp.build_commands" :key="cmd"><code>{{ cmd }}</code></li>
              <li v-for="cmd in exp.test_commands" :key="cmd"><code>{{ cmd }}</code></li>
            </ul>
            <h4>風險</h4>
            <ul><li v-for="risk in exp.risks" :key="risk">{{ risk }}</li></ul>
            <small v-if="exp.report_path">Report：{{ exp.report_path }}</small>
            <small>{{ formatDate(exp.created_at) }}</small>
          </article>
        </div>
      </section>

      <section v-if="activeTab === 'evolution'" class="grid two">
        <div class="card wide">
          <h3>Phase 6 題目演化中心</h3>
          <p class="muted">這裡不是產生新點子，而是找出相似題目、合併母題、保存族譜，並從墳場找出可復活的題目。</p>
          <div class="status-actions">
            <button @click="loadEvolutionDashboard(true)">重新分析題目族群</button>
          </div>
        </div>

        <div class="card wide">
          <h3>合併建議</h3>
          <div v-if="!ideaFamilies.length" class="empty">目前沒有足夠相似的題目族群。多產生幾張怪題後再試。</div>
          <article v-for="family in ideaFamilies" :key="family.family_name + family.idea_ids.join('-')" class="family-card">
            <div class="review-head"><strong>{{ family.family_name }}</strong><span>{{ family.idea_ids.length }} 張</span></div>
            <p>{{ family.reason }}</p>
            <div class="chips"><span v-for="kw in family.shared_keywords" :key="kw">{{ kw }}</span></div>
            <h4>來源題目</h4>
            <ul>
              <li v-for="idea in family.ideas" :key="idea.id"><strong>{{ idea.name }}</strong> — {{ idea.one_liner }}</li>
            </ul>
            <h4>可合併成</h4>
            <div class="rename-list">
              <button v-for="option in family.merge_options" :key="option.name" class="name-chip" @click="mergeFamily(family, option)" :disabled="merging">
                {{ option.style }}：{{ option.name }}
              </button>
            </div>
          </article>
        </div>

        <div class="card wide">
          <h3>復活建議</h3>
          <p class="muted">系統會把近期素材與活題目，拿去和墳場題目比對；有重合時就提示復活。</p>
          <div v-if="!reviveSuggestions.length" class="empty">目前沒有復活建議。</div>
          <article v-for="item in reviveSuggestions" :key="item.idea.id" class="grave-card">
            <div class="review-head"><strong>{{ item.idea.name }}</strong><span>復活分 {{ item.score }}/10</span></div>
            <p>{{ item.idea.one_liner }}</p>
            <small v-for="reason in item.reasons" :key="reason">{{ reason }}</small>
            <div class="status-actions">
              <button @click="reviveIdea(item.idea)">標記復活候選</button>
              <button @click="moveBackToBoard(item.idea, 'saved')">直接移回收藏</button>
            </div>
          </article>
        </div>

        <div class="card wide" v-if="selectedIdea">
          <h3>目前選取題目的族譜</h3>
          <div class="mini-id">{{ selectedIdea.id }}</div>
          <h2>{{ selectedIdea.name }}</h2>
          <div v-if="!similarItems.length" class="empty">目前沒有相似題目。</div>
          <article v-for="item in similarItems" :key="item.idea.id" class="review-card">
            <div class="review-head"><strong>{{ item.idea.name }}</strong><span>相似 {{ Math.round(item.score * 100) }}%</span></div>
            <p>{{ item.idea.one_liner }}</p>
            <small>{{ item.reasons.join(' / ') }}</small>
          </article>
          <h4>演化紀錄</h4>
          <div v-if="!ideaEvents.length" class="empty">尚無演化紀錄。</div>
          <article v-for="event in ideaEvents" :key="event.id" class="review-card">
            <div class="review-head"><strong>{{ event.title || event.event_type }}</strong><span>{{ formatDate(event.created_at) }}</span></div>
            <p>{{ event.note }}</p>
          </article>
        </div>
      </section>


      <section v-if="activeTab === 'taste'" class="grid two">
        <div class="card">
          <h3>個人品味輪廓</h3>
          <p class="muted">Phase 9 會從你收藏、深入研究、丟進墳場、Prototype，以及明確回饋中推估你的偏好。這不是固定 persona，而是會隨使用行為更新。</p>
          <button @click="loadTasteDashboard(true)">重新計算品味</button>
          <div v-if="!tasteProfile" class="empty">尚未建立品味輪廓。</div>
          <template v-else>
            <p class="one-liner">{{ tasteProfile.summary }}</p>
            <div class="stat-row"><span>正向題目</span><strong>{{ tasteProfile.liked_count }}</strong></div>
            <div class="stat-row"><span>負向題目</span><strong>{{ tasteProfile.disliked_count }}</strong></div>
            <h4>偏好關鍵字</h4>
            <div class="chips"><span v-for="kw in tasteProfile.preferred_keywords" :key="kw">{{ kw }}</span></div>
            <h4>容易扣分的味道</h4>
            <div class="chips danger-chips"><span v-for="kw in tasteProfile.disliked_keywords" :key="kw">{{ kw }}</span></div>
            <h4>正向題目的平均分數</h4>
            <div class="score-grid">
              <div v-for="(value, key) in tasteProfile.average_positive_scores" :key="key" class="score-cell">
                <span>{{ SCORE_LABELS[key] || key }}</span>
                <strong>{{ value }}</strong>
              </div>
            </div>
            <p class="muted">{{ tasteProfile.recommendation_rule }}</p>
          </template>
        </div>

        <div class="card">
          <h3>依你品味排序的題目</h3>
          <div v-if="!tasteRecommendations.length" class="empty">尚無推薦。先收藏 / 淘汰一些題目。</div>
          <button v-for="item in tasteRecommendations" :key="item.idea.id" class="list-item" @click="selectIdea(item.idea); activeTab='ideas'">
            <strong>{{ item.idea.name }} · {{ item.fit.score }}/100</strong>
            <span>{{ item.fit.verdict }}</span>
            <em>{{ item.fit.reasons?.slice(0, 2).join(' / ') }}</em>
          </button>
        </div>
      </section>

      <section v-if="activeTab === 'graveyard'" class="grid two">
        <div class="card wide">
          <h3>墳場</h3>
          <p class="muted">被淘汰的題目不會刪除。Phase 2 的重點是保存死因，未來 Phase 6 才能復活或合併。</p>
        </div>

        <div class="card">
          <h3>復活候選</h3>
          <div v-if="!reviveIdeas.length" class="empty">尚無復活候選。</div>
          <article v-for="idea in reviveIdeas" :key="idea.id" class="grave-card">
            <h4>{{ idea.name }}</h4>
            <p>{{ idea.one_liner }}</p>
            <small>復活條件：{{ idea.revival_condition || '未填寫' }}</small>
            <div class="status-actions"><button @click="moveBackToBoard(idea, 'saved')">移回收藏</button></div>
          </article>
        </div>

        <div class="card">
          <h3>已死 / 已淘汰</h3>
          <div v-if="!graveyardIdeas.length" class="empty">墳場目前是空的。</div>
          <article v-for="idea in graveyardIdeas" :key="idea.id" class="grave-card">
            <div class="mini-id">{{ idea.id }}</div>
            <h4>{{ idea.name }}</h4>
            <p>{{ idea.one_liner }}</p>
            <small>死因：{{ idea.rejection_reason || '尚未填寫' }}</small>
            <small>復活條件：{{ idea.revival_condition || '尚未填寫' }}</small>
            <div class="status-actions">
              <button @click="selectIdea(idea); activeTab='ideas'">查看</button>
              <button @click="reviveIdea(idea)">標記復活候選</button>
              <button @click="moveBackToBoard(idea, 'saved')">直接移回收藏</button>
            </div>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

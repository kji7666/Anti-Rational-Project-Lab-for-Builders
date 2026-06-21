<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from './api'

const tabs = ['today', 'collectors', 'signals', 'generator', 'ideas', 'reviews', 'export', 'prototype', 'repoexp', 'evolution', 'taste', 'scheduler', 'settings', 'graveyard']
const NAV_GROUPS = [
  { title: '\u4e3b\u6d41\u7a0b', tabs: ['today', 'signals', 'ideas', 'reviews', 'prototype'] },
  { title: '\u7814\u7a76\u8cc7\u7522', tabs: ['evolution', 'taste', 'graveyard'] },
  { title: '\u5de5\u4f5c\u53f0', tabs: ['export', 'repoexp', 'scheduler', 'settings'] },
]
const activeTab = ref('today')
const signals = ref([])
const collectors = ref([])
const collectedSignals = ref([])
const duplicateSignals = ref([])
const collectionWarnings = ref([])
const collectionStats = ref(null)
const ideas = ref([])
const selectedIdea = ref(null)
const generatedIdeas = ref([])
const generationWarnings = ref([])
const generationStages = ref([])
const generationProviderUsed = ref('heuristic')
const llmHealth = ref(null)
const settingsDiagnostics = ref(null)
const settingsLoading = ref(false)
const schedulerStatus = ref(null)
const schedulerJobs = ref([])
const schedulerRuns = ref([])
const schedulerLoading = ref(false)
const schedulerMutatingId = ref('')
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
const ideaSearch = ref('')
const ideaSort = ref('updated_desc')
const showIdeaComposer = ref(false)

const BOARD_STATUSES = [
  { key: 'new', label: '\u65b0\u602a\u984c' },
  { key: 'saved', label: '\u5df2\u6536\u85cf' },
  { key: 'deep_dive', label: '\u6df1\u5165\u7814\u7a76' },
  { key: 'mvp_draft', label: 'MVP \u8349\u7a3f' },
  { key: 'prototype_ready', label: '\u53ef\u505a Prototype' },
  { key: 'prototype', label: 'Prototype \u9032\u884c\u4e2d' },
]

const DEAD_STATUSES = ['dead', 'rejected']

const STATUS_LABELS = {
  new: '\u525b\u751f\u6210',
  saved: '\u5df2\u6536\u85cf',
  rejected: '\u5df2\u6dd8\u6c70',
  deep_dive: '\u6df1\u5165\u7814\u7a76',
  mvp_draft: 'MVP \u8349\u7a3f',
  prototype_ready: '\u53ef\u505a Prototype',
  prototype: 'Prototype \u9032\u884c\u4e2d',
  dead: '\u58b3\u5834',
  revive_candidate: '\u5fa9\u6d3b\u5019\u9078',
  merged: '\u5df2\u5408\u4f75',
}

const SCORE_LABELS = {
  surprise: '驚喜感',
  weirdness: '怪異度',
  memorability: '記憶點',
  visual_imagination: '畫面感',
  real_pain: '真實痛點',
  mvp_feasibility: 'MVP 可做性',
  differentiation: '差異化',
  personal_fit: '個人適配',
  anti_saas: '反 SaaS',
  revival_potential: '復活潛力',
}

const IDEA_PROGRESS_STEPS = [
  { key: 'signals', label: '\u7d20\u6750' },
  { key: 'idea', label: '\u602a\u984c' },
  { key: 'review', label: '\u5be9\u67e5' },
  { key: 'mvp', label: 'MVP' },
  { key: 'prototype', label: 'Prototype' },
  { key: 'experiment', label: '\u5be6\u9a57' },
]

const SCORE_LABEL_MAP = {
  surprise: '驚喜感',
  weirdness: '怪異度',
  memorability: '記憶點',
  visual_imagination: '畫面感',
  real_pain: '真實痛點',
  mvp_feasibility: 'MVP 可做性',
  differentiation: '差異化',
  personal_fit: '個人適配',
  anti_saas: '反 SaaS',
  revival_potential: '復活潛力',
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
  sources: ['github', 'hacker_news', 'arxiv', 'devto', 'lobsters'],
  limit_per_source: 5,
  save: true,
  feed_urls_text: '',
  custom_urls_text: '',
})

const generationForm = ref({
  raw_text: `GitHub Next Discovery Agent 正在研究如何更可靠地 setup / build / test GitHub repositories。
OpenHands 這類 AI coding agent 仍然需要更穩定的 sandbox 與 repo 探測流程。
Railpack 這類工具把陌生 repo 轉成可重現的 build container。
如果不要做成一般 SaaS，而是做成有強烈研究感與畫面感的原型，會變成什麼怪題？`,
  selected_signal_ids: [],
  count: 10,
  save: true,
  mode: 'llm',
  provider: 'local_gpt',
  debug: false,
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

const filteredActiveIdeas = computed(() => {
  const search = ideaSearch.value.trim().toLowerCase()
  let items = activeIdeas.value.slice()
  if (statusFilter.value !== 'all') {
    items = items.filter((idea) => idea.status === statusFilter.value)
  }
  if (search) {
    items = items.filter((idea) => {
      const haystack = [
        idea.name,
        idea.one_liner,
        idea.weird_angle,
        idea.real_pain,
        idea.first_screen,
        idea.mvp,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return haystack.includes(search)
    })
  }

  const scoreTotalForSort = (idea) =>
    ['surprise', 'weirdness', 'memorability', 'real_pain', 'mvp_feasibility', 'anti_saas']
      .reduce((sum, key) => sum + Number(idea?.scores?.[key] || 0), 0)

  items.sort((a, b) => {
    if (ideaSort.value === 'updated_asc') return new Date(a.updated_at) - new Date(b.updated_at)
    if (ideaSort.value === 'score_desc') return scoreTotalForSort(b) - scoreTotalForSort(a)
    if (ideaSort.value === 'name_asc') return (a.name || '').localeCompare(b.name || '', 'zh-Hant')
    return new Date(b.updated_at) - new Date(a.updated_at)
  })
  return items
})

const ideaGroups = computed(() => {
  const groups = Object.fromEntries(BOARD_STATUSES.map((status) => [status.key, []]))
  for (const idea of filteredActiveIdeas.value) {
    if (groups[idea.status]) groups[idea.status].push(idea)
    else groups.new.push(idea)
  }
  return groups
})

const filteredIdeas = computed(() => {
  return filteredActiveIdeas.value
})

const topIdeas = computed(() => ideas.value.slice(0, 5))
const recentSignals = computed(() => signals.value.slice(0, 5))
const nextScheduledJob = computed(() => {
  const enabledJobs = (schedulerJobs.value || [])
    .filter((job) => job.enabled && job.next_run_at)
    .slice()
    .sort((a, b) => new Date(a.next_run_at) - new Date(b.next_run_at))
  return enabledJobs[0] || null
})
const lastSchedulerRun = computed(() => (schedulerRuns.value || [])[0] || null)

const todayStats = computed(() => [
  { key: 'signals', label: '\u7d20\u6750\u6578', value: signals.value.length },
  { key: 'ideas', label: '\u984c\u76ee\u7e3d\u6578', value: ideas.value.length },
  { key: 'active', label: '\u6d3b\u984c\u76ee', value: activeIdeas.value.length },
  { key: 'graveyard', label: '\u58b3\u5834\u6578', value: graveyardIdeas.value.length },
])

const nextAction = computed(() => {
  if (!signals.value.length) {
    return {
      title: '\u5148\u628a\u7814\u7a76\u8a0a\u865f\u4e1f\u9032\u4f86',
      description: '\u5148\u624b\u52d5\u8cbc\u4e00\u5247\u7d20\u6750\uff0c\u6216\u53bb\u81ea\u52d5\u7d20\u6750\u9801\u6293\u4e00\u6279\u8a0a\u865f\uff0c\u602a\u984c\u6d41\u7a0b\u624d\u6709\u6a19\u672c\u53ef\u4ee5\u89e3\u5256\u3002',
      primaryLabel: '\u65b0\u589e\u7d20\u6750',
      primaryTab: 'signals',
      secondaryLabel: '\u81ea\u52d5\u6536\u96c6',
      secondaryTab: 'signals',
    }
  }
  if (!ideas.value.length) {
    return {
      title: '\u628a\u7d20\u6750\u7149\u6210\u7b2c\u4e00\u6279\u602a\u984c',
      description: '\u7d20\u6750\u5df2\u7d93\u6709\u4e86\uff0c\u4e0b\u4e00\u6b65\u5c31\u662f\u628a\u7d20\u6750\u7149\u6210\u7b2c\u4e00\u6279\u53ef\u8a0e\u8ad6\u7684\u602a\u984c\uff0c\u4e26\u7acb\u5373\u653e\u9032\u984c\u76ee\u770b\u677f\u7be9\u9078\u3002',
      primaryLabel: '\u524d\u5f80\u984c\u76ee\u770b\u677f',
      primaryTab: 'ideas',
      secondaryLabel: '\u67e5\u770b\u7d20\u6750\u7bb1',
      secondaryTab: 'signals',
    }
  }
  if (!selectedReviews.value.length) {
    return {
      title: '\u9078\u4e00\u5f35\u984c\u76ee\u505a\u53cd\u5408\u7406\u5be9\u67e5',
      description: '\u73fe\u5728\u6700\u503c\u5f97\u505a\u7684\u662f\u6bba\u6389\u592a\u666e\u901a\u3001\u592a\u50cf SaaS \u7684\u65b9\u5411\uff0c\u7559\u4e0b\u771f\u6b63\u6709\u602a\u5473\u7684\u984c\u76ee\u3002',
      primaryLabel: '\u5230\u5be9\u67e5\u4e2d\u5fc3',
      primaryTab: 'reviews',
      secondaryLabel: '\u67e5\u770b\u984c\u76ee\u677f',
      secondaryTab: 'ideas',
    }
  }
  if (!mvpDraft.value) {
    return {
      title: '\u6536\u6582\u6210 MVP \u8349\u7a3f',
      description: '\u5be9\u67e5\u505a\u5b8c\u5f8c\uff0c\u628a\u6d3b\u4e0b\u4f86\u7684\u984c\u76ee\u58d3\u6210\u7b2c\u4e00\u7248 MVP\uff0c\u624d\u77e5\u9053\u5b83\u80fd\u4e0d\u80fd\u771f\u7684\u88ab\u505a\u51fa\u4f86\u3002',
      primaryLabel: '\u524d\u5f80 MVP \u8f38\u51fa',
      primaryTab: 'export',
      secondaryLabel: '\u56de\u984c\u76ee\u677f',
      secondaryTab: 'ideas',
    }
  }
  if (!prototypeWorkspaces.value.length) {
    return {
      title: '\u5efa\u7acb Prototype Workspace',
      description: 'MVP \u5df2\u7d93\u6210\u5f62\uff0c\u4e0b\u4e00\u6b65\u662f\u751f\u6210 workspace\uff0c\u628a\u984c\u76ee\u8b8a\u6210\u53ef\u4ee5\u5be6\u4f5c\u8207\u8a18\u9304\u7684\u5be6\u9a57\u7a7a\u9593\u3002',
      primaryLabel: '\u524d\u5f80 Prototype',
      primaryTab: 'prototype',
      secondaryLabel: '\u770b MVP \u8349\u7a3f',
      secondaryTab: 'export',
    }
  }
  return {
    title: '\u958b\u59cb\u8a18\u9304\u5be6\u4f5c\u8207\u63a2\u6e2c',
    description: '\u4f60\u5df2\u7d93\u9032\u5230\u539f\u578b\u968e\u6bb5\uff0c\u63a5\u4e0b\u4f86\u53ef\u4ee5\u88dc run ledger\uff0c\u6216\u7528 repo probe \u9a57\u8b49\u5916\u90e8 repo \u5047\u8a2d\u3002',
    primaryLabel: '\u524d\u5f80 Prototype',
    primaryTab: 'prototype',
    secondaryLabel: '\u524d\u5f80 Repo \u5be6\u9a57',
    secondaryTab: 'repoexp',
  }
})

const llmStatusSummary = computed(() => {
  if (llmHealth.value?.available) {
    return {
      title: 'Local GPT \u5728\u7dda',
      detail: '\u53ef\u4ee5\u76f4\u63a5\u8d70\u591a\u6b65\u602a\u984c\u751f\u6210\u6d41\u7a0b\u3002',
      tone: 'ok',
    }
  }
  return {
    title: 'Local GPT \u76ee\u524d\u96e2\u7dda',
    detail: '\u602a\u984c\u7522\u751f\u5668\u4ecd\u53ef\u9000\u56de\u6a21\u677f\u7522\u751f\uff0c\u4e0d\u6703\u5361\u4f4f\u6574\u500b\u4e3b\u6d41\u7a0b\u3002',
      tone: 'warn',
    }
})

const favoriteGenerated = computed(() => {
  return generatedIdeas.value
    .slice()
    .sort((a, b) => scoreTotal(b) - scoreTotal(a))
    .slice(0, 3)
})

function tabLabel(tab) {
  if (tab === 'today') return '\u4eca\u65e5\u6307\u63ee\u53f0'
  if (tab === 'collectors') return '\u81ea\u52d5\u7d20\u6750'
  if (tab === 'signals') return '\u7d20\u6750\u6536\u96c6\u7bb1'
  if (tab === 'generator') return '\u602a\u984c\u7522\u751f\u5668'
  if (tab === 'ideas') return '\u984c\u76ee\u770b\u677f'
  if (tab === 'reviews') return '\u53cd\u5408\u7406\u5be9\u67e5'
  if (tab === 'export') return 'MVP \u8f38\u51fa'
  if (tab === 'prototype') return 'Prototype'
  if (tab === 'repoexp') return 'Repo \u5be6\u9a57'
  if (tab === 'evolution') return '\u984c\u76ee\u6f14\u5316'
  if (tab === 'taste') return '\u500b\u4eba\u54c1\u5473'
  if (tab === 'scheduler') return '\u672c\u5730\u6392\u7a0b'
  if (tab === 'settings') return '\u8a2d\u5b9a / \u8a3a\u65b7'
  if (tab === 'graveyard') return '\u58b3\u5834'
  return '\u984c\u76ee\u770b\u677f'
}

function ideaProgressIndex(status) {
  if (status === 'new') return 1
  if (status === 'saved') return 2
  if (status === 'deep_dive') return 3
  if (status === 'mvp_draft') return 4
  if (status === 'prototype_ready' || status === 'prototype') return 5
  return 0
}

function progressSteps(idea) {
  const current = ideaProgressIndex(idea?.status)
  return IDEA_PROGRESS_STEPS.map((step, index) => ({
    ...step,
    active: current >= index + 1,
  }))
}

function statusLabel(status) {
  return STATUS_LABELS[status] || status || '未設定'
}

function scoreText(idea) {
  const scores = idea?.scores || {}
  const keys = ['surprise', 'weirdness', 'memorability', 'real_pain', 'mvp_feasibility', 'anti_saas']
  return keys
    .filter((key) => scores[key])
    .map((key) => `${SCORE_LABEL_MAP[key]} ${scores[key]}`)
    .join(' / ')
}

function scoreEntries(idea) {
  const scores = idea?.scores || {}
  return Object.entries(SCORE_LABEL_MAP).map(([key, label]) => ({ key, label, value: Number(scores[key] || 0) }))
}

function scoreTotal(idea) {
  return scoreEntries(idea).reduce((sum, item) => sum + Number(item.value || 0), 0)
}

function scoreHighlights(idea) {
  const scores = idea?.scores || {}
  return [
    ['怪異度', scores.weirdness],
    ['真實痛點', scores.real_pain],
    ['反 SaaS', scores.anti_saas],
  ]
    .filter(([, value]) => value)
    .map(([label, value]) => `${label} ${value}`)
}

function flagLabel(flag) {
  const labels = {
    too_saas: '太像 SaaS',
    dashboard_smell: '太像 dashboard / 後台產品',
    platform_smell: '太像 platform / marketplace',
    workflow_smell: '太像 workflow / automation',
    generic_ai_tool: '太像 AI assistant / copilot',
    productivity_smell: '太像效率工具 / 一般生產力產品',
    name_too_plain: '名稱太普通',
    missing_weird_angle: '缺少怪異切角',
    missing_real_pain: '缺少真實痛點',
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

function formatSchedule(job) {
  if (!job) return ''
  if (job.schedule_type === 'interval') {
    return `每 ${job.interval_minutes || 60} 分鐘`
  }
  if (job.schedule_type === 'weekly') {
    const weekdayLabels = ['週日', '週一', '週二', '週三', '週四', '週五', '週六']
    return `${weekdayLabels[job.day_of_week || 0] || '每週'} ${job.time_of_day || '09:00'}`
  }
  return `每天 ${job.time_of_day || '09:00'}`
}

function schedulerStatusLabel(status) {
  const labels = {
    running: '執行中',
    passed: '成功',
    failed: '失敗',
    idle: '待命',
    stopped: '已停止',
  }
  return labels[status] || status || '未設定'
}

function tabNeedsSelectedIdea(tab) {
  return ['reviews', 'export', 'prototype', 'repoexp'].includes(tab)
}

async function activateTab(tab) {
  if (tab === 'collectors') tab = 'signals'
  if (tab === 'generator') tab = 'ideas'
  if ((tabNeedsSelectedIdea(tab) || tab === 'ideas') && !selectedIdea.value && ideas.value.length) {
    await selectIdea(ideas.value[0])
  }
  activeTab.value = tab
}

async function loadLlmHealth() {
  try {
    llmHealth.value = await api.getLlmHealth()
  } catch (err) {
    llmHealth.value = {
      available: false,
      status: 'offline',
      detail: err.message,
      base_url: 'http://127.0.0.1:8788/v1',
      model: 'chatgpt-web-local',
      timeout_seconds: 300,
      api_key_configured: false,
    }
  }
}

async function loadSettingsDiagnostics() {
  settingsLoading.value = true
  try {
    settingsDiagnostics.value = await api.getSettingsDiagnostics()
  } catch (err) {
    settingsDiagnostics.value = null
    error.value = err.message
  } finally {
    settingsLoading.value = false
  }
}

async function loadSchedulerDashboard(showTab = false) {
  schedulerLoading.value = true
  try {
    const [statusResponse, jobsResponse, runsResponse] = await Promise.all([
      api.getSchedulerStatus(),
      api.listSchedulerJobs(),
      api.listSchedulerRuns(),
    ])
    schedulerStatus.value = statusResponse
    schedulerJobs.value = jobsResponse.jobs || []
    schedulerRuns.value = runsResponse.runs || []
    if (showTab) activeTab.value = 'scheduler'
  } catch (err) {
    schedulerStatus.value = null
    schedulerJobs.value = []
    schedulerRuns.value = []
    error.value = err.message
  } finally {
    schedulerLoading.value = false
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
    await loadLlmHealth()
    await loadSettingsDiagnostics()
    await loadSchedulerDashboard(false)
    await loadEvolutionDashboard(false)
    await loadTasteDashboard(false)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

async function toggleSchedulerJob(job, enabled) {
  error.value = ''
  schedulerMutatingId.value = job.id
  try {
    await api.updateSchedulerJob(job.id, { enabled })
    await loadSchedulerDashboard(activeTab.value === 'scheduler')
  } catch (err) {
    error.value = err.message
  } finally {
    schedulerMutatingId.value = ''
  }
}

async function runSchedulerJobNow(job) {
  error.value = ''
  schedulerMutatingId.value = job.id
  try {
    const response = await api.runSchedulerJob(job.id)
    if (response?.message) {
      error.value = response.message.includes('憭望?') ? response.message : ''
    }
    await refreshAll()
    activeTab.value = 'scheduler'
  } catch (err) {
    error.value = err.message
  } finally {
    schedulerMutatingId.value = ''
  }
}


async function runCollectors() {
  error.value = ''
  collectionWarnings.value = []
  collectionStats.value = null
  duplicateSignals.value = []
  if (!collectorForm.value.sources.length) {
    error.value = '請至少選擇一個素材來源。'
    return
  }
  collecting.value = true
  try {
    const feedUrls = collectorForm.value.feed_urls_text
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean)
    const customUrls = collectorForm.value.custom_urls_text
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean)
    const response = await api.collectSignals({
      query: collectorForm.value.query,
      sources: collectorForm.value.sources,
      limit_per_source: Number(collectorForm.value.limit_per_source),
      save: collectorForm.value.save,
      feed_urls: feedUrls,
      custom_urls: customUrls,
    })
    collectedSignals.value = response.signals || []
    duplicateSignals.value = response.duplicate_signals || []
    collectionWarnings.value = response.warnings || []
    collectionStats.value = response.stats || null
    if (response.errors?.length) {
      error.value = response.errors.map((item) => `${item.source}: ${item.error}`).join(' / ')
    }
    await refreshAll()
    activeTab.value = 'signals'
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
  generationWarnings.value = []
  generationStages.value = []
  generationProviderUsed.value = generationForm.value.mode === 'llm' ? 'local_gpt' : 'heuristic'
  try {
    const response = await api.generateIdeas({
      raw_text: generationForm.value.raw_text,
      signal_ids: generationForm.value.selected_signal_ids,
      count: Number(generationForm.value.count),
      save: generationForm.value.save,
      mode: generationForm.value.mode,
      provider: generationForm.value.mode === 'llm' ? generationForm.value.provider : null,
      debug: generationForm.value.debug,
    })
    generatedIdeas.value = response.ideas
    generationWarnings.value = response.warnings || []
    generationStages.value = response.pipeline_stages || []
    generationProviderUsed.value = response.provider_used || generationProviderUsed.value
    await loadLlmHealth()
    await refreshAll()
    activeTab.value = 'ideas'
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
    showIdeaComposer.value = false
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

async function selectIdea(idea) {
  selectedIdea.value = idea
  syncGraveyardForm(idea)
  await loadIdeaMeta(idea)
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
    rejection_reason: graveyardForm.value.rejection_reason || '尚未填寫淘汰原因',
    revival_condition: graveyardForm.value.revival_condition,
    status_note: graveyardForm.value.status_note,
  })
  activeTab.value = 'graveyard'
}

async function reviveIdea(idea) {
  await setIdeaStatus(idea, 'revive_candidate', {
    status_note: idea.status_note || '已加入復活候選，等待重新評估。',
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
    status_note: idea.status_note || '已移回主題目看板。',
  })
  activeTab.value = 'ideas'
}

onMounted(refreshAll)
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">&#x602A;</div>
        <div>
          <h1>&#x602A;&#x984C;&#x7814;&#x7A76;&#x6240;</h1>
          <p>&#x5F9E;&#x7D20;&#x6750;&#x3001;&#x602A;&#x984C;&#x3001;&#x5BE9;&#x67E5;&#x5230; Prototype &#x7684;&#x672C;&#x5730;&#x5BE6;&#x9A57;&#x5BA4;</p>
        </div>
      </div>

      <div v-for="group in NAV_GROUPS" :key="group.title" class="nav-group">
        <div class="nav-group-title">{{ group.title }}</div>
        <button
          v-for="tab in group.tabs"
          :key="tab"
          type="button"
          class="nav-button"
          :class="{ active: activeTab === tab }"
          @click="activateTab(tab)"
        >
          {{ tabLabel(tab) }}
        </button>
      </div>
    </aside>

    <main class="main-panel">
      <div class="topbar">
        <div>
          <h2 v-if="activeTab === 'today'">&#x4ECA;&#x65E5;&#x6307;&#x63EE;&#x53F0;</h2>
          <h2 v-else-if="activeTab === 'collectors'">&#x81EA;&#x52D5;&#x7D20;&#x6750;&#x6536;&#x96C6;</h2>
          <h2 v-else-if="activeTab === 'signals'">&#x7D20;&#x6750;&#x6536;&#x96C6;&#x7BB1;</h2>
          <h2 v-else-if="activeTab === 'generator'">&#x602A;&#x984C;&#x7522;&#x751F;&#x5668;</h2>
          <h2 v-else-if="activeTab === 'reviews'">&#x53CD;&#x5408;&#x7406;&#x5BE9;&#x67E5;</h2>
          <h2 v-else-if="activeTab === 'export'">MVP &#x6536;&#x6582;&#x8207;&#x4EFB;&#x52D9;&#x5305;&#x8F38;&#x51FA;</h2>
          <h2 v-else-if="activeTab === 'prototype'">Prototype Workspace &#x8207; Run Ledger</h2>
          <h2 v-else-if="activeTab === 'repoexp'">Repo Setup / Build / Test &#x5BE6;&#x9A57;</h2>
          <h2 v-else-if="activeTab === 'evolution'">&#x984C;&#x76EE;&#x6F14;&#x5316;&#x3001;&#x5408;&#x4F75;&#x8207;&#x5FA9;&#x6D3B;</h2>
          <h2 v-else-if="activeTab === 'taste'">&#x500B;&#x4EBA;&#x54C1;&#x5473;&#x5B78;&#x7FD2;</h2>
          <h2 v-else-if="activeTab === 'scheduler'">&#x672C;&#x5730;&#x6392;&#x7A0B;&#x8207;&#x57F7;&#x884C;&#x7D00;&#x9304;</h2>
          <h2 v-else-if="activeTab === 'settings'">&#x8A2D;&#x5B9A;&#x8207;&#x8A3A;&#x65B7;</h2>
          <h2 v-else-if="activeTab === 'graveyard'">&#x58B3;&#x5834;</h2>
          <h2 v-else>&#x984C;&#x76EE;&#x770B;&#x677F;</h2>
          <p>&#x9019;&#x88E1;&#x4E0D;&#x662F;&#x529F;&#x80FD;&#x6E05;&#x55AE;&#xFF0C;&#x800C;&#x662F;&#x4E00;&#x689D;&#x5F9E;&#x7D20;&#x6750;&#x8D70;&#x5230;&#x539F;&#x578B;&#x7684;&#x602A;&#x984C;&#x4E3B;&#x6D41;&#x7A0B;&#x3002;</p>
        </div>
        <button class="ghost" @click="refreshAll">&#x91CD;&#x65B0;&#x6574;&#x7406;</button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="loading" class="muted">&#x8B80;&#x53D6;&#x4E2D;...</p>

      <section v-if="activeTab === 'today'" class="grid two">
        <div class="card">
          <h3>&#x4ECA;&#x65E5;&#x6A19;&#x672C;&#x6578;</h3>
          <div v-for="item in todayStats" :key="item.key" class="stat-row"><span>{{ item.label }}</span><strong>{{ item.value }}</strong></div>
        </div>

        <div class="card">
          <h3>&#x4E0B;&#x4E00;&#x6B65;&#x6700;&#x503C;&#x5F97;&#x505A;</h3>
          <p class="one-liner">{{ nextAction.title }}</p>
          <p class="muted">{{ nextAction.description }}</p>
          <div class="status-actions">
            <button @click="activeTab = nextAction.primaryTab">{{ nextAction.primaryLabel }}</button>
            <button class="ghost" @click="activeTab = nextAction.secondaryTab">{{ nextAction.secondaryLabel }}</button>
          </div>
        </div>

        <div class="card">
          <h3>Local GPT &#x72C0;&#x614B;</h3>
          <div class="llm-status">
            <strong>{{ llmStatusSummary.title }}</strong>
            <span>API&#xFF1A;{{ llmHealth?.base_url || 'http://127.0.0.1:8788/v1' }}</span>
            <span>&#x6A21;&#x578B;&#xFF1A;{{ llmHealth?.model || 'chatgpt-web-local' }}</span>
            <span>{{ llmStatusSummary.detail }}</span>
          </div>
        </div>

        <div class="card">
          <h3>&#x5FEB;&#x901F;&#x5165;&#x53E3;</h3>
          <div class="quick-links">
            <button class="ghost" @click="activateTab('signals')">開始收集素材</button>
            <button class="ghost" @click="activateTab('signals')">查看素材箱</button>
            <button class="ghost" @click="activateTab('ideas')">產生怪題</button>
            <button class="ghost" @click="activateTab('ideas')">打開題目看板</button>
          </div>
        </div>

        <div class="card">
          <h3>下一個排程</h3>
          <div v-if="!schedulerStatus" class="empty">排程服務尚未啟動，請先確認 backend 已啟用排程模組。</div>
          <div v-else-if="!nextScheduledJob" class="empty">目前沒有啟用中的排程工作。</div>
          <div v-else class="llm-status">
            <strong>{{ nextScheduledJob.name }}</strong>
            <span>頻率：{{ formatSchedule(nextScheduledJob) }}</span>
            <span>下次執行：{{ formatDate(nextScheduledJob.next_run_at) }}</span>
            <span>上次狀態：{{ schedulerStatusLabel(nextScheduledJob.last_status) }}</span>
          </div>
          <div class="status-actions">
            <button @click="activateTab('scheduler')">前往排程</button>
          </div>
        </div>

        <div class="card">
          <h3>最近一次排程紀錄</h3>
          <div v-if="!lastSchedulerRun" class="empty">目前還沒有排程執行紀錄。</div>
          <div v-else class="llm-status">
            <strong>{{ lastSchedulerRun.job_key }}</strong>
            <span>狀態：{{ schedulerStatusLabel(lastSchedulerRun.status) }}</span>
            <span>開始時間：{{ formatDate(lastSchedulerRun.started_at) }}</span>
            <span>摘要：{{ lastSchedulerRun.summary || '目前沒有摘要' }}</span>
          </div>
        </div>

        <div class="card wide">
          <h3>&#x6700;&#x8FD1;&#x5192;&#x51FA;&#x4F86;&#x7684;&#x984C;&#x76EE;</h3>
          <div v-if="!topIdeas.length" class="empty">&#x9084;&#x6C92;&#x6709;&#x984C;&#x76EE;&#x3002;&#x5148;&#x4E1F;&#x4E00;&#x6279;&#x7D20;&#x6750;&#xFF0C;&#x6216;&#x76F4;&#x63A5;&#x53BB;&#x602A;&#x984C;&#x7522;&#x751F;&#x5668;&#x7149;&#x51FA;&#x7B2C;&#x4E00;&#x8F2A;&#x6A19;&#x672C;&#x3002;</div>
          <button v-for="idea in topIdeas" :key="idea.id" class="list-item" @click="selectIdea(idea); activeTab='ideas'">
            <strong>{{ idea.name }}</strong>
            <span>{{ idea.one_liner || '\u9084\u6c92\u6709\u4e00\u53e5\u8a71\u63cf\u8ff0\u3002' }}</span>
            <em>{{ statusLabel(idea.status) }}</em>
          </button>
        </div>

        <div class="card wide">
          <h3>&#x6700;&#x8FD1;&#x6536;&#x9032;&#x4F86;&#x7684;&#x7D20;&#x6750;</h3>
          <div v-if="!recentSignals.length" class="empty">&#x76EE;&#x524D;&#x9084;&#x6C92;&#x6709;&#x7D20;&#x6750;&#x3002;&#x4F60;&#x53EF;&#x4EE5;&#x624B;&#x52D5;&#x8CBC;&#x4E00;&#x5247;&#x7814;&#x7A76;&#x8A0A;&#x865F;&#xFF0C;&#x6216;&#x53BB;&#x81EA;&#x52D5;&#x7D20;&#x6750;&#x9801;&#x5148;&#x6293;&#x4E00;&#x6279;&#x3002;</div>
          <div v-for="signal in recentSignals" :key="signal.id" class="signal-line">
            <strong>{{ signal.title }}</strong>
            <span>{{ signal.summary }}</span>
          </div>
        </div>
      </section>



      <section v-if="activeTab === 'signals'" class="grid two">
        <form class="card form" @submit.prevent="runCollectors">
          <h3>自動素材收集</h3>
          <p class="muted">先決定主題與來源，系統會從可用管道抓取素材、去重，並在存檔前盡量翻成中文。</p>
          <label>收集主題
            <textarea v-model="collectorForm.query" rows="3" placeholder="例如：AI agent、prototype tool、developer workflow" />
          </label>
          <div class="signal-picker">
            <h4>收集來源</h4>
            <label v-for="collector in collectors" :key="collector.key" class="collector-option">
              <div class="checkbox-line">
                <input type="checkbox" :value="collector.key" v-model="collectorForm.sources" :disabled="!collector.enabled" />
                <span><strong>{{ collector.label }}</strong> {{ collector.description }}</span>
              </div>
              <div class="collector-meta">
                <span>分類：{{ collector.category || '一般來源' }}</span>
                <span>{{ collector.enabled ? '可用' : '目前不可用' }}</span>
                <span>{{ collector.requires_network ? '需要網路' : '本地可用' }}</span>
                <span>{{ collector.requires_api_key ? '需要 API Key' : '不需 API Key' }}</span>
                <span>風險：{{ collector.risk_level }}</span>
              </div>
            </label>
          </div>
          <div class="split">
            <label>RSS Feed URL
              <textarea v-model="collectorForm.feed_urls_text" rows="4" placeholder="每行一個 feed URL" />
            </label>
            <label>自訂網址
              <textarea v-model="collectorForm.custom_urls_text" rows="4" placeholder="每行一個要抓取的網址" />
            </label>
          </div>
          <div class="split">
            <label>每個來源最多幾則<input v-model="collectorForm.limit_per_source" type="number" min="1" max="10" /></label>
            <label class="checkbox-inline"><input v-model="collectorForm.save" type="checkbox" /> 收集後直接存入素材箱</label>
          </div>
          <button type="submit" :disabled="collecting">{{ collecting ? '收集中...' : '開始收集' }}</button>
        </form>

        <div class="card">
          <h3>素材箱</h3>
          <div v-if="collectionStats" class="collection-stats">
            <div class="status-count"><span>總抓取</span><strong>{{ collectionStats.collected_count }}</strong></div>
            <div class="status-count"><span>新增素材</span><strong>{{ collectionStats.new_count }}</strong></div>
            <div class="status-count"><span>重複素材</span><strong>{{ collectionStats.duplicate_count }}</strong></div>
            <div class="status-count"><span>失敗來源</span><strong>{{ collectionStats.failed_count }}</strong></div>
          </div>
          <div v-if="collectionWarnings.length" class="warning-box">
            <strong>收集警告</strong>
            <ul>
              <li v-for="warning in collectionWarnings" :key="warning">{{ warning }}</li>
            </ul>
          </div>
          <div v-if="!signals.length" class="empty">目前還沒有素材。</div>
          <div v-for="signal in signals" :key="signal.id" class="signal-card">
            <div class="mini-id">{{ signal.id }}</div>
            <strong>{{ signal.title }}</strong>
            <p>{{ signal.summary }}</p>
            <div class="collector-meta">
              <span>分類：{{ signal.source_category || '手動 / 一般來源' }}</span>
              <span>品質分數：{{ signal.quality_score ?? '未評估' }}</span>
            </div>
            <p v-if="signal.quality_reason" class="muted">品質理由：{{ signal.quality_reason }}</p>
            <div class="chips"><span v-for="tag in signal.tags" :key="tag">{{ tag }}</span></div>
          </div>
        </div>

        <form class="card form" @submit.prevent="submitSignal">
          <h3>手動新增素材</h3>
          <label>標題<input v-model="signalForm.title" required /></label>
          <label>來源類型<input v-model="signalForm.source_type" /></label>
          <label>URL<input v-model="signalForm.source_url" /></label>
          <label>摘要<textarea v-model="signalForm.summary" rows="3" /></label>
          <label>原文 / 原始訊號<textarea v-model="signalForm.raw_text" rows="6" /></label>
          <label>標籤（以逗號分隔）<input v-model="signalForm.tags_text" /></label>
          <div class="split">
            <label>怪異度<input v-model="signalForm.weirdness" type="number" min="1" max="10" /></label>
            <label>痛點感<input v-model="signalForm.pain_signal" type="number" min="1" max="10" /></label>
          </div>
          <button type="submit">存入素材箱</button>
        </form>

        <div class="card">
          <h3>最近收集結果</h3>
          <div v-if="!collectedSignals.length" class="empty">還沒有新的收集結果。</div>
          <article v-for="signal in collectedSignals" :key="signal.id || signal.title" class="signal-card">
            <div class="mini-id">{{ signal.id || 'preview' }} · {{ signal.source_type }}</div>
            <strong>{{ signal.title }}</strong>
            <p>{{ signal.summary }}</p>
            <a v-if="signal.source_url" :href="signal.source_url" target="_blank" rel="noreferrer">查看來源</a>
          </article>
        </div>
      </section>

      <section v-if="false && activeTab === 'generator'" class="generator-layout">
        <form class="card form" @submit.prevent="generateIdeas">
          <h3>怪題產生器</h3>
          <p class="muted">可直接貼文字，或勾選素材箱中的素材，快速產生一批怪題候選。</p>
          <label>怪題輸入<textarea v-model="generationForm.raw_text" rows="10" /></label>
          <label>產生模式
            <select v-model="generationForm.mode">
              <option value="heuristic">模板產生</option>
              <option value="llm">Local GPT 多步產生</option>
            </select>
          </label>
          <div class="llm-status" v-if="generationForm.mode === 'llm'">
            <strong>檢查 Local GPT</strong>
            <span>API：http://127.0.0.1:8788/v1</span>
            <span v-if="llmHealth?.available">Local GPT 可用</span>
            <span v-else>Local GPT 無法使用，已改用模板產生</span>
          </div>
          <div class="signal-picker signal-picker-scroll">
            <h4>勾選素材箱中的素材</h4>
            <div v-if="!signals.length" class="empty">還沒有可用素材，先回素材箱收集。</div>
            <label v-for="signal in signals" :key="signal.id" class="checkbox-line">
              <input type="checkbox" :value="signal.id" v-model="generationForm.selected_signal_ids" />
              <span>{{ signal.title }}</span>
            </label>
          </div>
          <div class="split">
            <label>產生數量<input v-model="generationForm.count" type="number" min="1" max="10" /></label>
            <label class="checkbox-inline"><input v-model="generationForm.save" type="checkbox" /> 產生後直接存入題目庫</label>
          </div>
          <button type="submit" :disabled="generating">{{ generating ? '產生中...' : '開始產生' }}</button>
          <label class="checkbox-inline" v-if="generationForm.mode === 'llm'"><input v-model="generationForm.debug" type="checkbox" /> 顯示 Pipeline 摘要</label>
        </form>

        <div class="generated-list">
          <div class="card">
            <div class="mini-id">目前提供者：{{ generationProviderUsed }}</div>
            <div v-if="generationWarnings.length" class="warning-box">
              <strong>Fallback 警告</strong>
              <ul>
                <li v-for="warning in generationWarnings" :key="warning">{{ warning }}</li>
              </ul>
            </div>
            <div v-if="generationStages.length" class="stage-box">
              <strong>Pipeline 摘要</strong>
              <article v-for="stage in generationStages" :key="stage.stage" class="stage-item">
                <h4>{{ stage.title }}</h4>
                <p>{{ stage.summary }}</p>
              </article>
            </div>
          </div>
          <div class="card"><h3>最新產生結果</h3><div v-if="!generatedIdeas.length" class="empty">還沒有新的怪題結果。</div></div>
          <article v-for="idea in generatedIdeas" :key="idea.id || idea.name" class="idea-result card">
            <div class="idea-result-head">
              <div><div class="mini-id">{{ idea.id || '未存檔' }}</div><h3>{{ idea.name }}</h3></div>
              <button v-if="!idea.id" type="button" class="ghost small" @click="saveGeneratedIdea(idea)">存成題目</button>
              <button v-else type="button" class="ghost small" @click="selectIdea(idea); activeTab='ideas'">查看詳情</button>
            </div>
            <p class="one-liner">{{ idea.one_liner }}</p>
            <div class="score-line">{{ scoreText(idea) }}</div>
            <h4>怪異切角</h4><p>{{ idea.weird_angle }}</p>
            <h4>真實痛點</h4><p>{{ idea.real_pain }}</p>
            <h4>第一屏畫面</h4><p>{{ idea.first_screen }}</p>
            <h4>MVP 草稿</h4><p>{{ idea.mvp }}</p>
          </article>
        </div>
      </section>

      <section v-if="activeTab === 'ideas'" class="ideas-layout">
        <div class="left-column">
          <div class="generator-layout merged-generator">
            <form class="card form" @submit.prevent="generateIdeas">
              <h3>怪題產生器</h3>
              <p class="muted">可直接貼文字，或勾選素材箱中的素材，快速產生一批怪題候選。</p>
              <label>怪題輸入<textarea v-model="generationForm.raw_text" rows="10" /></label>
              <label>產生模式
                <select v-model="generationForm.mode">
                  <option value="heuristic">模板產生</option>
                  <option value="llm">Local GPT 多步產生</option>
                </select>
              </label>
              <div class="llm-status" v-if="generationForm.mode === 'llm'">
                <strong>檢查 Local GPT</strong>
                <span>API：http://127.0.0.1:8788/v1</span>
                <span v-if="llmHealth?.available">Local GPT 可用</span>
                <span v-else>Local GPT 無法使用，已改用模板產生</span>
              </div>
              <div class="signal-picker signal-picker-scroll">
                <h4>勾選素材箱中的素材</h4>
                <div v-if="!signals.length" class="empty">還沒有可用素材，先回素材箱收集。</div>
                <label v-for="signal in signals" :key="signal.id" class="checkbox-line">
                  <input type="checkbox" :value="signal.id" v-model="generationForm.selected_signal_ids" />
                  <span>{{ signal.title }}</span>
                </label>
              </div>
              <div class="split">
                <label>產生數量<input v-model="generationForm.count" type="number" min="1" max="10" /></label>
                <label class="checkbox-inline"><input v-model="generationForm.save" type="checkbox" /> 產生後直接存入題目庫</label>
              </div>
              <button type="submit" :disabled="generating">{{ generating ? '產生中...' : '開始產生' }}</button>
              <label class="checkbox-inline" v-if="generationForm.mode === 'llm'"><input v-model="generationForm.debug" type="checkbox" /> 顯示 Pipeline 摘要</label>
            </form>

            <div class="generated-list">
              <div class="card">
                <div class="mini-id">目前提供者：{{ generationProviderUsed }}</div>
                <div v-if="generationWarnings.length" class="warning-box">
                  <strong>Fallback 警告</strong>
                  <ul>
                    <li v-for="warning in generationWarnings" :key="warning">{{ warning }}</li>
                  </ul>
                </div>
                <div v-if="generationStages.length" class="stage-box">
                  <strong>Pipeline 摘要</strong>
                  <article v-for="stage in generationStages" :key="stage.stage" class="stage-item">
                    <h4>{{ stage.title }}</h4>
                    <p>{{ stage.summary }}</p>
                  </article>
                </div>
              </div>
              <div class="card"><h3>最新產生結果</h3><div v-if="!generatedIdeas.length" class="empty">還沒有新的怪題結果。</div></div>
              <article v-for="idea in generatedIdeas" :key="idea.id || idea.name" class="idea-result card">
                <div class="idea-result-head">
                  <div><div class="mini-id">{{ idea.id || '未存檔' }}</div><h3>{{ idea.name }}</h3></div>
                  <button v-if="!idea.id" type="button" class="ghost small" @click="saveGeneratedIdea(idea)">存成題目</button>
                  <button v-else type="button" class="ghost small" @click="selectIdea(idea); activeTab='ideas'">查看詳情</button>
                </div>
                <p class="one-liner">{{ idea.one_liner }}</p>
                <div class="score-line">{{ scoreText(idea) }}</div>
                <h4>怪異切角</h4><p>{{ idea.weird_angle }}</p>
                <h4>真實痛點</h4><p>{{ idea.real_pain }}</p>
                <h4>第一屏畫面</h4><p>{{ idea.first_screen }}</p>
                <h4>MVP 草稿</h4><p>{{ idea.mvp }}</p>
              </article>
            </div>
          </div>

          <div class="card board-shell">
            <div class="board-topbar">
              <div>
                <h3>題目看板</h3>
                <p class="muted">把新產生的想法快速篩到合適狀態，再挑一張往審查與原型推進。</p>
              </div>
              <div class="status-actions">
                <button type="button" @click="showIdeaComposer = !showIdeaComposer">{{ showIdeaComposer ? '收起新建題目' : '新增題目' }}</button>
                <button type="button" class="ghost" @click="activateTab('ideas')">留在看板篩選</button>
              </div>
            </div>

            <div class="board-filters">
              <label>搜尋題目<input v-model="ideaSearch" placeholder="搜尋標題、切角、痛點或 MVP..." /></label>
              <label>排序方式
                <select v-model="ideaSort">
                  <option value="updated_desc">最近更新優先</option>
                  <option value="updated_asc">最早更新優先</option>
                  <option value="score_desc">高分題目優先</option>
                  <option value="name_asc">標題 A-Z</option>
                </select>
              </label>
            </div>

            <div class="board-summary">
              <div class="status-count"><span>目前可見題目</span><strong>{{ filteredIdeas.length }}</strong></div>
              <div class="status-count"><span>活躍題目</span><strong>{{ activeIdeas.length }}</strong></div>
              <div class="status-count"><span>已選題目</span><strong>{{ selectedIdea ? 1 : 0 }}</strong></div>
            </div>
          </div>

          <form v-if="showIdeaComposer" class="card form" @submit.prevent="submitIdea">
            <h3>手動建立題目</h3>
            <label>題目名稱<input v-model="ideaForm.name" required /></label>
            <label>一句話介紹<input v-model="ideaForm.one_liner" /></label>
            <label>怪異切角<textarea v-model="ideaForm.weird_angle" rows="2" /></label>
            <label>真實痛點<textarea v-model="ideaForm.real_pain" rows="2" /></label>
            <label>第一屏畫面<textarea v-model="ideaForm.first_screen" rows="2" /></label>
            <label>MVP 草稿<textarea v-model="ideaForm.mvp" rows="3" /></label>
            <label>來源素材 ID（以逗號分隔）<input v-model="ideaForm.source_signal_ids_text" /></label>
            <div class="status-actions">
              <button type="submit">新增題目</button>
              <button type="button" class="ghost" @click="showIdeaComposer = false">取消</button>
            </div>
          </form>

          <div class="card board-toolbar">
            <h3>題目狀態篩選</h3>
            <div class="status-actions">
              <button type="button" :class="{ active: statusFilter === 'all' }" @click="statusFilter='all'">全部活躍題目</button>
              <button type="button" v-for="status in BOARD_STATUSES" :key="status.key" :class="{ active: statusFilter === status.key }" @click="statusFilter=status.key">
                {{ status.label }} {{ statusCounts[status.key] || 0 }}
              </button>
            </div>
          </div>

          <div class="board">
            <div v-for="status in BOARD_STATUSES" :key="status.key" class="board-column">
              <h3>{{ status.label }} <span>{{ ideaGroups[status.key]?.length || 0 }}</span></h3>
              <button type="button" v-for="idea in ideaGroups[status.key]" :key="idea.id" class="idea-card" @click="selectIdea(idea)">
                <div class="idea-card-head">
                  <strong>{{ idea.name }}</strong>
                  <span class="mini-badge">{{ statusLabel(idea.status) }}</span>
                </div>
                <span>{{ idea.one_liner || '\u6c92\u6709\u4e00\u53e5\u8a71\u63cf\u8ff0' }}</span>
                <div class="chips compact-chips">
                  <span v-for="item in scoreHighlights(idea)" :key="item">{{ item }}</span>
                </div>
                <div class="progress-row compact">
                  <span v-for="step in progressSteps(idea)" :key="step.key" :class="['progress-chip', { active: step.active }]">{{ step.label }}</span>
                </div>
              </button>
            </div>
          </div>

          <div class="card">
            <h3>快速題目清單</h3>
            <div v-if="!filteredIdeas.length" class="empty">
              還沒有符合條件的題目，先新增一張，或回素材頁與怪題產生器建立候選。
              <div class="status-actions empty-actions">
                <button type="button" @click="showIdeaComposer = true">手動新增第一張題目</button>
                <button type="button" class="ghost" @click="activateTab('signals')">先去整理素材</button>
              </div>
            </div>
            <button type="button" v-for="idea in filteredIdeas" :key="idea.id" class="list-item" @click="selectIdea(idea)">
              <div class="idea-card-head">
                <strong>{{ idea.name }}</strong>
                <span class="mini-badge">{{ statusLabel(idea.status) }}</span>
              </div>
              <span>{{ idea.one_liner || '\u6c92\u6709\u4e00\u53e5\u8a71\u63cf\u8ff0' }}</span>
              <div class="chips compact-chips">
                <span v-for="item in scoreHighlights(idea)" :key="item">{{ item }}</span>
              </div>
              <div class="progress-row compact">
                <span v-for="step in progressSteps(idea)" :key="step.key" :class="['progress-chip', { active: step.active }]">{{ step.label }}</span>
              </div>
              <em>{{ statusLabel(idea.status) }} &#xB7; {{ formatDate(idea.updated_at) }}</em>
            </button>
          </div>
        </div>

        <aside class="detail card" v-if="selectedIdea">
          <div class="mini-id">{{ selectedIdea.id }}</div>
          <h3>{{ selectedIdea.name }}</h3>
          <p class="one-liner">{{ selectedIdea.one_liner }}</p>
          <div class="score-line">{{ scoreText(selectedIdea) || '撠?' }}</div>
          <div class="status-pill">{{ statusLabel(selectedIdea.status) }}</div>
          <div class="progress-row">
            <span v-for="step in progressSteps(selectedIdea)" :key="step.key" :class="['progress-chip', { active: step.active }]">{{ step.label }}</span>
          </div>
          <div class="quick-actions cardless">
            <button type="button" @click="setIdeaStatus(selectedIdea, 'saved')">加入收藏</button>
            <button type="button" @click="setIdeaStatus(selectedIdea, 'deep_dive')">深入研究</button>
            <button type="button" @click="runReview" :disabled="reviewing">{{ reviewing ? '審查中...' : '送去反合理審查' }}</button>
            <button type="button" class="ghost" @click="activeTab='export'; loadMvpDraft()">查看 MVP</button>
            <button type="button" class="ghost" @click="sendToGraveyard('rejected')">送入墳場</button>
          </div>

          <details class="detail-section" open>
            <summary>基本資訊</summary>
            <h4>怪異切角</h4><p>{{ selectedIdea.weird_angle || '尚未填寫' }}</p>
            <h4>真實痛點</h4><p>{{ selectedIdea.real_pain || '尚未填寫' }}</p>
            <h4>第一屏畫面</h4><p>{{ selectedIdea.first_screen || '尚未填寫' }}</p>
            <h4>MVP 草稿</h4><p>{{ selectedIdea.mvp || '尚未填寫' }}</p>
          </details>

          <details class="detail-section" open>
            <summary>反合理審查</summary>
            <div class="status-actions">
              <button type="button" @click="runReview" :disabled="reviewing">{{ reviewing ? '審查中...' : '重新執行審查' }}</button>
              <button type="button" @click="refreshIdeaScores">重新計分</button>
              <button type="button" @click="loadRenameSuggestions">取得改名建議</button>
              <button type="button" class="ghost" @click="activeTab='reviews'">前往審查頁</button>
            </div>
            <div v-if="commercialSmell" class="smell-box">
              <strong>商業味濃度：{{ commercialSmell.severity }}/10</strong>
              <div v-if="commercialSmell.flags?.length" class="chips danger-chips">
                <span v-for="flag in commercialSmell.flags" :key="flag">{{ flagLabel(flag) }}</span>
              </div>
              <p v-else class="muted">目前沒有明顯的 SaaS 氣味警告。</p>
            </div>
            <div v-if="renameSuggestions.length" class="rename-box">
              <h4>改名建議</h4>
              <button type="button" v-for="name in renameSuggestions" :key="name" class="name-chip" @click="applyRenameSuggestion(name)">{{ name }}</button>
            </div>
            <div v-if="!selectedReviews.length" class="empty">還沒有審查紀錄。</div>
            <article v-for="review in selectedReviews.slice(0, 2)" :key="review.id" class="review-mini">
              <strong>{{ review.passes ? '通過' : '未通過' }} · {{ review.review_type }}</strong>
              <p>{{ review.comment }}</p>
            </article>
          </details>

          <details class="detail-section">
            <summary>分數與品味</summary>
            <div class="score-grid">
              <div v-for="item in scoreEntries(selectedIdea)" :key="item.key" class="score-cell">
                <span>{{ item.label }}</span>
                <strong>{{ item.value || '-' }}</strong>
              </div>
            </div>
            <div class="status-actions">
              <button type="button" @click="loadTasteFit">載入品味適配</button>
              <button type="button" @click="giveTasteFeedback('love')">我喜歡</button>
              <button type="button" @click="giveTasteFeedback('too_boring')">太無聊</button>
              <button type="button" @click="giveTasteFeedback('too_saas')">太像 SaaS</button>
              <button type="button" @click="applyTasteScoreToIdea">套用 personal_fit 分數</button>
            </div>
            <input v-model="tasteFeedbackNote" placeholder="補充一句你喜歡或不喜歡這個題目的原因" />
            <div v-if="selectedTasteFit" class="smell-box">
              <strong>個人適配分數：{{ selectedTasteFit.score }}/100</strong>
              <p>{{ selectedTasteFit.verdict }}</p>
              <div v-if="selectedTasteFit.reasons?.length" class="chips"><span v-for="reason in selectedTasteFit.reasons" :key="reason">{{ reason }}</span></div>
              <div v-if="selectedTasteFit.warnings?.length" class="chips danger-chips"><span v-for="warning in selectedTasteFit.warnings" :key="warning">{{ warning }}</span></div>
            </div>
          </details>

          <details class="detail-section">
            <summary>演化、相似與事件</summary>
            <div v-if="!similarItems.length" class="empty">目前沒有找到相似題目。</div>
            <article v-for="item in similarItems.slice(0, 3)" :key="item.idea.id" class="review-mini">
              <strong>{{ item.idea.name }} · 相似度 {{ Math.round(item.score * 100) }}%</strong>
              <p>{{ item.idea.one_liner }}</p>
              <small>{{ item.reasons.join(' / ') }}</small>
              <div class="status-actions"><button type="button" @click="selectIdea(item.idea)">查看</button></div>
            </article>
            <form class="inline-form" @submit.prevent="createEvent">
              <input v-model="eventForm.title" placeholder="例如：改名、合併、復活條件" />
              <textarea v-model="eventForm.note" rows="2" placeholder="補充這次變更對題目的影響或原因" />
              <button type="submit">新增事件</button>
            </form>
            <div v-if="!ideaEvents.length" class="empty">還沒有事件紀錄。</div>
            <article v-for="event in ideaEvents.slice(0, 3)" :key="event.id" class="review-mini">
              <strong>{{ event.title || event.event_type }}</strong>
              <p>{{ event.note }}</p>
              <small>{{ formatDate(event.created_at) }}</small>
            </article>
          </details>

          <details class="detail-section">
            <summary>MVP 與任務輸出</summary>
            <div class="status-actions">
              <button type="button" @click="loadMvpDraft">產生 MVP 草稿</button>
              <button type="button" @click="exportTaskPackage" :disabled="exporting">{{ exporting ? '匯出中...' : '匯出 Prototype 任務包' }}</button>
              <button type="button" class="ghost" @click="activeTab='export'; loadMvpDraft()">查看 MVP 匯出頁</button>
              <button type="button" class="ghost" @click="loadEvolutionDashboard(true)">查看演化紀錄</button>
            </div>
          </details>

          <details class="detail-section danger-detail">
            <summary>狀態流轉與墳場</summary>
            <div class="status-actions">
              <button type="button" @click="setIdeaStatus(selectedIdea, 'saved')">收藏</button>
              <button type="button" @click="setIdeaStatus(selectedIdea, 'deep_dive')">深入研究</button>
              <button type="button" @click="setIdeaStatus(selectedIdea, 'mvp_draft')">MVP</button>
              <button type="button" @click="setIdeaStatus(selectedIdea, 'prototype_ready')">可做 Prototype</button>
              <button type="button" @click="setIdeaStatus(selectedIdea, 'prototype')">Prototype 進行中</button>
            </div>
            <label>淘汰原因<textarea v-model="graveyardForm.rejection_reason" rows="3" placeholder="例如：太像 SaaS、太像 prompt wrapper、沒有真實痛點..." /></label>
            <label>復活條件<textarea v-model="graveyardForm.revival_condition" rows="3" placeholder="例如：未來出現新的技術條件、資料來源或自動化能力" /></label>
            <label>狀態備註<textarea v-model="graveyardForm.status_note" rows="2" /></label>
            <div class="status-actions danger-zone">
              <button type="button" @click="saveGraveyardNote">儲存備註</button>
              <button type="button" @click="sendToGraveyard('rejected')">標記淘汰</button>
              <button type="button" @click="sendToGraveyard('dead')">送入墳場</button>
            </div>
          </details>
        </aside>
      </section>

      <section v-if="activeTab === 'reviews'" class="reviews-layout">
        <div class="card">
          <h3>反合理審查中心</h3>
          <p class="muted">這裡會集中顯示審查結果、商業味警告與改名建議，幫你把太普通的方向淘汰掉。</p>
          <div v-if="!selectedIdea" class="empty">請先在題目看板選一個題目。</div>
          <template v-else>
            <div class="mini-id">{{ selectedIdea.id }}</div>
            <h2>{{ selectedIdea.name }}</h2>
            <p class="one-liner">{{ selectedIdea.one_liner }}</p>
            <div class="status-actions">
              <button type="button" @click="runReview" :disabled="reviewing">{{ reviewing ? '審查中...' : '執行反合理審查' }}</button>
              <button type="button" @click="refreshIdeaScores">重新計分</button>
              <button type="button" @click="loadRenameSuggestions">重新產生改名建議</button>
            </div>
          </template>
        </div>

        <div class="card" v-if="selectedIdea">
          <h3>十分向度分數</h3>
          <div class="score-grid large">
            <div v-for="item in scoreEntries(selectedIdea)" :key="item.key" class="score-cell">
              <span>{{ item.label }}</span>
              <strong>{{ item.value || '-' }}</strong>
            </div>
          </div>
        </div>

        <div class="card" v-if="selectedIdea">
          <h3>商業味濃度</h3>
          <div v-if="commercialSmell">
            <div class="stat-row"><span>嚴重程度</span><strong>{{ commercialSmell.severity }}/10</strong></div>
            <div v-if="commercialSmell.flags?.length" class="chips danger-chips">
              <span v-for="flag in commercialSmell.flags" :key="flag">{{ flagLabel(flag) }}</span>
            </div>
            <p v-else class="muted">目前沒有額外的商業味警告。</p>
          </div>
        </div>

        <div class="card" v-if="selectedIdea">
          <h3>改名建議</h3>
          <p class="muted">如果原題名太像一般產品，這裡會提供更有記憶點的命名方向。</p>
          <div v-if="!renameSuggestions.length" class="empty">目前還沒有改名建議，先跑一次審查或改名分析。</div>
          <div class="rename-list">
            <button type="button" v-for="name in renameSuggestions" :key="name" class="name-chip" @click="applyRenameSuggestion(name)">{{ name }}</button>
          </div>
        </div>

        <div class="card wide" v-if="selectedIdea">
          <h3>審查紀錄</h3>
          <div v-if="!selectedReviews.length" class="empty">目前還沒有審查紀錄。</div>
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
              <button type="button" v-for="name in review.suggestions" :key="name" class="name-chip" @click="applyRenameSuggestion(name)">{{ name }}</button>
            </div>
          </article>
        </div>
      </section>



      <section v-if="activeTab === 'export'" class="grid two">
        <div class="card wide">
          <h3>MVP 草稿與任務輸出</h3>
          <p class="muted">把已選題目壓成 MVP 草稿，再匯出成可交給後續原型工作的任務包。</p>
          <div v-if="!selectedIdea" class="empty">目前沒有選中的題目。</div>
          <template v-else>
            <div class="mini-id">{{ selectedIdea.id }}</div>
            <h2>{{ selectedIdea.name }}</h2>
            <p class="one-liner">{{ selectedIdea.one_liner }}</p>
            <div class="status-actions">
              <button @click="loadMvpDraft">產生 MVP 草稿</button>
              <button @click="exportTaskPackage" :disabled="exporting">{{ exporting ? '匯出中...' : '匯出 Prototype 任務包' }}</button>
            </div>
          </template>
        </div>

        <div class="card wide" v-if="mvpDraft">
          <h3>MVP 草稿</h3>
          <pre class="markdown-preview">{{ mvpDraft.markdown }}</pre>
        </div>

        <div class="card wide" v-if="selectedIdea">
          <h3>匯出紀錄</h3>
          <div v-if="!selectedExports.length" class="empty">目前還沒有匯出紀錄。</div>
          <article v-for="item in selectedExports" :key="item.id" class="review-card">
            <div class="review-head"><strong>{{ item.export_type }}</strong><span>{{ formatDate(item.created_at) }}</span></div>
            <p>{{ item.path }}</p>
          </article>
        </div>
      </section>



      <section v-if="activeTab === 'prototype'" class="grid two">
        <div class="card wide">
          <h3>Prototype Workspace</h3>
          <p class="muted">為題目建立專屬 workspace，集中放置 prompts、runs、logs 與原型紀錄，方便後續實作。</p>
          <div v-if="!selectedIdea" class="empty">請先在題目看板選一個題目。</div>
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
          <label>標題<input v-model="workspaceForm.title" placeholder="例如：第一版 prototype workspace" /></label>
          <label>說明<textarea v-model="workspaceForm.notes" rows="3" placeholder="補充這個 prototype workspace 的目的與假設" /></label>
          <label class="checkbox-inline"><input v-model="workspaceForm.overwrite" type="checkbox" /> 若已存在同名內容則覆寫 docs / prompts</label>
          <button type="submit" :disabled="creatingWorkspace">{{ creatingWorkspace ? '建立中...' : '建立 Prototype Workspace' }}</button>
        </form>

        <div class="card" v-if="selectedIdea">
          <h3>Workspace 清單</h3>
          <div v-if="!prototypeWorkspaces.length" class="empty">目前還沒有 workspace。</div>
          <article v-for="workspace in prototypeWorkspaces" :key="workspace.id" class="review-card">
            <div class="review-head"><strong>{{ workspace.title }}</strong><span>{{ workspace.worker }}</span></div>
            <p>{{ workspace.directory }}</p>
            <small>{{ formatDate(workspace.created_at) }}</small>
            <div class="status-actions">
              <button class="ghost small" @click="runForm.workspace_id = workspace.id">指定給新 Run</button>
            </div>
          </article>
        </div>

        <form class="card form" v-if="selectedIdea" @submit.prevent="createPrototypeRun">
          <h3>新增 Prototype Run</h3>
          <label>Workspace
            <select v-model="runForm.workspace_id">
              <option value="">請選擇 workspace</option>
              <option v-for="workspace in prototypeWorkspaces" :key="workspace.id" :value="workspace.id">{{ workspace.title }} · {{ workspace.worker }}</option>
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
          <label>變更檔案（以逗號分隔）<textarea v-model="runForm.changed_files_text" rows="3" /></label>
          <label>測試指令（以逗號分隔）<textarea v-model="runForm.test_commands_text" rows="3" /></label>
          <label>結果<textarea v-model="runForm.result" rows="3" /></label>
          <label>下一步<textarea v-model="runForm.next_step" rows="2" /></label>
          <button type="submit" :disabled="creatingRun">{{ creatingRun ? '建立中...' : '新增 Prototype Run' }}</button>
        </form>

        <div class="card wide" v-if="selectedIdea">
          <h3>Prototype Run Ledger</h3>
          <div v-if="!prototypeRuns.length" class="empty">目前還沒有 prototype run。</div>
          <article v-for="run in prototypeRuns" :key="run.id" class="review-card">
            <div class="review-head"><strong>{{ run.title }}</strong><span>{{ run.worker }} / {{ run.status }}</span></div>
            <p>{{ run.summary || run.goal || '尚未填寫摘要' }}</p>
            <div v-if="run.changed_files?.length" class="chips"><span v-for="file in run.changed_files" :key="file">{{ file }}</span></div>
            <small v-if="run.report_path">Run report：{{ run.report_path }}</small>
            <small>{{ formatDate(run.created_at) }}</small>
          </article>
        </div>
      </section>


      <section v-if="activeTab === 'repoexp'" class="grid two">
        <div class="card wide">
          <h3>Repo Setup / Build / Test 探針</h3>
          <p class="muted">針對外部 repo 先做安全探測，預設使用 inspect_only，幫你整理 setup / build / test 相關資訊。</p>
          <div v-if="!selectedIdea" class="empty">請先在題目看板選一個題目。</div>
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
                <option value="inspect_only">inspect_only：只分析結構與設定</option>
                <option value="local_dry_run">local_dry_run：模擬本地流程，不執行危險步驟</option>
                <option value="local_execute">local_execute：在本地 VM 實際執行</option>
              </select>
            </label>
            <label>Timeout 秒數<input v-model="repoExperimentForm.timeout_seconds" type="number" min="30" max="1800" /></label>
          </div>
          <label>說明<textarea v-model="repoExperimentForm.notes" rows="3" placeholder="補充這次 repo probe 想驗證的假設，例如 setup / build / test 成功率" /></label>
          <button type="submit" :disabled="creatingRepoExperiment">{{ creatingRepoExperiment ? '建立中...' : '建立 Repo Probe' }}</button>
        </form>

        <div class="card wide" v-if="selectedIdea">
          <h3>Repo Probe 紀錄</h3>
          <div v-if="!repoExperiments.length" class="empty">目前還沒有 repo probe 紀錄。</div>
          <article v-for="exp in repoExperiments" :key="exp.id" class="review-card">
            <div class="review-head"><strong>{{ exp.title }}</strong><span>{{ exp.status }} / {{ exp.run_mode }}</span></div>
            <p><strong>{{ exp.repo_url }}</strong></p>
            <p>{{ exp.summary || '尚未填寫摘要' }}</p>
            <div v-if="exp.detected_stack?.length" class="chips"><span v-for="stack in exp.detected_stack" :key="stack">{{ stack }}</span></div>
            <h4>建議 setup 指令</h4>
            <ul><li v-for="cmd in exp.setup_commands" :key="cmd"><code>{{ cmd }}</code></li></ul>
            <h4>建議 build / test 指令</h4>
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
          <h3>題目演化與合併</h3>
          <p class="muted">查看題目之間的相似性、家族關係、合併方向與復活候選，幫你整理題目庫的演化脈絡。</p>
          <div class="status-actions">
            <button @click="loadEvolutionDashboard(true)">重新整理演化資料</button>
          </div>
        </div>

        <div class="card wide">
          <h3>合併候選</h3>
          <div v-if="!ideaFamilies.length" class="empty">目前沒有可合併的題目家族。</div>
          <article v-for="family in ideaFamilies" :key="family.family_name + family.idea_ids.join('-')" class="family-card">
            <div class="review-head"><strong>{{ family.family_name }}</strong><span>{{ family.idea_ids.length }} 題</span></div>
            <p>{{ family.reason }}</p>
            <div class="chips"><span v-for="kw in family.shared_keywords" :key="kw">{{ kw }}</span></div>
            <h4>相關題目</h4>
            <ul>
              <li v-for="idea in family.ideas" :key="idea.id"><strong>{{ idea.name }}</strong> · {{ idea.one_liner }}</li>
            </ul>
            <h4>合併方式</h4>
            <div class="rename-list">
              <button v-for="option in family.merge_options" :key="option.name" class="name-chip" @click="mergeFamily(family, option)" :disabled="merging">
                {{ option.style }}：{{ option.name }}
              </button>
            </div>
          </article>
        </div>

        <div class="card wide">
          <h3>復活候選</h3>
          <p class="muted">這些是可能因為新條件出現而值得重新檢查的題目。</p>
          <div v-if="!reviveSuggestions.length" class="empty">目前沒有復活候選。</div>
          <article v-for="item in reviveSuggestions" :key="item.idea.id" class="grave-card">
            <div class="review-head"><strong>{{ item.idea.name }}</strong><span>復活分數 {{ item.score }}/10</span></div>
            <p>{{ item.idea.one_liner }}</p>
            <small v-for="reason in item.reasons" :key="reason">{{ reason }}</small>
            <div class="status-actions">
              <button @click="reviveIdea(item.idea)">直接復活</button>
              <button @click="moveBackToBoard(item.idea, 'saved')">移回收藏</button>
            </div>
          </article>
        </div>

        <div class="card wide" v-if="selectedIdea">
          <h3>目前題目的相似與事件</h3>
          <div class="mini-id">{{ selectedIdea.id }}</div>
          <h2>{{ selectedIdea.name }}</h2>
          <div v-if="!similarItems.length" class="empty">目前沒有相似題目。</div>
          <article v-for="item in similarItems" :key="item.idea.id" class="review-card">
            <div class="review-head"><strong>{{ item.idea.name }}</strong><span>相似度 {{ Math.round(item.score * 100) }}%</span></div>
            <p>{{ item.idea.one_liner }}</p>
            <small>{{ item.reasons.join(' / ') }}</small>
          </article>
          <h4>事件紀錄</h4>
          <div v-if="!ideaEvents.length" class="empty">目前還沒有事件紀錄。</div>
          <article v-for="event in ideaEvents" :key="event.id" class="review-card">
            <div class="review-head"><strong>{{ event.title || event.event_type }}</strong><span>{{ formatDate(event.created_at) }}</span></div>
            <p>{{ event.note }}</p>
          </article>
        </div>
      </section>


      <section v-if="activeTab === 'taste'" class="grid two">
        <div class="card">
          <h3>個人品味學習</h3>
          <p class="muted">根據你對題目的偏好回饋，逐步整理出比較偏愛的關鍵字、切角與分數傾向。</p>
          <button @click="loadTasteDashboard(true)">重新整理品味資料</button>
          <div v-if="!tasteProfile" class="empty">目前還沒有品味資料。</div>
          <template v-else>
            <p class="one-liner">{{ tasteProfile.summary }}</p>
            <div class="stat-row"><span>甇??憿</span><strong>{{ tasteProfile.liked_count }}</strong></div>
            <div class="stat-row"><span>鞎?憿</span><strong>{{ tasteProfile.disliked_count }}</strong></div>
            <h4>偏好關鍵字</h4>
            <div class="chips"><span v-for="kw in tasteProfile.preferred_keywords" :key="kw">{{ kw }}</span></div>
            <h4>不喜歡關鍵字</h4>
            <div class="chips danger-chips"><span v-for="kw in tasteProfile.disliked_keywords" :key="kw">{{ kw }}</span></div>
            <h4>高分題目的平均分數</h4>
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
          <h3>品味推薦排序</h3>
          <div v-if="!tasteRecommendations.length" class="empty">目前還沒有推薦結果。</div>
          <button v-for="item in tasteRecommendations" :key="item.idea.id" class="list-item" @click="selectIdea(item.idea); activeTab='ideas'">
            <strong>{{ item.idea.name }} 繚 {{ item.fit.score }}/100</strong>
            <span>{{ item.fit.verdict }}</span>
            <em>{{ item.fit.reasons?.slice(0, 2).join(' / ') }}</em>
          </button>
        </div>
      </section>

      <section v-if="activeTab === 'scheduler'" class="grid two">
        <div class="card wide">
          <div class="review-head">
            <strong>排程服務概況</strong>
            <button class="ghost small" @click="loadSchedulerDashboard(true)" :disabled="schedulerLoading">
              {{ schedulerLoading ? '載入中...' : '重新整理排程' }}
            </button>
          </div>
          <div v-if="!schedulerStatus" class="empty">目前無法讀取排程狀態，請先確認 backend 已啟動。</div>
          <div v-else class="settings-list">
            <div class="stat-row"><span>服務狀態</span><strong>{{ schedulerStatus.status }}</strong></div>
            <div class="stat-row"><span>目前工作</span><strong>{{ schedulerStatus.current_job_key || '目前沒有執行中的工作' }}</strong></div>
            <div class="stat-row"><span>Tick 秒數</span><strong>{{ schedulerStatus.tick_seconds }} 秒</strong></div>
            <div class="stat-row"><span>最後更新</span><strong>{{ formatDate(schedulerStatus.last_tick_at) || '尚未更新' }}</strong></div>
            <div class="stat-row"><span>時區</span><strong>{{ schedulerStatus.timezone }}</strong></div>
          </div>
          <p class="muted" v-if="schedulerStatus">{{ schedulerStatus.backend_note }}</p>
        </div>

        <div class="card wide">
          <h3>排程工作清單</h3>
          <div v-if="!schedulerJobs.length" class="empty">目前沒有排程工作。</div>
          <article v-for="job in schedulerJobs" :key="job.id" class="scheduler-job-card">
            <div class="review-head">
              <strong>{{ job.name }}</strong>
              <span>{{ job.enabled ? '已啟用' : '已停用' }}</span>
            </div>
            <p>{{ job.description }}</p>
            <div class="collector-meta">
               <span>頻率：{{ formatSchedule(job) }}</span>
               <span>下次執行：{{ formatDate(job.next_run_at) || '尚未排定' }}</span>
               <span>上次執行：{{ formatDate(job.last_run_at) || '尚未執行' }}</span>
               <span>上次狀態：{{ schedulerStatusLabel(job.last_status) }}</span>
            </div>
            <p v-if="job.last_message" class="muted">{{ job.last_message }}</p>
            <div class="status-actions">
              <button @click="runSchedulerJobNow(job)" :disabled="schedulerMutatingId === job.id">立即執行</button>
              <button class="ghost" v-if="job.enabled" @click="toggleSchedulerJob(job, false)" :disabled="schedulerMutatingId === job.id">停用</button>
              <button class="ghost" v-else @click="toggleSchedulerJob(job, true)" :disabled="schedulerMutatingId === job.id">啟用</button>
            </div>
          </article>
        </div>

        <div class="card">
          <h3>排程執行紀錄</h3>
          <div v-if="!schedulerRuns.length" class="empty">目前還沒有排程執行紀錄。</div>
          <article v-for="run in schedulerRuns" :key="run.id" class="review-card">
            <div class="review-head">
              <strong>{{ run.job_key }}</strong>
              <span>{{ schedulerStatusLabel(run.status) }}</span>
            </div>
            <p>開始時間：{{ formatDate(run.started_at) || '未設定' }}</p>
            <p>耗時：{{ run.duration_seconds || 0 }} 秒</p>
            <p>{{ run.summary || '目前沒有摘要' }}</p>
            <p v-if="run.warning" class="muted">警告：{{ run.warning }}</p>
            <p v-if="run.error" class="muted">錯誤：{{ run.error }}</p>
          </article>
        </div>

        <div class="card">
          <h3>使用提醒</h3>
          <ul class="settings-hints">
            <li>排程依賴 backend 常駐運行。</li>
            <li>Repo Probe 預設保持在安全的 inspect_only 模式。</li>
            <li>Codex / OpenCode 相關工作建議先確認 workspace 已建立。</li>
            <li>若 Local GPT 離線，排程可能退回模板或略過相關步驟。</li>
            <li>變更排程前，先確認最近一次 shell 執行結果正常。</li>
          </ul>
        </div>
      </section>

      <section v-if="activeTab === 'settings'" class="grid two settings-grid">
        <div class="card wide">
          <div class="review-head">
            <strong>系統診斷總覽</strong>
            <button class="ghost small" @click="loadSettingsDiagnostics" :disabled="settingsLoading">
              {{ settingsLoading ? '載入中...' : '重新整理診斷' }}
            </button>
          </div>
          <p class="muted">集中檢查 backend、Local GPT、排程與資料路徑狀態，方便快速確認目前環境是否正常。</p>
          <div v-if="!settingsDiagnostics && settingsLoading" class="empty">診斷載入中...</div>
          <div v-else-if="!settingsDiagnostics" class="empty">目前無法取得診斷資料，請先確認 backend 已啟動。</div>
        </div>

        <div class="card" v-if="settingsDiagnostics">
          <h3>應用程式資訊</h3>
          <div class="settings-list">
            <div class="stat-row"><span>名稱</span><strong>{{ settingsDiagnostics.app.name }}</strong></div>
            <div class="stat-row"><span>目前階段</span><strong>{{ settingsDiagnostics.app.phase }}</strong></div>
            <div class="stat-row"><span>模式</span><strong>{{ settingsDiagnostics.app.mode }}</strong></div>
            <div class="stat-row"><span>Backend URL</span><strong>{{ settingsDiagnostics.backend.base_url_hint }}</strong></div>
            <div class="stat-row"><span>Python 目標</span><strong>{{ settingsDiagnostics.backend.python_target }}</strong></div>
          </div>
        </div>

        <div class="card" v-if="settingsDiagnostics">
          <h3>Local GPT 設定</h3>
          <div class="settings-list">
            <div class="stat-row"><span>Base URL</span><strong>{{ settingsDiagnostics.local_gpt.base_url }}</strong></div>
            <div class="stat-row"><span>模型</span><strong>{{ settingsDiagnostics.local_gpt.model }}</strong></div>
            <div class="stat-row"><span>Timeout</span><strong>{{ settingsDiagnostics.local_gpt.timeout_seconds }} 秒</strong></div>
            <div class="stat-row"><span>健康狀態</span><strong>{{ settingsDiagnostics.local_gpt.health }}</strong></div>
            <div class="stat-row"><span>API Key 已設定</span><strong>{{ settingsDiagnostics.local_gpt.api_key_configured ? '是' : '否' }}</strong></div>
            <div class="stat-row"><span>Fallback 模式</span><strong>{{ settingsDiagnostics.local_gpt.fallback }}</strong></div>
          </div>
          <p class="settings-note">如果沒有 API Key 或健康檢查失敗，怪題產生器會依設定退回模板流程。</p>
          <p class="muted" v-if="settingsDiagnostics.local_gpt.detail">{{ settingsDiagnostics.local_gpt.detail }}</p>
          <div class="status-actions">
            <button @click="loadLlmHealth">重新檢查 Local GPT</button>
            <button class="ghost" @click="loadSettingsDiagnostics">重新整理 LLM 診斷</button>
          </div>
          <p class="muted" v-if="settingsDiagnostics.local_gpt.health === 'offline'">Local GPT 離線時，系統會優先改用模板產生，避免整個流程卡住。</p>
        </div>

        <div class="card" v-if="settingsDiagnostics">
          <h3>排程設定</h3>
          <div class="settings-list">
            <div class="stat-row"><span>排程模式</span><strong>{{ settingsDiagnostics.scheduler.mode }}</strong></div>
            <div class="stat-row"><span>排程狀態</span><strong>{{ settingsDiagnostics.scheduler.status }}</strong></div>
          </div>
          <p class="settings-note">{{ settingsDiagnostics.scheduler.note }}</p>
          <div class="status-actions">
            <button @click="activeTab = 'scheduler'">前往排程頁</button>
          </div>
        </div>

        <div class="card wide" v-if="settingsDiagnostics">
          <h3>資料輸出與儲存位置</h3>
          <div class="settings-stack">
            <div class="review-mini">
              <strong>data/</strong>
              <p>{{ settingsDiagnostics.paths.data.purpose }}</p>
              <small>{{ settingsDiagnostics.paths.data.path }}</small>
            </div>
            <div class="review-mini">
              <strong>exports/ideas/</strong>
              <p>{{ settingsDiagnostics.paths.exports.purpose }}</p>
              <small>{{ settingsDiagnostics.paths.exports.path }}</small>
            </div>
            <div class="review-mini">
              <strong>prototypes/</strong>
              <p>{{ settingsDiagnostics.paths.prototypes.purpose }}</p>
              <small>{{ settingsDiagnostics.paths.prototypes.path }}</small>
            </div>
            <div class="review-mini">
              <strong>experiments/repo-probes/</strong>
              <p>{{ settingsDiagnostics.paths.repo_experiments.purpose }}</p>
              <small>{{ settingsDiagnostics.paths.repo_experiments.path }}</small>
            </div>
            <div class="review-mini">
              <strong>logs/</strong>
              <p>{{ settingsDiagnostics.paths.logs.purpose }}</p>
              <small>{{ settingsDiagnostics.paths.logs.path }}</small>
            </div>
          </div>
        </div>

        <div class="card" v-if="settingsDiagnostics">
          <h3>Repo Probe 安全設定</h3>
          <div class="settings-list">
            <div class="stat-row"><span>預設模式</span><strong>{{ settingsDiagnostics.repo_probe.default_mode }}</strong></div>
            <div class="stat-row"><span>Windows local_execute</span><strong>{{ settingsDiagnostics.repo_probe.local_execute_windows }}</strong></div>
          </div>
          <p class="settings-note">{{ settingsDiagnostics.repo_probe.safety_note }}</p>
        </div>

        <div class="card" v-if="settingsDiagnostics">
          <h3>Codex / OpenCode</h3>
          <div class="settings-list">
            <div class="stat-row"><span>運作模式</span><strong>{{ settingsDiagnostics.codex_opencode.mode }}</strong></div>
            <div class="stat-row"><span>自動化</span><strong>{{ settingsDiagnostics.codex_opencode.automation }}</strong></div>
          </div>
          <p class="settings-note">{{ settingsDiagnostics.codex_opencode.notes }}</p>
        </div>

        <div class="card" v-if="settingsDiagnostics">
          <h3>備份建議</h3>
          <p class="settings-note">建議定期備份 SQLite、prototype workspace 與 repo probe 相關輸出。</p>
          <div class="review-mini">
            <strong>SQLite 資料庫</strong>
            <p>{{ settingsDiagnostics.backup.sqlite_db }}</p>
          </div>
          <ul>
            <li v-for="item in settingsDiagnostics.backup.recommended_items" :key="item"><code>{{ item }}</code></li>
          </ul>
          <p class="muted">{{ settingsDiagnostics.backup.note }}</p>
        </div>

        <div class="card" v-if="settingsDiagnostics">
          <h3>建議環境變數</h3>
          <p class="settings-note">這些環境變數有助於設定 Local GPT、Repo Probe 與其他本地流程。</p>
          <ul>
            <li v-for="item in settingsDiagnostics.environment_variables" :key="item"><code>{{ item }}</code></li>
          </ul>
        </div>
      </section>

      <section v-if="activeTab === 'graveyard'" class="grid two">
        <div class="card wide">
          <h3>憓喳</h3>
          <p class="muted">這裡存放被淘汰或暫時放棄的題目，也會保留之後可能復活的條件與原因。</p>
        </div>

        <div class="card">
          <h3>復活候選</h3>
          <div v-if="!reviveIdeas.length" class="empty">目前沒有復活候選。</div>
          <article v-for="idea in reviveIdeas" :key="idea.id" class="grave-card">
            <h4>{{ idea.name }}</h4>
            <p>{{ idea.one_liner }}</p>
            <small>復活條件：{{ idea.revival_condition || '尚未設定' }}</small>
            <div class="status-actions"><button @click="moveBackToBoard(idea, 'saved')">移回收藏</button></div>
        </article>
        </div>

        <div class="card">
          <h3>墳場清單</h3>
          <div v-if="!graveyardIdeas.length" class="empty">墳場目前是空的。</div>
          <article v-for="idea in graveyardIdeas" :key="idea.id" class="grave-card">
            <div class="mini-id">{{ idea.id }}</div>
            <h4>{{ idea.name }}</h4>
            <p>{{ idea.one_liner }}</p>
            <small>淘汰原因：{{ idea.rejection_reason || '尚未填寫' }}</small>
            <small>復活條件：{{ idea.revival_condition || '尚未填寫' }}</small>
            <div class="status-actions">
              <button @click="selectIdea(idea); activeTab='ideas'">查看</button>
              <button @click="reviveIdea(idea)">直接復活</button>
              <button @click="moveBackToBoard(idea, 'saved')">移回收藏</button>
            </div>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

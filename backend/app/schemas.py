from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

IdeaStatus = Literal[
    "new",
    "saved",
    "rejected",
    "deep_dive",
    "mvp_draft",
    "prototype_ready",
    "prototype",
    "dead",
    "revive_candidate",
    "merged",
]


class SignalCreate(BaseModel):
    title: str = Field(min_length=1)
    source_type: str = "manual"
    source_url: str | None = None
    summary: str = ""
    raw_text: str = ""
    tags: list[str] = Field(default_factory=list)
    weirdness: int = Field(default=5, ge=1, le=10)
    pain_signal: int = Field(default=5, ge=1, le=10)
    source_category: str = ""
    quality_score: int | None = Field(default=None, ge=0, le=100)
    quality_reason: str = ""
    fingerprint: str = ""
    collected_at: str = ""


class Signal(SignalCreate):
    id: str
    created_at: str
    updated_at: str


class IdeaCreate(BaseModel):
    name: str = Field(min_length=1)
    one_liner: str = ""
    weird_angle: str = ""
    real_pain: str = ""
    first_screen: str = ""
    mvp: str = ""
    status: IdeaStatus = "new"
    source_signal_ids: list[str] = Field(default_factory=list)
    scores: dict[str, Any] = Field(default_factory=dict)
    status_note: str = ""
    rejection_reason: str = ""
    revival_condition: str = ""


class IdeaUpdate(BaseModel):
    name: str | None = None
    one_liner: str | None = None
    weird_angle: str | None = None
    real_pain: str | None = None
    first_screen: str | None = None
    mvp: str | None = None
    status: IdeaStatus | None = None
    source_signal_ids: list[str] | None = None
    scores: dict[str, Any] | None = None
    status_note: str | None = None
    rejection_reason: str | None = None
    revival_condition: str | None = None


class Idea(IdeaCreate):
    id: str
    created_at: str
    updated_at: str


class IdeaGenerateRequest(BaseModel):
    raw_text: str = ""
    signal_ids: list[str] = Field(default_factory=list)
    count: int = Field(default=10, ge=1, le=10)
    save: bool = True
    mode: Literal["heuristic", "llm"] = "heuristic"
    provider: Literal["local_gpt"] | None = None
    debug: bool = False


class GeneratedIdea(IdeaCreate):
    generator_note: str = ""
    source_summary: str = ""
    target_user: str = ""
    anti_saas_notes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class PipelineStageSummary(BaseModel):
    stage: str
    title: str
    summary: str
    warning: str | None = None


class IdeaGenerateResponse(BaseModel):
    ideas: list[Idea | GeneratedIdea]
    saved: bool
    source_signal_ids: list[str] = Field(default_factory=list)
    provider_used: str = "heuristic"
    warnings: list[str] = Field(default_factory=list)
    pipeline_stages: list[PipelineStageSummary] = Field(default_factory=list)



class ReviewCreate(BaseModel):
    idea_id: str
    review_type: str = "anti_rational"
    passes: bool = False
    flags: list[str] = Field(default_factory=list)
    comment: str = ""
    suggestions: list[str] = Field(default_factory=list)


class Review(ReviewCreate):
    id: str
    created_at: str


class AntiRationalReviewResponse(BaseModel):
    review: Review
    idea: Idea
    scores: dict[str, Any] = Field(default_factory=dict)
    flags: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class RenameSuggestionsResponse(BaseModel):
    idea_id: str
    suggestions: list[str] = Field(default_factory=list)


class ScoreRefreshResponse(BaseModel):
    idea: Idea
    scores: dict[str, Any] = Field(default_factory=dict)


class CommercialSmellResponse(BaseModel):
    idea_id: str
    flags: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    severity: int = 0


class ExperimentCreate(BaseModel):
    idea_id: str
    title: str = Field(min_length=1)
    goal: str = ""
    method: str = ""
    success_criteria: str = ""
    result_status: str = "pending"
    result_summary: str = ""


class Experiment(ExperimentCreate):
    id: str
    created_at: str
    updated_at: str


class ExportRecord(BaseModel):
    id: str
    idea_id: str
    export_type: str
    path: str
    created_at: str


class MvpDraftResponse(BaseModel):
    idea_id: str
    name: str
    markdown: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    do_items: list[str] = Field(default_factory=list)
    dont_items: list[str] = Field(default_factory=list)
    tasks: list[str] = Field(default_factory=list)
    acceptance: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class TaskPackageExportResponse(BaseModel):
    idea_id: str
    directory: str
    files: list[str] = Field(default_factory=list)
    export_record: ExportRecord


class SourceCollectorInfo(BaseModel):
    key: str
    label: str
    description: str = ""
    category: str = ""
    enabled: bool = True
    requires_network: bool = True
    requires_api_key: bool = False
    risk_level: Literal["low", "medium", "high"] = "low"
    default_query_hint: str = ""
    notes: str = ""


class SignalCollectRequest(BaseModel):
    query: str = "AI developer tools agent repo setup build test"
    sources: list[str] = Field(default_factory=lambda: ["github", "hacker_news", "arxiv"])
    limit_per_source: int = Field(default=5, ge=1, le=10)
    save: bool = True
    feed_urls: list[str] = Field(default_factory=list)
    custom_urls: list[str] = Field(default_factory=list)


class SignalCollectStats(BaseModel):
    collected_count: int = 0
    new_count: int = 0
    duplicate_count: int = 0
    failed_count: int = 0


class SignalCollectResponse(BaseModel):
    signals: list[Signal | SignalCreate]
    saved: bool
    errors: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duplicate_signals: list[Signal | SignalCreate] = Field(default_factory=list)
    stats: SignalCollectStats = Field(default_factory=SignalCollectStats)


class IdeaEventCreate(BaseModel):
    idea_id: str
    event_type: str
    title: str = ""
    note: str = ""
    related_idea_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IdeaEvent(IdeaEventCreate):
    id: str
    created_at: str


class SimilarIdeaItem(BaseModel):
    idea: Idea
    score: float
    reasons: list[str] = Field(default_factory=list)


class SimilarIdeasResponse(BaseModel):
    idea_id: str
    items: list[SimilarIdeaItem] = Field(default_factory=list)


class MergeOption(BaseModel):
    style: str
    name: str
    description: str = ""


class IdeaFamilySuggestion(BaseModel):
    family_name: str
    idea_ids: list[str] = Field(default_factory=list)
    ideas: list[Idea] = Field(default_factory=list)
    shared_keywords: list[str] = Field(default_factory=list)
    merge_options: list[MergeOption] = Field(default_factory=list)
    reason: str = ""


class IdeaFamiliesResponse(BaseModel):
    families: list[IdeaFamilySuggestion] = Field(default_factory=list)


class ReviveSuggestionItem(BaseModel):
    idea: Idea
    score: int
    reasons: list[str] = Field(default_factory=list)


class ReviveSuggestionsResponse(BaseModel):
    items: list[ReviveSuggestionItem] = Field(default_factory=list)


class MergeIdeasRequest(BaseModel):
    idea_ids: list[str] = Field(min_length=2)
    name: str | None = None
    mark_sources_merged: bool = True


class MergeIdeasResponse(BaseModel):
    merged_idea: Idea
    source_ideas: list[Idea] = Field(default_factory=list)
    events: list[IdeaEvent] = Field(default_factory=list)

PrototypeWorker = Literal["manual", "codex", "opencode"]
PrototypeRunStatus = Literal["planned", "running", "passed", "failed", "blocked", "needs_rethink"]


class PrototypeWorkspaceCreate(BaseModel):
    worker: PrototypeWorker = "manual"
    title: str = ""
    notes: str = ""
    overwrite: bool = False


class PrototypeWorkspace(BaseModel):
    id: str
    idea_id: str
    title: str = ""
    worker: str = "manual"
    directory: str
    status: str = "created"
    notes: str = ""
    created_at: str
    updated_at: str


class PrototypeWorkspaceCreateResponse(BaseModel):
    workspace: PrototypeWorkspace
    idea: Idea
    directory: str
    written_files: list[str] = Field(default_factory=list)
    skipped_files: list[str] = Field(default_factory=list)


class PrototypeRunCreate(BaseModel):
    idea_id: str
    workspace_id: str | None = None
    title: str = "Prototype Run"
    worker: PrototypeWorker = "manual"
    status: PrototypeRunStatus = "planned"
    goal: str = ""
    summary: str = ""
    changed_files: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    result: str = ""
    next_step: str = ""
    report_path: str = ""


class PrototypeRunUpdate(BaseModel):
    title: str | None = None
    worker: PrototypeWorker | None = None
    status: PrototypeRunStatus | None = None
    goal: str | None = None
    summary: str | None = None
    changed_files: list[str] | None = None
    test_commands: list[str] | None = None
    result: str | None = None
    next_step: str | None = None
    report_path: str | None = None


class PrototypeRun(BaseModel):
    id: str
    idea_id: str
    workspace_id: str | None = None
    title: str = ""
    worker: str = "manual"
    status: str = "planned"
    goal: str = ""
    summary: str = ""
    changed_files: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    result: str = ""
    next_step: str = ""
    report_path: str = ""
    created_at: str
    updated_at: str


class PrototypeRunCreateResponse(BaseModel):
    run: PrototypeRun
    report_path: str | None = None
    idea: Idea | None = None

RepoExperimentRunMode = Literal["inspect_only", "local_dry_run", "local_execute"]
RepoExperimentStatus = Literal["planned", "inspected", "planned_commands", "running", "passed", "failed", "blocked"]


class RepoExperimentCreate(BaseModel):
    repo_url: str = Field(min_length=1)
    title: str = "Repo Probe Experiment"
    run_mode: RepoExperimentRunMode = "inspect_only"
    timeout_seconds: int = Field(default=180, ge=30, le=1800)
    notes: str = ""


class RepoExperiment(BaseModel):
    id: str
    idea_id: str
    title: str = ""
    repo_url: str
    run_mode: str = "inspect_only"
    status: str = "planned"
    summary: str = ""
    detected_stack: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    setup_commands: list[str] = Field(default_factory=list)
    build_commands: list[str] = Field(default_factory=list)
    test_commands: list[str] = Field(default_factory=list)
    start_commands: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    report_path: str = ""
    workspace_dir: str = ""
    logs: list[dict[str, Any]] = Field(default_factory=list)
    notes: str = ""
    created_at: str
    updated_at: str


class RepoExperimentCreateResponse(BaseModel):
    experiment: RepoExperiment
    idea: Idea | None = None

TasteAction = Literal["like", "love", "save", "deep_dive", "prototype", "dislike", "reject", "too_boring", "too_saas", "not_for_me"]


class TasteFeedbackCreate(BaseModel):
    idea_id: str
    action: TasteAction = "like"
    weight: int = Field(default=0, ge=-10, le=10)
    note: str = ""


class TasteFeedback(TasteFeedbackCreate):
    id: str
    created_at: str


class TasteProfileResponse(BaseModel):
    summary: str
    liked_count: int = 0
    disliked_count: int = 0
    preferred_keywords: list[str] = Field(default_factory=list)
    disliked_keywords: list[str] = Field(default_factory=list)
    boring_words_seen: dict[str, int] = Field(default_factory=dict)
    average_positive_scores: dict[str, float] = Field(default_factory=dict)
    recommendation_rule: str = ""


class TasteFitResponse(BaseModel):
    idea_id: str
    score: int
    verdict: str
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    profile_summary: str = ""


class TasteRecommendationItem(BaseModel):
    idea: Idea
    fit: TasteFitResponse


class TasteRecommendationsResponse(BaseModel):
    items: list[TasteRecommendationItem] = Field(default_factory=list)


class TasteFeedbackResponse(BaseModel):
    feedback: TasteFeedback
    fit: TasteFitResponse | None = None
    profile: TasteProfileResponse | None = None


class LlmSettingsResponse(BaseModel):
    base_url: str
    model: str
    timeout_seconds: float
    api_key_configured: bool


class LlmHealthResponse(BaseModel):
    base_url: str
    model: str
    timeout_seconds: float
    api_key_configured: bool
    available: bool
    status: str
    detail: str = ""


class DiagnosticsAppInfo(BaseModel):
    name: str
    phase: str
    mode: str


class DiagnosticsBackendInfo(BaseModel):
    status: str
    base_url_hint: str
    python_target: str


class DiagnosticsLocalGptInfo(BaseModel):
    base_url: str
    model: str
    timeout_seconds: float
    api_key_configured: bool
    api_key_visible: bool
    health: str
    detail: str = ""
    fallback: str


class DiagnosticsPathItem(BaseModel):
    path: str
    purpose: str


class DiagnosticsPathsInfo(BaseModel):
    data: DiagnosticsPathItem
    exports: DiagnosticsPathItem
    prototypes: DiagnosticsPathItem
    repo_experiments: DiagnosticsPathItem
    logs: DiagnosticsPathItem
    backup_database: DiagnosticsPathItem


class DiagnosticsRepoProbeInfo(BaseModel):
    default_mode: str
    local_execute_windows: str
    safety_note: str


class DiagnosticsCodexInfo(BaseModel):
    mode: str
    automation: str
    notes: str


class DiagnosticsSchedulerInfo(BaseModel):
    status: str
    mode: str
    note: str


class DiagnosticsBackupInfo(BaseModel):
    sqlite_db: str
    recommended_items: list[str] = Field(default_factory=list)
    note: str


class DiagnosticsResponse(BaseModel):
    app: DiagnosticsAppInfo
    backend: DiagnosticsBackendInfo
    local_gpt: DiagnosticsLocalGptInfo
    paths: DiagnosticsPathsInfo
    repo_probe: DiagnosticsRepoProbeInfo
    codex_opencode: DiagnosticsCodexInfo
    scheduler: DiagnosticsSchedulerInfo
    backup: DiagnosticsBackupInfo
    environment_variables: list[str] = Field(default_factory=list)


class ScheduledJobUpdate(BaseModel):
    enabled: bool | None = None
    interval_minutes: int | None = Field(default=None, ge=5, le=10080)
    time_of_day: str | None = None
    day_of_week: int | None = Field(default=None, ge=0, le=6)


class ScheduledJob(BaseModel):
    id: str
    job_key: str
    name: str
    description: str = ""
    enabled: bool = False
    schedule_type: Literal["daily", "weekly", "interval"] = "daily"
    interval_minutes: int | None = None
    time_of_day: str = ""
    day_of_week: int | None = None
    config_json: dict[str, Any] = Field(default_factory=dict)
    last_run_at: str = ""
    next_run_at: str = ""
    last_status: str = "idle"
    last_message: str = ""
    created_at: str
    updated_at: str


class ScheduledJobRun(BaseModel):
    id: str
    job_id: str
    job_key: str
    status: str
    started_at: str
    finished_at: str = ""
    duration_seconds: float = 0
    summary: str = ""
    warning: str = ""
    error: str = ""
    result_json: dict[str, Any] = Field(default_factory=dict)


class SchedulerStatusResponse(BaseModel):
    status: str
    running: bool
    backend_note: str
    timezone: str
    tick_seconds: int
    current_job_key: str = ""
    last_tick_at: str = ""


class SchedulerJobsResponse(BaseModel):
    jobs: list[ScheduledJob] = Field(default_factory=list)


class SchedulerRunsResponse(BaseModel):
    runs: list[ScheduledJobRun] = Field(default_factory=list)

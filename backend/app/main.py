from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import crud
from .db import init_db
from .generator import generated_idea_payloads
from .reviewer import commercial_smell_report, make_suggestions, review_idea, score_idea
from .mvp import build_mvp_draft, export_task_package
from .prototype import create_prototype_workspace_files, write_run_markdown
from .repo_probe import probe_repo
from .taste import build_taste_profile, create_feedback, recommendations, score_taste_fit
from .collectors import collect_many, collector_infos
from .evolution import build_family_suggestions, similar_ideas, revive_suggestions, build_merged_idea_payload
from .schemas import (
    AntiRationalReviewResponse,
    CommercialSmellResponse,
    ExportRecord,
    SignalCollectRequest,
    SignalCollectResponse,
    SourceCollectorInfo,
    Experiment,
    ExperimentCreate,
    Idea,
    IdeaCreate,
    IdeaGenerateRequest,
    IdeaGenerateResponse,
    IdeaUpdate,
    MvpDraftResponse,
    RenameSuggestionsResponse,
    Review,
    ReviewCreate,
    ScoreRefreshResponse,
    TaskPackageExportResponse,
    Signal,
    SignalCreate,
    IdeaEvent,
    IdeaEventCreate,
    SimilarIdeasResponse,
    IdeaFamiliesResponse,
    ReviveSuggestionsResponse,
    MergeIdeasRequest,
    MergeIdeasResponse,
    PrototypeWorkspaceCreate,
    PrototypeWorkspace,
    PrototypeWorkspaceCreateResponse,
    PrototypeRunCreate,
    PrototypeRunUpdate,
    PrototypeRun,
    PrototypeRunCreateResponse,
    RepoExperimentCreate,
    RepoExperiment,
    RepoExperimentCreateResponse,
    TasteFeedbackCreate,
    TasteFeedbackResponse,
    TasteFitResponse,
    TasteProfileResponse,
    TasteRecommendationsResponse,
)

app = FastAPI(title="怪題研究所 API", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/collectors", response_model=list[SourceCollectorInfo])
def list_collectors() -> list[dict]:
    return collector_infos()


@app.post("/signals/collect", response_model=SignalCollectResponse)
def collect_signals(payload: SignalCollectRequest) -> dict:
    collected, errors = collect_many(
        sources=payload.sources,
        query=payload.query,
        limit_per_source=payload.limit_per_source,
    )

    if not payload.save:
        return {"signals": collected, "saved": False, "errors": errors}

    saved = []
    for item in collected:
        saved.append(crud.create_signal(SignalCreate(**item)))
    return {"signals": saved, "saved": True, "errors": errors}


@app.post("/signals", response_model=Signal)
def create_signal(payload: SignalCreate) -> dict:
    return crud.create_signal(payload)


@app.get("/signals", response_model=list[Signal])
def list_signals() -> list[dict]:
    return crud.list_signals()


@app.get("/signals/{signal_id}", response_model=Signal)
def get_signal(signal_id: str) -> dict:
    try:
        return crud.get_signal(signal_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Signal not found")


@app.post("/ideas", response_model=Idea)
def create_idea(payload: IdeaCreate) -> dict:
    return crud.create_idea(payload)


@app.post("/ideas/generate", response_model=IdeaGenerateResponse)
def generate_ideas(payload: IdeaGenerateRequest) -> dict:
    source_text_parts: list[str] = []
    source_signal_ids: list[str] = []

    for signal_id in payload.signal_ids:
        try:
            signal = crud.get_signal(signal_id)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Signal not found: {signal_id}")
        source_signal_ids.append(signal_id)
        source_text_parts.append(
            "\n".join(
                part
                for part in [signal.get("title", ""), signal.get("summary", ""), signal.get("raw_text", "")]
                if part
            )
        )

    if payload.raw_text.strip():
        source_text_parts.append(payload.raw_text.strip())

    combined_text = "\n\n".join(source_text_parts).strip()
    if not combined_text:
        raise HTTPException(status_code=400, detail="raw_text or signal_ids is required")

    generated = generated_idea_payloads(
        text=combined_text,
        source_signal_ids=source_signal_ids,
        count=payload.count,
    )

    if not payload.save:
        return {"ideas": generated, "saved": False, "source_signal_ids": source_signal_ids}

    saved = []
    for item in generated:
        item_without_note = {key: value for key, value in item.items() if key != "generator_note"}
        saved.append(crud.create_idea(IdeaCreate(**item_without_note)))
    return {"ideas": saved, "saved": True, "source_signal_ids": source_signal_ids}


@app.get("/ideas", response_model=list[Idea])
def list_ideas(status: str | None = Query(default=None)) -> list[dict]:
    return crud.list_ideas(status=status)


@app.get("/ideas/{idea_id}", response_model=Idea)
def get_idea(idea_id: str) -> dict:
    try:
        return crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")


@app.patch("/ideas/{idea_id}", response_model=Idea)
def update_idea(idea_id: str, payload: IdeaUpdate) -> dict:
    try:
        return crud.update_idea(idea_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")


@app.post("/ideas/{idea_id}/anti-rational-review", response_model=AntiRationalReviewResponse)
def run_anti_rational_review(idea_id: str) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")

    result = review_idea(idea)
    updated_idea = crud.update_idea(idea_id, IdeaUpdate(scores=result["scores"]))
    review = crud.create_review(
        ReviewCreate(
            idea_id=idea_id,
            review_type=result["review_type"],
            passes=result["passes"],
            flags=result["flags"],
            comment=result["comment"],
            suggestions=result["suggestions"],
        )
    )
    return {
        "review": review,
        "idea": updated_idea,
        "scores": result["scores"],
        "flags": result["flags"],
        "suggestions": result["suggestions"],
    }


@app.post("/ideas/{idea_id}/refresh-scores", response_model=ScoreRefreshResponse)
def refresh_scores(idea_id: str) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    scores = score_idea(idea)
    updated_idea = crud.update_idea(idea_id, IdeaUpdate(scores=scores))
    return {"idea": updated_idea, "scores": scores}


@app.get("/ideas/{idea_id}/rename-suggestions", response_model=RenameSuggestionsResponse)
def rename_suggestions(idea_id: str) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return {"idea_id": idea_id, "suggestions": make_suggestions(idea)}


@app.get("/ideas/{idea_id}/commercial-smell", response_model=CommercialSmellResponse)
def commercial_smell(idea_id: str) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    report = commercial_smell_report(idea)
    return {"idea_id": idea_id, **report}


@app.post("/reviews", response_model=Review)
def create_review(payload: ReviewCreate) -> dict:
    try:
        crud.get_idea(payload.idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return crud.create_review(payload)


@app.get("/ideas/{idea_id}/reviews", response_model=list[Review])
def list_reviews(idea_id: str) -> list[dict]:
    return crud.list_reviews(idea_id)


@app.post("/experiments", response_model=Experiment)
def create_experiment(payload: ExperimentCreate) -> dict:
    try:
        crud.get_idea(payload.idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return crud.create_experiment(payload)


@app.get("/ideas/{idea_id}/experiments", response_model=list[Experiment])
def list_experiments(idea_id: str) -> list[dict]:
    return crud.list_experiments(idea_id)


@app.get("/ideas/{idea_id}/mvp-draft", response_model=MvpDraftResponse)
def get_mvp_draft(idea_id: str) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return build_mvp_draft(idea)


@app.post("/ideas/{idea_id}/export-task-package", response_model=TaskPackageExportResponse)
def export_idea_task_package(idea_id: str) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    package = export_task_package(idea)
    record = crud.create_export_record(
        idea_id=idea_id,
        export_type="prototype_task_package",
        path=package["directory"],
    )
    updated = crud.update_idea(idea_id, IdeaUpdate(status="mvp_draft", status_note="已產生 Phase 4 Prototype 任務包。"))
    package["export_record"] = record
    package["idea"] = updated
    return package


@app.get("/ideas/{idea_id}/exports", response_model=list[ExportRecord])
def list_idea_exports(idea_id: str) -> list[dict]:
    try:
        crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return crud.list_exports(idea_id)


@app.get("/ideas/{idea_id}/similar", response_model=SimilarIdeasResponse)
def get_similar_ideas(idea_id: str) -> dict:
    try:
        target = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    items = similar_ideas(target, crud.list_ideas(), limit=8)
    return {"idea_id": idea_id, "items": items}


@app.get("/idea-families", response_model=IdeaFamiliesResponse)
def list_idea_families() -> dict:
    ideas = crud.list_ideas()
    families = build_family_suggestions(ideas)
    return {"families": families}


@app.get("/graveyard/revive-suggestions", response_model=ReviveSuggestionsResponse)
def list_revive_suggestions() -> dict:
    items = revive_suggestions(crud.list_ideas(), crud.list_signals(), limit=10)
    return {"items": items}


@app.post("/idea-events", response_model=IdeaEvent)
def create_idea_event(payload: IdeaEventCreate) -> dict:
    try:
        crud.get_idea(payload.idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return crud.create_idea_event(payload)


@app.get("/ideas/{idea_id}/events", response_model=list[IdeaEvent])
def list_idea_events(idea_id: str) -> list[dict]:
    try:
        crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return crud.list_idea_events(idea_id)


@app.post("/ideas/merge", response_model=MergeIdeasResponse)
def merge_ideas(payload: MergeIdeasRequest) -> dict:
    source_ideas = []
    for idea_id in payload.idea_ids:
        try:
            source_ideas.append(crud.get_idea(idea_id))
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Idea not found: {idea_id}")

    merged_payload = build_merged_idea_payload(source_ideas, selected_name=payload.name)
    merged_idea = crud.create_idea(IdeaCreate(**merged_payload))
    events = []
    events.append(
        crud.create_idea_event(
            IdeaEventCreate(
                idea_id=merged_idea["id"],
                event_type="merged_from",
                title="Phase 6 合併產生",
                note="由相似題目合併而成：" + "、".join(item["name"] for item in source_ideas),
                related_idea_ids=[item["id"] for item in source_ideas],
                metadata={"source_names": [item["name"] for item in source_ideas]},
            )
        )
    )

    if payload.mark_sources_merged:
        for item in source_ideas:
            crud.update_idea(
                item["id"],
                IdeaUpdate(status="merged", status_note=f"Phase 6 已合併到 {merged_idea['name']} ({merged_idea['id']})"),
            )
            events.append(
                crud.create_idea_event(
                    IdeaEventCreate(
                        idea_id=item["id"],
                        event_type="merged_into",
                        title="已合併到母題",
                        note=f"合併到 {merged_idea['name']}。",
                        related_idea_ids=[merged_idea["id"]],
                    )
                )
            )

    return {"merged_idea": merged_idea, "source_ideas": source_ideas, "events": events}


@app.post("/ideas/{idea_id}/prototype-workspace", response_model=PrototypeWorkspaceCreateResponse)
def create_prototype_workspace(idea_id: str, payload: PrototypeWorkspaceCreate) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")

    files = create_prototype_workspace_files(idea, worker=payload.worker, overwrite=payload.overwrite)
    title = payload.title or f"{idea.get('name')} Prototype Workspace"
    workspace = crud.create_prototype_workspace(
        idea_id=idea_id,
        title=title,
        worker=payload.worker,
        directory=files["directory"],
        notes=payload.notes,
    )
    updated = crud.update_idea(
        idea_id,
        IdeaUpdate(status="prototype_ready", status_note=f"Phase 7 已建立 prototype workspace：{workspace['directory']}"),
    )
    crud.create_idea_event(
        IdeaEventCreate(
            idea_id=idea_id,
            event_type="prototype_workspace_created",
            title="建立 Prototype Workspace",
            note=f"建立 {workspace['directory']}，worker={payload.worker}。",
            metadata={"workspace_id": workspace["id"], "directory": workspace["directory"]},
        )
    )
    return {"workspace": workspace, "idea": updated, **files}


@app.get("/ideas/{idea_id}/prototype-workspaces", response_model=list[PrototypeWorkspace])
def list_prototype_workspaces(idea_id: str) -> list[dict]:
    try:
        crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return crud.list_prototype_workspaces(idea_id=idea_id)


@app.post("/prototype-runs", response_model=PrototypeRunCreateResponse)
def create_prototype_run(payload: PrototypeRunCreate) -> dict:
    try:
        idea = crud.get_idea(payload.idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")

    workspace = None
    if payload.workspace_id:
        try:
            workspace = crud.get_prototype_workspace(payload.workspace_id)
        except KeyError:
            raise HTTPException(status_code=404, detail="Prototype workspace not found")

    run = crud.create_prototype_run(payload)
    report_path = None
    if workspace:
        report_path = write_run_markdown(workspace.get("directory", ""), run)
        if report_path:
            run = crud.update_prototype_run(run["id"], PrototypeRunUpdate(report_path=report_path))

    updated_idea = crud.update_idea(
        payload.idea_id,
        IdeaUpdate(status="prototype", status_note=f"Phase 7 已新增 prototype run：{run['title']}"),
    )
    crud.create_idea_event(
        IdeaEventCreate(
            idea_id=payload.idea_id,
            event_type="prototype_run_created",
            title="新增 Prototype Run",
            note=f"{run['title']} / {run['worker']} / {run['status']}",
            metadata={"run_id": run["id"], "workspace_id": payload.workspace_id, "report_path": run.get("report_path", "")},
        )
    )
    return {"run": run, "report_path": run.get("report_path") or report_path, "idea": updated_idea}


@app.get("/ideas/{idea_id}/prototype-runs", response_model=list[PrototypeRun])
def list_prototype_runs(idea_id: str) -> list[dict]:
    try:
        crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return crud.list_prototype_runs(idea_id=idea_id)


@app.patch("/prototype-runs/{run_id}", response_model=PrototypeRun)
def update_prototype_run(run_id: str, payload: PrototypeRunUpdate) -> dict:
    try:
        run = crud.update_prototype_run(run_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Prototype run not found")

    workspace = None
    if run.get("workspace_id"):
        try:
            workspace = crud.get_prototype_workspace(run["workspace_id"])
        except KeyError:
            workspace = None
    if workspace:
        report_path = write_run_markdown(workspace.get("directory", ""), run)
        if report_path and report_path != run.get("report_path"):
            run = crud.update_prototype_run(run_id, PrototypeRunUpdate(report_path=report_path))
    return run



@app.post("/ideas/{idea_id}/repo-experiments", response_model=RepoExperimentCreateResponse)
def create_repo_experiment(idea_id: str, payload: RepoExperimentCreate) -> dict:
    try:
        crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")

    # Create an id first by using a lightweight temporary payload id from crud.new_id.
    experiment_id = crud.new_id("repoexp")
    try:
        result = probe_repo(
            experiment_id=experiment_id,
            title=payload.title,
            repo_url=payload.repo_url,
            run_mode=payload.run_mode,
            timeout_seconds=payload.timeout_seconds,
        )
    except Exception as exc:
        result = {
            "status": "blocked",
            "summary": f"Repo probe failed before report generation: {exc}",
            "detected_stack": [],
            "evidence": [],
            "setup_commands": [],
            "build_commands": [],
            "test_commands": [],
            "start_commands": [],
            "risks": ["probe 執行階段發生未預期錯誤。"],
            "report_path": "",
            "workspace_dir": "",
            "logs": [],
        }

    # Persist with a normal generated DB id. The workspace/report path keeps the pre-generated probe id.
    experiment = crud.create_repo_experiment(idea_id, payload, result=result)
    status = "prototype" if experiment.get("status") in {"passed", "inspected", "planned"} else "deep_dive"
    updated_idea = crud.update_idea(
        idea_id,
        IdeaUpdate(
            status=status,
            status_note=f"Phase 8 Repo Probe：{experiment['repo_url']} / {experiment['status']}",
        ),
    )
    crud.create_idea_event(
        IdeaEventCreate(
            idea_id=idea_id,
            event_type="repo_experiment",
            title="新增 Repo Setup/Build/Test 實驗",
            note=f"{experiment['repo_url']} → {experiment['status']}: {experiment['summary']}",
            metadata={
                "repo_experiment_id": experiment["id"],
                "repo_url": experiment["repo_url"],
                "report_path": experiment.get("report_path", ""),
                "detected_stack": experiment.get("detected_stack", []),
            },
        )
    )
    return {"experiment": experiment, "idea": updated_idea}


@app.get("/ideas/{idea_id}/repo-experiments", response_model=list[RepoExperiment])
def list_repo_experiments(idea_id: str) -> list[dict]:
    try:
        crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return crud.list_repo_experiments(idea_id=idea_id)


@app.get("/repo-experiments/{experiment_id}", response_model=RepoExperiment)
def get_repo_experiment(experiment_id: str) -> dict:
    try:
        return crud.get_repo_experiment(experiment_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Repo experiment not found")


@app.get("/taste/profile", response_model=TasteProfileResponse)
def get_taste_profile() -> dict:
    return build_taste_profile()


@app.post("/taste/feedback", response_model=TasteFeedbackResponse)
def post_taste_feedback(payload: TasteFeedbackCreate) -> dict:
    try:
        feedback = create_feedback(payload)
        idea = crud.get_idea(payload.idea_id)
        fit = score_taste_fit(idea)
        profile = build_taste_profile()
        return {"feedback": feedback, "fit": fit, "profile": profile}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Idea not found: {exc}")


@app.get("/ideas/{idea_id}/taste-fit", response_model=TasteFitResponse)
def get_idea_taste_fit(idea_id: str) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    return score_taste_fit(idea)


@app.post("/ideas/{idea_id}/apply-taste-score", response_model=Idea)
def apply_taste_score(idea_id: str) -> dict:
    try:
        idea = crud.get_idea(idea_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Idea not found")
    fit = score_taste_fit(idea)
    scores = dict(idea.get("scores") or {})
    scores["personal_fit"] = round(fit["score"] / 10)
    return crud.update_idea(idea_id, IdeaUpdate(scores=scores))


@app.get("/taste/recommendations", response_model=TasteRecommendationsResponse)
def get_taste_recommendations(limit: int = Query(default=10, ge=1, le=50)) -> dict:
    return {"items": recommendations(limit)}

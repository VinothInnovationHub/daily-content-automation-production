from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from .config import settings
from .db import init_db, get_db
from .models import Job, Content
from .schemas import JobCreate, JobOut, ContentUpdate, HealthOut
from .auth import require_admin
from .service import generate_job, approve_job, reject_job, publish_job, update_content, get_job


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", include_in_schema=False)
async def home():
    return FileResponse(Path(__file__).resolve().parents[1] / "frontend" / "index.html")


@app.get("/health", response_model=HealthOut)
async def health():
    return {
        "status": "ok",
        "timezone": settings.timezone,
        "daily_run": f"{settings.daily_run_hour:02d}:{settings.daily_run_minute:02d}",
        "llm_provider": settings.llm_provider,
    }


@app.get("/api/jobs", response_model=list[JobOut], dependencies=[Depends(require_admin)])
async def list_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Job).order_by(desc(Job.created_at)).limit(100)
    )
    jobs = result.scalars().all()
    output = []
    for job in jobs:
        output.append(await get_job(db, job.id))
    return output


@app.post("/api/jobs", response_model=JobOut, dependencies=[Depends(require_admin)])
async def create_job(payload: JobCreate, db: AsyncSession = Depends(get_db)):
    job = Job(
        topic=payload.topic,
        perspective=payload.perspective,
        instructions=payload.instructions,
        status="DRAFT",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return await get_job(db, job.id)


@app.post("/api/jobs/{job_id}/run", response_model=JobOut, dependencies=[Depends(require_admin)])
async def run_job(job_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await generate_job(db, job_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/jobs/{job_id}/approve", response_model=JobOut, dependencies=[Depends(require_admin)])
async def approve(job_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await approve_job(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/jobs/{job_id}/reject", response_model=JobOut, dependencies=[Depends(require_admin)])
async def reject(job_id: int, reason: str = "Rejected by administrator", db: AsyncSession = Depends(get_db)):
    try:
        return await reject_job(db, job_id, reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/jobs/{job_id}/publish", response_model=JobOut, dependencies=[Depends(require_admin)])
async def publish(job_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await publish_job(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/jobs/{job_id}/approve-and-publish", response_model=JobOut, dependencies=[Depends(require_admin)])
async def approve_and_publish(job_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await approve_job(db, job_id)
        return await publish_job(db, job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.patch("/api/contents/{content_id}", dependencies=[Depends(require_admin)])
async def edit_content(content_id: int, payload: ContentUpdate, db: AsyncSession = Depends(get_db)):
    try:
        content = await update_content(db, content_id, payload.title, payload.body)
        return {
            "id": content.id,
            "channel": content.channel,
            "title": content.title,
            "body": content.body,
            "status": content.status,
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/api/internal/daily-run")
async def daily_run(
    x_cron_secret: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
):
    if x_cron_secret != settings.cron_secret:
        raise HTTPException(status_code=403, detail="Invalid cron secret")

    job = Job(
        topic="Daily technology trend",
        perspective="Create a useful, credible technology insight for software architects and engineering leaders.",
        instructions="Use the configured daily topic strategy. Produce a LinkedIn post and a standalone long-form article. Leave both pending human approval.",
        status="DRAFT",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    await generate_job(db, job.id)
    return {"status": "ok", "job_id": job.id}

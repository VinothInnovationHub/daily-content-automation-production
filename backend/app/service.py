import json
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Job, Content, Log
from .llm import get_provider
from .prompting import build_generation_prompt
from .research import research as run_research
from .config import settings


async def log(db: AsyncSession, job_id: int, message: str, level: str = "INFO"):
    db.add(Log(job_id=job_id, message=message, level=level))
    await db.commit()


async def get_job(db: AsyncSession, job_id: int) -> Job | None:
    result = await db.execute(
        select(Job)
        .options(selectinload(Job.contents), selectinload(Job.logs))
        .where(Job.id == job_id)
    )
    return result.scalar_one_or_none()


async def generate_job(db: AsyncSession, job_id: int):
    job = await get_job(db, job_id)
    if not job:
        raise ValueError("Job not found")

    job.status = "GENERATING"
    job.rejection_reason = ""
    await db.commit()

    try:
        await log(db, job_id, "Generation started")
        research = await run_research(job.topic)
        await log(db, job_id, "Research completed")
        provider = get_provider()
        raw = await provider.generate(
            build_generation_prompt(job.topic, job.perspective, job.instructions, research)
        )

        if raw.startswith("```"):
            raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)
        linkedin = data["linkedin"]
        medium = data["medium"]

        for old in list(job.contents):
            await db.delete(old)

        db.add(Content(
            job_id=job.id,
            channel="linkedin",
            title=linkedin.get("title", ""),
            body=linkedin["body"],
            status="PENDING_APPROVAL",
        ))
        db.add(Content(
            job_id=job.id,
            channel="medium",
            title=medium["title"],
            body=medium["body"],
            status="PENDING_APPROVAL",
        ))

        job.status = "PENDING_APPROVAL"
        await db.commit()
        await log(db, job_id, "Content generated and waiting for human approval")
        return await get_job(db, job_id)

    except Exception as exc:
        job.status = "FAILED"
        await db.commit()
        await log(db, job_id, f"Generation failed: {type(exc).__name__}: {exc}", "ERROR")
        raise


async def approve_job(db: AsyncSession, job_id: int):
    job = await get_job(db, job_id)
    if not job:
        raise ValueError("Job not found")
    if job.status != "PENDING_APPROVAL":
        raise ValueError(f"Job cannot be approved from status {job.status}")
    for content in job.contents:
        content.status = "APPROVED"
    job.status = "APPROVED"
    await db.commit()
    await log(db, job_id, "Human approval recorded")
    return await get_job(db, job_id)


async def reject_job(db: AsyncSession, job_id: int, reason: str):
    job = await get_job(db, job_id)
    if not job:
        raise ValueError("Job not found")
    if job.status not in {"PENDING_APPROVAL", "APPROVED"}:
        raise ValueError(f"Job cannot be rejected from status {job.status}")
    job.status = "REJECTED"
    job.rejection_reason = reason
    for content in job.contents:
        content.status = "REJECTED"
    await db.commit()
    await log(db, job_id, f"Human rejected content: {reason}", "WARN")
    return await get_job(db, job_id)


async def update_content(db: AsyncSession, content_id: int, title: str | None, body: str | None):
    result = await db.execute(select(Content).where(Content.id == content_id))
    content = result.scalar_one_or_none()
    if not content:
        raise ValueError("Content not found")
    if title is not None:
        content.title = title
    if body is not None:
        content.body = body
    if content.status == "PENDING_APPROVAL":
        content.status = "PENDING_APPROVAL"
    await db.commit()
    return content


async def publish_job(db: AsyncSession, job_id: int):
    job = await get_job(db, job_id)
    if not job:
        raise ValueError("Job not found")
    if job.status != "APPROVED":
        raise ValueError("Human approval is required before publishing")
    if not settings.publish_enabled:
        raise ValueError("Publishing is disabled by configuration")

    linkedin = next((c for c in job.contents if c.channel == "linkedin"), None)
    medium = next((c for c in job.contents if c.channel == "medium"), None)

    if linkedin and settings.linkedin_enabled:
        from .publishers.linkedin import LinkedInPublisher
        url = await LinkedInPublisher().publish(linkedin.body)
        linkedin.published_url = url
        linkedin.status = "PUBLISHED"
    elif linkedin:
        linkedin.status = "APPROVED"

    # Medium API terms currently prohibit automatically generated content.
    # Therefore this application deliberately does NOT auto-publish Medium.
    if medium:
        medium.status = "APPROVED"

    job.status = "PUBLISHED" if linkedin and linkedin.status == "PUBLISHED" else "APPROVED"
    await db.commit()
    await log(db, job_id, "LinkedIn publishing completed; Medium remains approved for manual publication")
    return await get_job(db, job_id)

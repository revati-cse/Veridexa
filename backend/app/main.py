from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.rate_limit import RateLimitMiddleware
from app.routers import (
    candidates,
    challenges,
    evaluations,
    evidence,
    github,
    jobs,
    readiness,
    skills,
    submissions,
)

app = FastAPI(title="Veridexa AI API", version="0.1.0")

# Middleware order: the LAST one added is outermost. RateLimitMiddleware is
# added first so CORSMiddleware wraps it — otherwise a 429 rejection would
# skip CORS headers and the frontend couldn't even read the rejection.
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(skills.router)
app.include_router(candidates.router)
app.include_router(github.router)
app.include_router(challenges.router)
app.include_router(submissions.router)
app.include_router(evaluations.router)
app.include_router(readiness.router)
app.include_router(evidence.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

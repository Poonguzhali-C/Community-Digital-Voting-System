import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import CORS_ORIGINS
from .routers import admin, auth, proposals, votes

logger = logging.getLogger("voting")

app = FastAPI(
    title="Community Digital Voting System",
    description="REST API for community proposals, deadlines and one-vote-per-user voting.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(proposals.router)
app.include_router(votes.router)
app.include_router(admin.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get("/", tags=["Health"])
def root():
    return {"message": "Community Digital Voting System API is running"}

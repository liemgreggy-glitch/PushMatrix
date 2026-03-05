from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import (
    accounts,
    proxies,
    messages,
    direct,
    invites,
    checker,
    profile,
    tasks,
    stats,
    settings,
)
from database.connection import init_db

app = FastAPI(
    title="PushMatrix API",
    description="Telegram 营销工具后端 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(accounts.router)
app.include_router(proxies.router)
app.include_router(messages.router)
app.include_router(direct.router)
app.include_router(invites.router)
app.include_router(checker.router)
app.include_router(profile.router)
app.include_router(tasks.router)
app.include_router(stats.router)
app.include_router(settings.router)


@app.get("/")
async def root():
    return {"message": "PushMatrix API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    from config import settings

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.profiles import router as profiles_router
from app.api.content import router as content_router
from app.api.game import router as game_router
from app.core.config import settings
from app.core.logging import LoggingMiddleware, global_exception_handler

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

app.add_middleware(LoggingMiddleware)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, tags=["Authentication"])
app.include_router(profiles_router, prefix="/profiles", tags=["Profiles"])
app.include_router(content_router, prefix="/content", tags=["Content"])
app.include_router(game_router, prefix="/game", tags=["Gameplay"])

@app.get("/")
def root():
    return {"message": "Welcome to KULTURE API"}

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.core.lifespan import lifespan
from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.user.router import router as user_router

app = FastAPI(title="FastAPI Synology SSO", version="0.1.0", lifespan=lifespan, openapi_url=None, docs_url=None, redoc_url=None)

_session_kwargs: dict = dict(
    secret_key=settings.secret_key,
    max_age=settings.session_max_age,
    https_only=False,
    same_site="lax",
)
if settings.session_cookie_domain:
    _session_kwargs["domain"] = settings.session_cookie_domain

app.add_middleware(SessionMiddleware, **_session_kwargs)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(user_router, tags=["user"])

@app.get("/health", summary="健康检查")
async def health():
    return {"status": "ok"}
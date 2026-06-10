"""全局 FastAPI 依赖项。"""
import httpx
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.modules.user.schemas import SessionUser

from .oauth import OpenIDConfiguration
from .state import State
import logging

logger = logging.getLogger(__name__)


def get_state(request: Request) -> State:
    return request.state


def get_sso_metadata(request: Request) -> OpenIDConfiguration:
    return get_state(request).sso_metadata


def get_sso_client(request: Request) -> httpx.AsyncClient:
    return get_state(request).sso_client


def get_current_user(request: Request) -> SessionUser:
    user_data = request.session.get("user")
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录，请先完成 SSO 认证",
        )
    return SessionUser(**user_data)


def get_optional_user(request: Request) -> SessionUser | None:
    user_data = request.session.get("user")
    return SessionUser(**user_data) if user_data else None


def require_login(request: Request) -> SessionUser:
    """未登录时重定向到登录页，登录完成后跳回当前页面。"""
    
    user_data = request.session.get("user")
    if not user_data:
        next_url = str(request.url)

        logger.info(f"用户未登录，重定向到登录页，next={next_url}")
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/auth/login?next={next_url}"},
        )
    return SessionUser(**user_data)

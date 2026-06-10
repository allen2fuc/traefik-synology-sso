import base64
import json
import logging
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.config import settings
from app.core.dependencies import get_sso_client, get_sso_metadata
from app.core.oauth import OpenIDConfiguration

from .schemas import SSOAccessToken, SSOUserInfo

router = APIRouter()

NONCE_COOKIE = "oauth_nonce"

logger = logging.getLogger(__name__)


def _encode_state(next_url: str) -> str:
    """将 next_url 和随机 state 一起编码进 state 参数。"""
    payload = {"r": secrets.token_urlsafe(24), "next": next_url}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _decode_state(state: str) -> tuple[str, str]:
    """解码 state，返回 (random, next_url)。"""
    try:
        payload = json.loads(base64.urlsafe_b64decode(state.encode()))
        return payload["r"], payload.get("next", "/")
    except Exception:
        return "", "/"


@router.get("/login", summary="重定向到 Synology SSO 授权页")
async def login(
    next: str = "/",
    sso_metadata: OpenIDConfiguration = Depends(get_sso_metadata),
):
    state = _encode_state(next)
    nonce = secrets.token_urlsafe(24)

    params = urlencode({
        "response_type": "code",
        "client_id": settings.synology_client_id,
        "redirect_uri": settings.redirect_uri,
        "scope": "openid profile email",
        "state": state,
        "nonce": nonce,
    })
    url = f"{sso_metadata.authorization_url}?{params}"
    logger.info(f"[SSO] redirecting to NAS, next={next}")

    response = RedirectResponse(url=url)
    # nonce 仍需 cookie 校验（可选安全增强），此处仅记录
    response.set_cookie(NONCE_COOKIE, nonce, httponly=True, samesite="none", secure=False, max_age=600)
    return response


@router.get("/callback", summary="SSO 回调：换取 token 并写入 session")
async def callback(
    request: Request,
    sso_metadata: OpenIDConfiguration = Depends(get_sso_metadata),
    sso_client: httpx.AsyncClient = Depends(get_sso_client),
):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少 authorization code")

    raw_state = request.query_params.get("state", "")
    _, next_url = _decode_state(raw_state)

    resp = await sso_client.post(
        sso_metadata.token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.redirect_uri,
            "client_id": settings.synology_client_id,
            "client_secret": settings.synology_client_secret,
        },
    )
    logger.info(f"[SSO] token response {resp.status_code}")
    resp.raise_for_status()
    token = SSOAccessToken.model_validate(resp.json())

    resp = await sso_client.get(
        sso_metadata.userinfo_url,
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    logger.info(f"[SSO] userinfo response {resp.status_code}")
    resp.raise_for_status()
    userinfo = SSOUserInfo.model_validate(resp.json())

    request.session["user"] = userinfo.model_dump()
    logger.info(f"[SSO] login success: {userinfo.username}, redirecting to {next_url}")

    response = RedirectResponse(url=next_url)
    response.delete_cookie(NONCE_COOKIE)
    return response


@router.get("/logout", summary="清除本地 session")
async def logout(request: Request):
    # 仅清除本地 session；Synology SSO 不支持 end_session_endpoint，
    # NAS 端 session 无法主动中断，用户在 NAS session 过期前重新访问会自动登录。
    request.session.clear()
    return RedirectResponse(url="/auth/login")


@router.get("/me", summary="返回当前登录用户信息")
async def me(request: Request):
    user = request.session.get("user")
    if not user:
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "未登录"})
    return user


@router.get("/verify", summary="Traefik forwardAuth 验证端点")
async def verify(request: Request):
    """
    Traefik forwardAuth 中间件调用此端点：
    - 已登录 → 200，响应头携带用户信息，Traefik 将其转发给上游服务
    - 未登录 → 302，跳转到登录页（Traefik 将重定向透传给浏览器）
    """
    user = request.session.get("user")

    if not user:
        # 从 Traefik 转发头中还原原始请求 URL，登录后跳回
        proto = request.headers.get("X-Forwarded-Proto", "http")
        host = request.headers.get("X-Forwarded-Host", request.headers.get("host", ""))
        uri = request.headers.get("X-Forwarded-Uri", "/")
        original_url = f"{proto}://{host}{uri}" if host else uri

        login_url = f"{settings.app_base_url}/auth/login?next={original_url}"
        logger.info(f"[verify] 未登录，重定向到 {login_url}")
        return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)

    # 已登录：返回 200 并附带用户信息 header，Traefik 可配置转发给上游
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"ok": True},
        headers={
            "X-User-Sub": user.get("sub", ""),
            "X-User-Name": user.get("username", ""),
            "X-User-Email": user.get("email", ""),
        },
    )

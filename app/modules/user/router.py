from fastapi import APIRouter, Depends

from app.core.dependencies import get_optional_user, require_login
from app.modules.user.schemas import SessionUser

router = APIRouter()


@router.get("/", summary="首页")
async def index(user: SessionUser | None = Depends(get_optional_user)):
    if user:
        return {"message": f"欢迎回来，{user.username}"}
    return {"message": "请访问 /auth/login 完成登录"}


@router.get("/profile", summary="个人主页（需登录，未登录跳转登录页后返回）")
async def profile(user: SessionUser = Depends(require_login)):
    return user

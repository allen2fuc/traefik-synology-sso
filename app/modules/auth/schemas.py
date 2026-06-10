from pydantic import BaseModel, Field
from typing import Annotated

class OAuthCallback(BaseModel):
    code: str
    state: str | None = None

class SSOAccessToken(BaseModel):
    access_token: Annotated[str, Field(description="访问令牌")]
    token_type: Annotated[str, Field(description="令牌类型", example="Bearer")]
    expires_in: Annotated[int, Field(description="令牌过期时间", example=180)]
    id_token: Annotated[str, Field(description="ID 令牌")]

class SSOUserInfo(BaseModel):
    sub: Annotated[str, Field(description="用户唯一标识")]
    username: Annotated[str, Field(description="用户名")]
    email: Annotated[str, Field(description="邮箱")]
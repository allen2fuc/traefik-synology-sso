from pydantic import BaseModel
from typing import Annotated
from pydantic import Field

class SessionUser(BaseModel):
    sub: Annotated[str, Field(description="用户唯一标识")]
    username: Annotated[str, Field(description="用户名")]
    email: Annotated[str, Field(description="邮箱")]
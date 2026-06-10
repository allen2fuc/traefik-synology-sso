import ssl
from typing import Annotated

import httpx
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from .config import settings

# 彻底跳过 SSL 验证的 context（应对自签证书 / TLS 握手失败）
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE


def _build_httpx_kwargs() -> dict:
    """根据 ssl_verify 配置生成 httpx 客户端参数。"""
    verify = True if settings.ssl_verify else _ssl_context
    return {"verify": verify, "timeout": httpx.Timeout(30.0)}


class OpenIDConfiguration(BaseModel):
    """Synology OIDC Well-known 文档结构。

    使用 extra="ignore" 忽略未知字段，兼容未来 DSM 版本新增字段。
    """

    model_config = ConfigDict(extra="ignore")

    # 核心端点（router 实际使用）
    authorization_endpoint: Annotated[HttpUrl, Field(description="授权端点")]
    token_endpoint: Annotated[HttpUrl, Field(description="令牌端点")]
    userinfo_endpoint: Annotated[HttpUrl, Field(description="用户信息端点")]
    jwks_uri: Annotated[HttpUrl, Field(description="JWKS 端点")]
    issuer: Annotated[HttpUrl, Field(description="发行者")]

    # 能力声明（供调用方参考，不强制使用）
    scopes_supported: list[str] = Field(default_factory=list, description="支持的 scope")
    response_types_supported: list[str] = Field(default_factory=list)
    grant_types_supported: list[str] = Field(default_factory=list)
    claims_supported: list[str] = Field(default_factory=list)
    id_token_signing_alg_values_supported: list[str] = Field(default_factory=list)
    token_endpoint_auth_methods_supported: list[str] = Field(default_factory=list)
    code_challenge_methods_supported: list[str] = Field(default_factory=list)
    subject_types_supported: list[str] = Field(default_factory=list)

    # ── 端点 URL 辅助属性 ──────────────────────────────────────────
    # Pydantic v2 HttpUrl.__str__() 可能带尾部斜杠，统一用 str(url).rstrip("/") 取值

    @property
    def authorization_url(self) -> str:
        return str(self.authorization_endpoint).rstrip("/")

    @property
    def token_url(self) -> str:
        return str(self.token_endpoint).rstrip("/")

    @property
    def userinfo_url(self) -> str:
        return str(self.userinfo_endpoint).rstrip("/")


async def load_sso_metadata(client: httpx.AsyncClient) -> OpenIDConfiguration:
    resp = await client.get(settings.oidc_discovery_url)
    resp.raise_for_status()
    return OpenIDConfiguration.model_validate(resp.json())


def create_sso_client() -> httpx.AsyncClient:
    """创建共享的 httpx 异步客户端（在 lifespan 中统一管理生命周期）。"""
    return httpx.AsyncClient(**_build_httpx_kwargs())

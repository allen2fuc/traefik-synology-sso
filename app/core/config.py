from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Synology SSO
    synology_base_url: str = "https://your-nas:5001"
    synology_client_id: str = ""
    # Synology SSO Server 部分版本不提供 client_secret，留空即可
    synology_client_secret: str = ""

    # 是否使用 OIDC 发现文档（DSM 7+ 支持，旧版设为 False 后手动端点生效）
    use_oidc_discovery: bool = True

    # 应用
    app_base_url: str = "http://localhost:8000"
    secret_key: str = "change-me"
    session_max_age: int = 3600
    # forwardAuth 场景下，浏览器请求上游服务时需携带 session cookie，
    # 须将 cookie domain 设为所有子域共享的父域（如 .example.com）。
    # 本地开发（localhost）留空即可。
    session_cookie_domain: str = ""

    # NAS 自签证书时设为 False
    ssl_verify: bool = False

    # Logger
    log_file: str = "logs/app.log"
    log_format: str = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
    log_datefmt: str = "%Y-%m-%d %H:%M:%S"
    log_level: str = "INFO"
    log_max_bytes: int = 10 * 1024 * 1024  # 50MB
    log_backup_count: int = 5

    @property
    def redirect_uri(self) -> str:
        return f"{self.app_base_url}/auth/callback"

    @property
    def oidc_discovery_url(self) -> str:
        return f"{self.synology_base_url}/webman/sso/.well-known/openid-configuration"

    # @property
    # def authorization_endpoint(self) -> str:
    #     return f"{self.synology_base_url}/webman/sso/oauth2/authorization"

    # @property
    # def token_endpoint(self) -> str:
    #     return f"{self.synology_base_url}/webman/sso/oauth2/token"

    # @property
    # def userinfo_endpoint(self) -> str:
    #     return f"{self.synology_base_url}/webman/sso/oauth2/userinfo"


settings = Settings()

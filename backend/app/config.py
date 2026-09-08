from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Env vars per BLUEPRINT.md Section S. All optional at import time so the
    stub routers can run without real credentials during Phase 2 scaffolding;
    services added later should fail loudly if the value they need is empty."""

    anthropic_api_key: str = ""
    github_token: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()

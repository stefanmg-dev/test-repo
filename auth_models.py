from pydantic import BaseModel, ConfigDict


class BrowserAuthConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    client_id: str | None = None
    authority: str | None = None
    redirect_path: str
    scopes: list[str]

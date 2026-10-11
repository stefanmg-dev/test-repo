from pydantic import BaseModel, ConfigDict, Field


class BrowserAuthConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool = Field(
        description="Whether browser-based OIDC authentication is enabled.",
        examples=[True],
    )
    client_id: str | None = Field(
        default=None,
        description="Public OIDC client identifier exposed to the browser.",
        examples=["00000000-0000-0000-0000-000000000000"],
    )
    authority: str | None = Field(
        default=None,
        description="OIDC authority used by the browser authentication client.",
        examples=["https://login.microsoftonline.com/common"],
    )
    redirect_path: str = Field(
        description="Application path used after browser authentication.",
        examples=["/ui/index.html"],
    )
    scopes: list[str] = Field(
        description="OIDC scopes requested by the browser authentication client.",
        examples=[["openid", "profile"]],
    )

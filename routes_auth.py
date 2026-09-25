from typing import Annotated

from fastapi import APIRouter, Depends

from app_settings import get_settings
from auth_models import BrowserAuthConfigModel


router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.get("/config", response_model=BrowserAuthConfigModel)
def get_browser_auth_config(
    settings: Annotated[
        object,
        Depends(get_settings),
    ],
):
    if not settings.oidc_browser_enabled:
        return BrowserAuthConfigModel(
            enabled=False,
            redirect_path=settings.oidc_browser_redirect_path,
            scopes=[],
        )
    return BrowserAuthConfigModel(
        enabled=True,
        client_id=settings.oidc_browser_client_id,
        authority=settings.oidc_browser_authority,
        redirect_path=settings.oidc_browser_redirect_path,
        scopes=settings.oidc_browser_scopes_list(),
    )

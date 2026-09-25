from fastapi import APIRouter, HTTPException, Response, status
from uuid import UUID

from api_key_models import (
    ApiKeyCreateRequest,
    ApiKeyCreatedModel,
    ApiKeyListResponseModel,
    ApiKeyModel,
    ApiKeyRotateRequest,
)
from api_key_service import ApiKeyNotFoundError
from security_audit import audit_security_event
from security_dependencies import (
    AdminPrincipal,
    ApiKeyServiceDependency,
)


router = APIRouter(prefix="/api/v1/api-keys", tags=["API keys"])


def created_response(created):
    return {
        **ApiKeyModel.model_validate(created.api_key).model_dump(),
        "secret": created.secret,
    }


@router.post("", response_model=ApiKeyCreatedModel, status_code=201)
def create_api_key(
    request: ApiKeyCreateRequest,
    principal: AdminPrincipal,
    service: ApiKeyServiceDependency,
):
    created = service.create_key(
        name=request.name,
        tenant_id=principal.tenant_id,
        scopes=request.scopes,
        expires_at=request.expires_at,
    )
    audit_security_event(
        "security.api_key_created",
        message="API key created",
        result="success",
        principal=principal,
        api_key_id=created.api_key.id,
    )
    return created_response(created)


@router.get("", response_model=ApiKeyListResponseModel)
def list_api_keys(
    principal: AdminPrincipal,
    service: ApiKeyServiceDependency,
):
    return {"items": service.list_keys(tenant_id=principal.tenant_id)}


@router.post("/{api_key_id}/rotate", response_model=ApiKeyCreatedModel)
def rotate_api_key(
    api_key_id: UUID,
    request: ApiKeyRotateRequest,
    principal: AdminPrincipal,
    service: ApiKeyServiceDependency,
):
    try:
        created = service.rotate_key(
            api_key_id,
            tenant_id=principal.tenant_id,
            expires_at=request.expires_at,
        )
    except ApiKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    audit_security_event(
        "security.api_key_rotated",
        message="API key rotated",
        result="success",
        principal=principal,
        api_key_id=created.api_key.id,
    )
    return created_response(created)


@router.delete("/{api_key_id}", status_code=204)
def revoke_api_key(
    api_key_id: UUID,
    principal: AdminPrincipal,
    service: ApiKeyServiceDependency,
):
    try:
        service.revoke_key(api_key_id, tenant_id=principal.tenant_id)
    except ApiKeyNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    audit_security_event(
        "security.api_key_revoked",
        message="API key revoked",
        result="success",
        principal=principal,
        api_key_id=api_key_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)

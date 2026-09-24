from dataclasses import dataclass
from typing import Literal


PrincipalType = Literal["user", "service", "system"]


@dataclass(frozen=True)
class SecurityPrincipal:
    principal_type: PrincipalType
    subject: str
    tenant_id: str
    scopes: frozenset[str]

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "admin" in self.scopes

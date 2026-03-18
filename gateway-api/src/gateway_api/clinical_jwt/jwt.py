from dataclasses import dataclass, field
from datetime import UTC, datetime
from time import time
from typing import Any

import jwt as pyjwt


@dataclass(frozen=True, kw_only=True)
class JWT:
    issuer: str
    subject: str
    audience: str
    requesting_device: str
    requesting_organization: str
    requesting_practitioner: str

    # Time fields
    issued_at: int = field(default_factory=lambda: int(time()))
    expiration: int = field(default_factory=lambda: int(time()) + 300)

    # These are here for future proofing but are not expected ever to be changed
    algorithm: str = "none"
    type: str = "JWT"
    reason_for_request: str = "directcare"
    requested_scope: str = "patient/*.read"

    @property
    def issue_time(self) -> str:
        return datetime.fromtimestamp(self.issued_at, tz=UTC).isoformat()

    @property
    def exp_time(self) -> str:
        return datetime.fromtimestamp(self.expiration, tz=UTC).isoformat()

    def encode(self) -> str:
        return pyjwt.encode(
            self.payload(),
            key=None,  # type: ignore[arg-type]
            algorithm=self.algorithm,
            headers={"typ": self.type},
        )

    @staticmethod
    def decode(token: str) -> "JWT":
        token_dict = pyjwt.decode(
            token,
            options={"verify_signature": False},  # NOSONAR S5659 (not signed)
        )

        return JWT(
            issuer=token_dict["iss"],
            subject=token_dict["sub"],
            audience=token_dict["aud"],
            expiration=token_dict["exp"],
            issued_at=token_dict["iat"],
            requesting_device=token_dict["requesting_device"],
            requesting_organization=token_dict["requesting_organization"],
            requesting_practitioner=token_dict["requesting_practitioner"],
        )

    def payload(self) -> dict[str, Any]:
        return {
            "iss": self.issuer,
            "sub": self.subject,
            "aud": self.audience,
            "exp": self.expiration,
            "iat": self.issued_at,
            "requesting_device": self.requesting_device,
            "requesting_organization": self.requesting_organization,
            "requesting_practitioner": self.requesting_practitioner,
            "reason_for_request": self.reason_for_request,
            "requested_scope": self.requested_scope,
        }

    def __str__(self) -> str:
        return self.encode()

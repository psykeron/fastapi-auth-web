from dataclasses import dataclass
from datetime import datetime
from os import urandom
from typing import Protocol

import jwt as pyjwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization


@dataclass
class PayloadClaim:
    user_id: str
    role: str

    # organization_id and organization_role are optional
    # as a user may not belong to any organization at first.
    organization_id: str | None = None
    organization_role: str | None = None

    # impersonator values are optional
    # but if one is present, the other must be present as well.
    impersonator_user_id: str | None = None
    impersonator_user_role: str | None = None
    impersonator_organization_id: str | None = None
    impersonator_organization_role: str | None = None

    def as_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "role": self.role,
            "organization_id": self.organization_id,
            "organization_role": self.organization_role,
            "impersonator_user_id": self.impersonator_user_id,
            "impersonator_user_role": self.impersonator_user_role,
            "impersonator_organization_id": self.impersonator_organization_id,
            "impersonator_organization_role": self.impersonator_organization_role,
        }


@dataclass
class JWTClaim:
    # Claims in the jwt standard
    sub: str  # Identifies the subject of the JWT. It is the user-id in the context of the issuer.
    exp: int  # Specifies the expiration time of the JWT. It is represented as a UNIX timestamp.
    iat: int  # Indicates the time at which the JWT was issued. It is represented as a UNIX timestamp.
    iss: str  # Identifies the issuer of the JWT. This claim indicates who created and signed the JWT.
    jti: str  # Provides a unique identifier for the JWT.

    # Custom claims
    custom_claims: PayloadClaim

    def as_dict(self) -> dict:
        return {
            "sub": self.sub,
            "exp": self.exp,
            "iat": self.iat,
            "iss": self.iss,
            "jti": self.jti,
            "custom_claims": {
                **self.custom_claims.as_dict(),
            },
        }


class JWTException(Exception):
    pass


class JWTSigningService(Protocol):
    def generate(self, payload: dict) -> str:
        pass


class JWTDecodeService(Protocol):
    def decode(self, jwt: str) -> dict:
        pass


class RSA256JWTSigningService:
    def __init__(
        self,
        private_key_pem: str,
        private_key_password: str,
    ):
        if not private_key_pem:
            raise JWTException(
                "Cannot initialize a JWT signing service without a private key"
            )
        if not private_key_password:
            raise JWTException(
                "Cannot initialize a JWT signing service without a private key password"
            )

        self.__private_key = serialization.load_pem_private_key(
            data=private_key_pem.encode(),
            password=private_key_password.encode(),
            backend=default_backend(),
        )

    def generate(self, payload: dict) -> str:
        if not self.__private_key:
            raise JWTException("Cannot generate a JWT without a private key")
        return pyjwt.encode(payload, self.__private_key, algorithm="RS256")  # type: ignore


class RSA256JWTDecodeService:
    def __init__(self, public_key_pem: str):
        if not public_key_pem:
            raise JWTException(
                "Cannot initialize a JWT decode service without a public key"
            )

        self.__public_key = public_key_pem

    def decode(self, jwt: str) -> dict:
        if not self.__public_key:
            raise JWTException("Cannot decode a JWT without a public key")

        try:
            return pyjwt.decode(
                jwt, self.__public_key, algorithms=["RS256"], verify=True
            )
        except pyjwt.exceptions.ExpiredSignatureError:
            raise JWTException("JWT expired")
        except pyjwt.exceptions.InvalidSignatureError:
            raise JWTException("Invalid JWT signature")
        except pyjwt.exceptions.PyJWTError:
            raise JWTException("Invalid JWT")


def build_jwt_claim(
    user_id: str,
    role: str,
    issuer: str,
    organization_id: str | None = None,
    organization_role: str | None = None,
    impersonator_user_id: str | None = None,
    impersonator_user_role: str | None = None,
    impersonator_organization_id: str | None = None,
    impersonator_organization_role: str | None = None,
    expire_in_seconds: int = 3600,
) -> JWTClaim:
    now = datetime.now()
    claim = JWTClaim(
        sub=user_id,
        exp=int(now.timestamp() + expire_in_seconds),
        iat=int(now.timestamp()),
        iss=issuer,
        jti=urandom(64).hex(),  # 512 bits, 128 hex chars
        custom_claims=PayloadClaim(
            user_id=user_id,
            role=role,
            organization_id=organization_id,
            organization_role=organization_role,
            impersonator_user_id=impersonator_user_id,
            impersonator_user_role=impersonator_user_role,
            impersonator_organization_id=impersonator_organization_id,
            impersonator_organization_role=impersonator_organization_role,
        ),
    )
    return claim


def create_jwt_token(
    payload: JWTClaim,
    signing_service: JWTSigningService,
) -> str:
    return signing_service.generate(payload.as_dict())


def decode_and_verify_jwt_token(
    jwt: str, decoding_service: JWTDecodeService
) -> JWTClaim:
    payload = decoding_service.decode(jwt)

    claim = JWTClaim(
        sub=payload["sub"],
        exp=payload["exp"],
        iat=payload["iat"],
        iss=payload["iss"],
        jti=payload["jti"],
        custom_claims=PayloadClaim(
            user_id=payload["custom_claims"]["user_id"],
            role=payload["custom_claims"]["role"],
            organization_id=payload["custom_claims"]["organization_id"],
            organization_role=payload["custom_claims"]["organization_role"],
            impersonator_user_id=payload["custom_claims"]["impersonator_user_id"],
            impersonator_user_role=payload["custom_claims"]["impersonator_user_role"],
            impersonator_organization_id=payload["custom_claims"][
                "impersonator_organization_id"
            ],
            impersonator_organization_role=payload["custom_claims"][
                "impersonator_organization_role"
            ],
        ),
    )

    if not verify_jwt_claim(claim):
        raise JWTException("JWT claim verification failed")

    return claim


def verify_jwt_claim(claim: JWTClaim) -> bool:
    if not claim:
        return False

    if not claim.exp:
        return False

    now = datetime.now()
    if now.timestamp() > claim.exp:
        return False

    if not claim.iat:
        return False

    if now.timestamp() < claim.iat:
        return False

    if not claim.sub:
        return False

    if not claim.iss:
        return False

    if not claim.jti:
        return False

    if not claim.custom_claims:
        return False

    if not claim.custom_claims.user_id:
        return False

    if not claim.custom_claims.role:
        return False

    if any(
        [claim.custom_claims.organization_id, claim.custom_claims.organization_role]
    ) and not all(
        [claim.custom_claims.organization_role, claim.custom_claims.organization_id]
    ):
        return False

    if any(
        [
            claim.custom_claims.impersonator_user_id,
            claim.custom_claims.impersonator_user_role,
            claim.custom_claims.impersonator_organization_id,
            claim.custom_claims.impersonator_organization_role,
        ]
    ) and not all(
        [
            claim.custom_claims.impersonator_user_id,
            claim.custom_claims.impersonator_user_role,
            claim.custom_claims.impersonator_organization_id,
            claim.custom_claims.impersonator_organization_role,
        ]
    ):
        return False

    return True

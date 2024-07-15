from datetime import datetime
from typing import Optional

from src.apps.auth.config import get_config
from src.lib_auth.jwt import JWTClaim, PayloadClaim, RSA256JWTSigningService
from src.lib_auth.roles import OrganizationRole, UserRole


def generate_test_jwt_token(
    user_id: str,
    user_role: UserRole,
    organization_id: str,
    organization_role: OrganizationRole,
    impersonator_user_id: Optional[str] = None,
    impersonator_user_role: Optional[UserRole] = None,
) -> str:
    private_key_config = get_config().private_key
    if not private_key_config:
        raise Exception("Private key is empty")

    private_key = private_key_config.key
    password = private_key_config.password

    if not private_key or not password:
        raise Exception("Private key or password is empty")

    jwt_signing_service = RSA256JWTSigningService(private_key, password)

    jwt = jwt_signing_service.generate(
        JWTClaim(
            sub=user_id,
            exp=int(datetime.now().timestamp() + 3600),
            iat=1,
            iss="oly-unit-test-token-generator",
            jti="test",
            custom_claims=PayloadClaim(
                user_id=user_id,
                role=user_role,
                organization_id=organization_id,
                organization_role=organization_role,
                impersonator_user_id=impersonator_user_id,
                impersonator_user_role=impersonator_user_role,
            ),
        ).as_dict()
    )

    return jwt

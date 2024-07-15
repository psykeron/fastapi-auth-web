from dataclasses import dataclass

from src.lib_auth.jwt import JWTClaim, verify_jwt_claim


@dataclass
class UserClaim:
    user_id: str
    user_role: str

    user_organization_id: str | None
    user_organization_role: str | None

    impersonator_user_id: str | None
    impersonator_user_role: str | None

    impersonator_organization_id: str | None
    impersonator_organization_role: str | None


def build_user_from_claim(claim: JWTClaim, with_verification: bool) -> UserClaim:
    if not claim:
        raise ValueError("No claim provided")

    if with_verification and not verify_jwt_claim(claim):
        raise ValueError("Invalid claim provided")

    return UserClaim(
        user_id=claim.custom_claims.user_id,
        user_role=claim.custom_claims.role,
        user_organization_id=claim.custom_claims.organization_id,
        user_organization_role=claim.custom_claims.organization_role,
        impersonator_user_id=claim.custom_claims.impersonator_user_id,
        impersonator_user_role=claim.custom_claims.impersonator_user_role,
        impersonator_organization_id=claim.custom_claims.impersonator_organization_id,
        impersonator_organization_role=claim.custom_claims.impersonator_organization_role,
    )

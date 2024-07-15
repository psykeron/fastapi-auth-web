from fastapi.testclient import TestClient

from src.apps.auth.app import app
from src.apps.auth.config import AuthDomainConfig, get_config
from src.apps.auth.endpoints.login import get_cookie_domain
from src.apps.auth.models.organization import Organization
from src.apps.auth.models.user import SensitiveUser, build_new_user
from src.apps.auth.repository.organizations import OrganizationsRepository
from src.apps.auth.repository.users import UserRepository
from src.lib_auth.jwt import (
    JWTClaim,
    RSA256JWTDecodeService,
    decode_and_verify_jwt_token,
)
from src.lib_auth.roles import OrganizationRole, UserRole


class TestGetCookieDomain:
    def test_get_cookie_domain_with_matching_origin(self):
        origin = "https://test.oly.co"
        allowed_domains = [
            AuthDomainConfig(
                **{
                    "origin": "https://test.oly.co",
                    "cookie_domain": "test.oly.co",
                    "cookie_is_secure": True,
                }
            ),
            AuthDomainConfig(
                **{
                    "origin": "https://test2.oly.co",
                    "cookie_domain": "test2.oly.co",
                    "cookie_is_secure": True,
                }
            ),
        ]

        assert get_cookie_domain(origin, allowed_domains) == AuthDomainConfig(
            **{
                "origin": "https://test.oly.co",
                "cookie_domain": "test.oly.co",
                "cookie_is_secure": True,
            }
        )

    def test_get_cookie_domain_without_matching_origin(self):
        origin = "https://test.oly.co"
        allowed_domains = [
            AuthDomainConfig(
                **{
                    "origin": "https://test2.oly.co",
                    "cookie_domain": "test2.oly.co",
                    "cookie_is_secure": True,
                }
            ),
        ]

        assert get_cookie_domain(origin, allowed_domains) is None

    def test_get_cookie_domain_with_matching_domain_but_wrong_protocol(self):
        origin = "http://test.oly.co"
        allowed_domains = [
            AuthDomainConfig(
                **{
                    "origin": "https://test.oly.co",
                    "cookie_domain": "test.oly.co",
                    "cookie_is_secure": True,
                }
            ),
            AuthDomainConfig(
                **{
                    "origin": "https://test2.oly.co",
                    "cookie_domain": "test2.oly.co",
                    "cookie_is_secure": True,
                }
            ),
        ]

        assert get_cookie_domain(origin, allowed_domains) is None

    def test_get_cookie_domain_without_origin(self):
        origin = ""
        allowed_domains = [
            AuthDomainConfig(
                **{
                    "origin": "https://test2.oly.co",
                    "cookie_domain": "test2.oly.co",
                    "cookie_is_secure": True,
                }
            ),
        ]

        assert get_cookie_domain(origin, allowed_domains) is None

    def test_get_cookie_domain_without_allowed_domains(self):
        origin = "https://test.oly.co"
        allowed_domains = []

        assert get_cookie_domain(origin, allowed_domains) is None


class TestLogin:
    def get_client(self) -> TestClient:
        return TestClient(app)

    def is_valid_token(self, token: str) -> bool:
        try:
            RSA256JWTDecodeService(
                public_key_pem=get_config().public_key.key  # type: ignore
            ).decode(token)
        except Exception:
            return False
        return True

    def get_jwt_claim(self, jwt: str) -> JWTClaim:
        return decode_and_verify_jwt_token(
            jwt,
            RSA256JWTDecodeService(
                public_key_pem=get_config().public_key.key  # type: ignore
            ),
        )

    async def test_login_for_user_without_organization(
        self, user_repository: UserRepository, ensure_clean_db: None
    ):
        email = "test@oly.co"
        password = "test_password_123_$$%"

        user: SensitiveUser = build_new_user(
            email=email, password=password, role=UserRole.USER
        )
        user.activate()
        user.confirm(user.confirmation_token)

        await user_repository.save_user(user)

        client = self.get_client()
        response = client.post(
            "/v1/login",
            json={"username": email, "password": password, "grant_type": "password"},
        )

        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert self.is_valid_token(response.json()["access_token"])

        jwt_claim = self.get_jwt_claim(response.json()["access_token"])
        assert jwt_claim.sub == user.id

        custom_claims = jwt_claim.custom_claims
        assert custom_claims.user_id == user.id
        assert custom_claims.role == user.role
        assert custom_claims.organization_id is None
        assert custom_claims.organization_role is None
        assert custom_claims.impersonator_user_id is None
        assert custom_claims.impersonator_user_role is None
        assert custom_claims.impersonator_organization_id is None
        assert custom_claims.impersonator_organization_role is None

    async def test_login_for_user_with_organization(
        self,
        user_repository: UserRepository,
        organizations_repository: OrganizationsRepository,
        ensure_clean_db: None,
    ):
        email = "test@oly.co"
        password = "test_password_123_$$%"
        organization_name = "test_organization"

        user: SensitiveUser = build_new_user(
            email=email, password=password, role=UserRole.USER
        )
        user.activate()
        user.confirm(user.confirmation_token)
        await user_repository.save_user(user)

        organization = Organization(
            name=organization_name,
            role=OrganizationRole.PLATFORM_USER,
            description="test organization",
        )
        await organizations_repository.create_organization(organization)

        user.organization = organization
        await user_repository.save_user(user)

        client = self.get_client()
        response = client.post(
            "/v1/login",
            json={"username": email, "password": password, "grant_type": "password"},
        )
        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert self.is_valid_token(response.json()["access_token"])

        jwt_claim = self.get_jwt_claim(response.json()["access_token"])
        assert jwt_claim.sub == user.id

        custom_claims = jwt_claim.custom_claims
        assert custom_claims.user_id == user.id
        assert custom_claims.role == user.role
        assert custom_claims.organization_id == organization.id
        assert custom_claims.organization_role == organization.role
        assert custom_claims.impersonator_user_id is None
        assert custom_claims.impersonator_user_role is None
        assert custom_claims.impersonator_organization_id is None
        assert custom_claims.impersonator_organization_role is None

    async def test_login_as_cookie_returns_cookie(
        self, user_repository: UserRepository, ensure_clean_db: None
    ):
        email = "test@oly.co"
        password = "test_password_123_$$%"

        user: SensitiveUser = build_new_user(
            email=email, password=password, role=UserRole.USER
        )
        user.activate()
        user.confirm(user.confirmation_token)

        await user_repository.save_user(user)

        client = self.get_client()
        response = client.post(
            "/v1/login",
            headers={"Origin": "http://test-local-app.fastapi-auth-server.com"},
            json={"username": email, "password": password, "grant_type": "password"},
            params={"as_cookie": True},
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.cookies["jwt_access_token"]
        assert self.is_valid_token(response.cookies["jwt_access_token"])

    async def test_login_as_cookie_for_unallowed_origin_returns_error(
        self, user_repository: UserRepository, ensure_clean_db: None
    ):
        email = "test@oly.co"
        password = "test_password_123_$$%"

        user: SensitiveUser = build_new_user(
            email=email, password=password, role=UserRole.USER
        )
        user.activate()
        user.confirm(user.confirmation_token)

        await user_repository.save_user(user)

        client = self.get_client()
        response = client.post(
            "/v1/login",
            headers={"Origin": "http://bumblefoot.fastapi-auth-server.com"},
            json={"username": email, "password": password, "grant_type": "password"},
            params={"as_cookie": True},
        )

        assert response.status_code == 400

    async def test_login_as_cookie_for_allowed_origin_but_for_different_domain_is_inaccessible(
        self, user_repository: UserRepository, ensure_clean_db: None
    ):
        email = "test@oly.co"
        password = "test_password_123_$$%"

        user: SensitiveUser = build_new_user(
            email=email, password=password, role=UserRole.USER
        )
        user.activate()
        user.confirm(user.confirmation_token)

        await user_repository.save_user(user)

        client = self.get_client()
        response = client.post(
            "/v1/login",
            headers={"Origin": "http://test-app.fastapi-auth-server.com"},
            json={"username": email, "password": password, "grant_type": "password"},
            params={"as_cookie": True},
        )

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert len(response.cookies) == 0

    def test_logout_removes_cookie(self):
        client = self.get_client()
        client.cookies = {"jwt_access_token": "Bearer test_token"}
        response = client.post("v1/logout")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert "jwt_access_token" not in response.cookies


class TestMe:
    def get_client(self) -> TestClient:
        return TestClient(app)

    async def test_me_with_valid_token(self, user_repository: UserRepository):
        email = "test@oly.co"
        password = "test_password_123_$$%"

        user: SensitiveUser = build_new_user(
            email=email, password=password, role=UserRole.USER
        )
        user.activate()
        user.confirm(user.confirmation_token)

        await user_repository.save_user(user)

        client = self.get_client()
        response = client.post(
            "/v1/login",
            json={"username": email, "password": password, "grant_type": "password"},
        )
        access_token = response.json()["access_token"]

        # act
        response = client.get(
            "/v1/me",
            headers={"X-Oly-Authorization": f"Bearer {access_token}"},
        )

        response_data = response.json()

        assert response.status_code == 200
        assert response_data["email"] == email
        assert response_data["role"] == UserRole.USER
        assert response_data["is_activated"] is True
        assert response_data["is_confirmed"] is True

    async def test_me_unauthorized(self):
        client = self.get_client()

        # act
        response = client.get(
            "/v1/me",
            headers={"X-Oly-Authorization": "Bearer beluga"},
        )

        assert response.status_code == 401

from typing import Annotated, List, Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from src.apps.auth.models.organization import Organization
from src.apps.auth.repository.organizations import OrganizationsRepository
from src.lib_auth.roles import UserRole

from ..app import app
from ..dependencies import (
    get_authenticated_platform_owner,
    get_authenticated_user,
    organizations_repository,
    user_repository,
)
from ..models.user import (
    InvalidEmailException,
    PasswordNotStrongException,
    User,
    build_new_user,
)
from ..repository.users import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/login")


class CreateUserRequest(BaseModel):
    email: str
    password: str
    confirm_password: str
    first_name: str
    last_name: str


class SimpleSuccessResponse(BaseModel):
    status: str = "ok"
    email: str


@app.post("/v1/users")
async def create(
    request: CreateUserRequest,
    user_repository: Annotated[UserRepository, Depends(user_repository)],
    authenticated_platform_owner: Annotated[
        User, Depends(get_authenticated_platform_owner)
    ],
):
    existing_user = await user_repository.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        user = build_new_user(
            email=request.email,
            password=request.password,
            role=UserRole.USER,
            first_name=request.first_name,
            last_name=request.last_name,
        )
        await user_repository.save_user(user)
    except (PasswordNotStrongException, InvalidEmailException) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # TODO : send email confirmation

    return SimpleSuccessResponse(email=request.email)


class UserSearchParams(BaseModel):
    username_contains: Optional[str] = None
    organization_id: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


def get_user_search_params(
    username_contains: str | None = None,
    organization_id: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
):
    return UserSearchParams(
        username_contains=username_contains,
        organization_id=organization_id,
        limit=limit,
        offset=offset,
    )


@app.get("/v1/users")
async def list(
    user_repository: Annotated[UserRepository, Depends(user_repository)],
    authenticated_platform_owner: Annotated[
        User, Depends(get_authenticated_platform_owner)
    ],
    user_search_params: UserSearchParams = Depends(get_user_search_params),
) -> List[User]:
    users = await user_repository.get_users(**user_search_params.model_dump())
    return users


@app.get("/v1/user/{user_id}")
async def get(
    user_repository: Annotated[UserRepository, Depends(user_repository)],
    authenticated_platform_owner: Annotated[
        User, Depends(get_authenticated_platform_owner)
    ],
    user_id: str,
) -> User:
    user = await user_repository.get_user_by_id(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class UpdateUserRequest(BaseModel):
    email: str
    first_name: str
    last_name: str
    role: UserRole
    is_activated: bool
    is_confirmed: bool
    organization_id: str = ""


@app.put("/v1/user/{user_id}")
async def update(
    user_repository: Annotated[UserRepository, Depends(user_repository)],
    organizations_repository: Annotated[
        OrganizationsRepository, Depends(organizations_repository)
    ],
    authenticated_user: Annotated[User, Depends(get_authenticated_user)],
    user_id: str,
    request: UpdateUserRequest,
) -> User:
    if authenticated_user.is_platform_owner():
        return await __update_as_platform_owner(
            user_repository,
            organizations_repository,
            authenticated_user,
            user_id,
            request,
        )

    return await __update_as_platform_user(
        user_repository, authenticated_user, user_id, request
    )


async def __update_as_platform_owner(
    user_repository: UserRepository,
    organizations_repository: OrganizationsRepository,
    authenticated_user: User,
    user_id: str,
    request: UpdateUserRequest,
) -> User:
    if not authenticated_user.is_platform_owner():
        raise HTTPException(status_code=403, detail="Forbidden")

    user_to_edit = await user_repository.get_user_by_id(user_id)
    if not user_to_edit:
        raise HTTPException(status_code=404, detail="User not found")

    organization: Organization | None = None
    if request.organization_id:
        organizaton = await organizations_repository.get_organization(
            request.organization_id
        )
        if not organizaton:
            raise HTTPException(status_code=404, detail="Organization not found")

    user_to_edit.email = request.email
    user_to_edit.first_name = request.first_name
    user_to_edit.last_name = request.last_name
    user_to_edit.role = request.role
    user_to_edit.organization = organization
    user_to_edit.is_activated = request.is_activated
    user_to_edit.is_confirmed = request.is_confirmed

    await user_repository.save_user(user_to_edit)
    user_to_return = await user_repository.get_user_by_id(user_id)
    if not user_to_return:
        raise HTTPException(status_code=404, detail="Failed to fetch user after update")
    return user_to_return


async def __update_as_platform_user(
    user_repository: UserRepository,
    authenticated_user: User,
    user_id: str,
    request: UpdateUserRequest,
) -> User:
    if authenticated_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    user_to_edit = await user_repository.get_user_by_id(user_id)
    if not user_to_edit:
        raise HTTPException(status_code=404, detail="User not found")

    user_to_edit.email = request.email
    user_to_edit.first_name = request.first_name
    user_to_edit.last_name = request.last_name
    # do not allow to change role, organization, self-activate, or self-confirm

    await user_repository.save_user(user_to_edit)

    user_to_return = await user_repository.get_user_by_id(user_id)
    if not user_to_return:
        raise HTTPException(status_code=404, detail="Failed to fetch user after update")
    return user_to_return

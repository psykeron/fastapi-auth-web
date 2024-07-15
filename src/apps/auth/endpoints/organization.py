from typing import Annotated, List, Optional

from fastapi import Depends, Request
from fastapi import status as HTTPStatus
from fastapi import status as http_status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.apps.auth.dependencies import (
    get_authenticated_platform_owner,
    get_authenticated_user,
    organizations_repository,
)
from src.apps.auth.models.organization import Organization
from src.apps.auth.models.user import User
from src.apps.auth.repository.organizations import (
    OrganizationExistsError,
    OrganizationNotFoundError,
    OrganizationsRepository,
)
from src.lib_auth.roles import OrganizationRole

from ..app import app


@app.exception_handler(OrganizationExistsError)
async def organization_already_exists_handler(
    request: Request, exc: OrganizationExistsError
):
    return JSONResponse(
        status_code=http_status.HTTP_409_CONFLICT,
        content={"error": "Organization with this name already exists."},
    )


@app.exception_handler(OrganizationNotFoundError)
async def organization_not_found_handler(
    request: Request, exc: OrganizationNotFoundError
):
    return JSONResponse(
        status_code=http_status.HTTP_404_NOT_FOUND,
        content={"error": "Organization not found."},
    )


class OrganizationCreateRequest(BaseModel):
    name: str
    description: str
    role: OrganizationRole


class OrganizationUpdateRequest(BaseModel):
    id: str
    name: str
    description: str
    role: OrganizationRole


# create organization
@app.post("/v1/organizations")
async def create_organization(
    authenticated_platform_owner: Annotated[
        User, Depends(get_authenticated_platform_owner)
    ],
    organizations_repository: Annotated[
        OrganizationsRepository, Depends(organizations_repository)
    ],
    create_organization_request: OrganizationCreateRequest,
) -> Organization:
    saved_organization = await organizations_repository.create_organization(
        Organization(
            name=create_organization_request.name,
            description=create_organization_request.description,
            role=create_organization_request.role,
        )
    )

    return saved_organization


# update organization
@app.put("/v1/organizations")
async def update_organization(
    authenticated_platform_owner: Annotated[
        User, Depends(get_authenticated_platform_owner)
    ],
    organizations_repository: Annotated[
        OrganizationsRepository, Depends(organizations_repository)
    ],
    update_organization_request: OrganizationUpdateRequest,
) -> Organization:
    saved_organization = await organizations_repository.update_organization(
        Organization(
            id=update_organization_request.id,
            name=update_organization_request.name,
            description=update_organization_request.description,
            role=update_organization_request.role,
        )
    )

    return saved_organization


# delete organization
@app.delete("/v1/organizations/{organization_id}")
async def delete_organization():
    raise HTTPException(HTTPStatus.HTTP_501_NOT_IMPLEMENTED, "Not implemented")


class OrganizationsSearchParams(BaseModel):
    name_contains: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


def get_organization_search_params(
    limit: int | None = None,
    offset: int | None = None,
    name_contains: str | None = None,
):
    return OrganizationsSearchParams(
        name_contains=name_contains, limit=limit, offset=offset
    )


# get organizations
@app.get("/v1/organizations")
async def get_organizations(
    authenticated_platform_owner: Annotated[
        User, Depends(get_authenticated_platform_owner)
    ],
    organizations_repository: Annotated[
        OrganizationsRepository, Depends(organizations_repository)
    ],
    params: OrganizationsSearchParams = Depends(get_organization_search_params),
) -> List[Organization]:
    organizations = await organizations_repository.get_organizations(
        **params.model_dump()
    )
    return organizations


# get organization by id
@app.get("/v1/organization/{organization_id}")
async def get_organization_by_id(
    authenticated_user: Annotated[User, Depends(get_authenticated_user)],
    organizations_repository: Annotated[
        OrganizationsRepository, Depends(organizations_repository)
    ],
    organization_id: str,
) -> Organization:
    organization: Organization | None = None

    if not authenticated_user.organization:
        raise HTTPException(HTTPStatus.HTTP_403_FORBIDDEN, "Forbidden")

    if authenticated_user.organization.role == OrganizationRole.PLATFORM_OWNER:
        organization = await organizations_repository.get_organization(organization_id)
    elif authenticated_user.organization.id == organization_id:
        organization = authenticated_user.organization
    else:
        raise HTTPException(HTTPStatus.HTTP_403_FORBIDDEN, "Forbidden")

    if not organization:
        raise HTTPException(HTTPStatus.HTTP_404_NOT_FOUND, "Organization not found")

    return organization

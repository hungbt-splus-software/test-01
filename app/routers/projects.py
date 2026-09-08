from fastapi import APIRouter, Depends, Query, status

from app.deps import get_project_service
from app.exceptions import DeskError
from app.http_errors import http_error
from app.schemas import ProjectCreate, ProjectOut
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
def list_projects(
    archived: bool | None = Query(default=None),
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectOut]:
    return [
        ProjectOut.model_validate(project, from_attributes=True)
        for project in service.list_projects(archived)
    ]


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectOut:
    try:
        project = service.create_project(payload.name, payload.slug)
        return ProjectOut.model_validate(project, from_attributes=True)
    except DeskError as exc:
        raise http_error(exc) from exc


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> ProjectOut:
    try:
        project = service.get_project(project_id)
        return ProjectOut.model_validate(project, from_attributes=True)
    except DeskError as exc:
        raise http_error(exc) from exc


@router.post("/{project_id}/archive", response_model=ProjectOut)
def archive_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
) -> ProjectOut:
    try:
        project = service.archive(project_id)
        return ProjectOut.model_validate(project, from_attributes=True)
    except DeskError as exc:
        raise http_error(exc) from exc

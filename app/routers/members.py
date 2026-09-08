from fastapi import APIRouter, Depends, Query, status

from app.deps import get_member_service
from app.exceptions import DeskError
from app.http_errors import http_error
from app.schemas import MemberCreate, MemberOut
from app.services.member_service import MemberService

router = APIRouter(prefix="/members", tags=["members"])


@router.get("", response_model=list[MemberOut])
def list_members(
    active: bool | None = Query(default=None),
    service: MemberService = Depends(get_member_service),
) -> list[MemberOut]:
    return [
        MemberOut.model_validate(member, from_attributes=True)
        for member in service.list_members(active)
    ]


@router.post("", response_model=MemberOut, status_code=status.HTTP_201_CREATED)
def create_member(
    payload: MemberCreate,
    service: MemberService = Depends(get_member_service),
) -> MemberOut:
    try:
        member = service.create_member(payload.username, payload.display_name)
        return MemberOut.model_validate(member, from_attributes=True)
    except DeskError as exc:
        raise http_error(exc) from exc


@router.get("/{member_id}", response_model=MemberOut)
def get_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
) -> MemberOut:
    try:
        member = service.get_member(member_id)
        return MemberOut.model_validate(member, from_attributes=True)
    except DeskError as exc:
        raise http_error(exc) from exc


@router.post("/{member_id}/deactivate", response_model=MemberOut)
def deactivate_member(
    member_id: int,
    service: MemberService = Depends(get_member_service),
) -> MemberOut:
    try:
        member = service.deactivate(member_id)
        return MemberOut.model_validate(member, from_attributes=True)
    except DeskError as exc:
        raise http_error(exc) from exc

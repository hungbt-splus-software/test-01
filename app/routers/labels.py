from fastapi import APIRouter, Depends, status

from app.deps import get_label_service
from app.exceptions import DeskError
from app.http_errors import http_error
from app.schemas import LabelCreate, LabelOut
from app.services.label_service import LabelService

router = APIRouter(prefix="/labels", tags=["labels"])


@router.get("", response_model=list[LabelOut])
def list_labels(service: LabelService = Depends(get_label_service)) -> list[LabelOut]:
    return [
        LabelOut.model_validate(label, from_attributes=True) for label in service.list_labels()
    ]


@router.post("", response_model=LabelOut, status_code=status.HTTP_201_CREATED)
def create_label(
    payload: LabelCreate,
    service: LabelService = Depends(get_label_service),
) -> LabelOut:
    try:
        label = service.create_label(payload.name, payload.slug)
        return LabelOut.model_validate(label, from_attributes=True)
    except DeskError as exc:
        raise http_error(exc) from exc

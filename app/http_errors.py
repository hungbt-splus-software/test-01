from fastapi import HTTPException, status

from app.exceptions import (
    DeskError,
    DuplicateLabelError,
    DuplicateMemberError,
    DuplicateProjectError,
    InvalidSlugError,
    InvalidStatusTransition,
    InvalidUsernameError,
    InvalidWorklogError,
    LabelAlreadyAttachedError,
    LabelLimitError,
    LabelNotFound,
    MemberHasActiveTicketsError,
    MemberInactiveError,
    MemberNotFound,
    ProjectArchivedError,
    ProjectHasOpenTicketsError,
    ProjectNotFound,
    TicketClosedError,
    TicketNotFound,
    WorklogLimitError,
)

_NOT_FOUND = (
    TicketNotFound,
    MemberNotFound,
    ProjectNotFound,
    LabelNotFound,
)
_BAD_REQUEST = (
    InvalidUsernameError,
    InvalidSlugError,
    InvalidWorklogError,
)
_CONFLICT = (
    InvalidStatusTransition,
    TicketClosedError,
    DuplicateMemberError,
    MemberInactiveError,
    MemberHasActiveTicketsError,
    DuplicateProjectError,
    ProjectArchivedError,
    ProjectHasOpenTicketsError,
    DuplicateLabelError,
    LabelAlreadyAttachedError,
    LabelLimitError,
    WorklogLimitError,
)


def http_error(exc: Exception) -> HTTPException:
    if isinstance(exc, _NOT_FOUND):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, _BAD_REQUEST):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, _CONFLICT):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    if isinstance(exc, DeskError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc

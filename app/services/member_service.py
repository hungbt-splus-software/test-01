from app.exceptions import (
    DuplicateMemberError,
    InvalidUsernameError,
    MemberHasActiveTicketsError,
    MemberNotFound,
)
from app.models import Member, TicketStatus
from app.store import InMemoryStore
from app.text import is_valid_username, normalize_username

ACTIVE_STATUSES = {TicketStatus.OPEN, TicketStatus.IN_PROGRESS}


class MemberService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def list_members(self, active: bool | None = None) -> list[Member]:
        members = self.store.list_members()
        if active is not None:
            members = [member for member in members if member.active is active]
        return sorted(members, key=lambda member: member.id)

    def get_member(self, member_id: int) -> Member:
        member = self.store.get_member(member_id)
        if member is None:
            raise MemberNotFound(member_id)
        return member

    def create_member(self, username: str, display_name: str) -> Member:
        normalized = normalize_username(username)
        if not is_valid_username(normalized):
            raise InvalidUsernameError(username)
        if self.store.get_member_by_username(normalized):
            raise DuplicateMemberError(normalized)
        return self.store.create_member(normalized, display_name.strip())

    def deactivate(self, member_id: int) -> Member:
        member = self.get_member(member_id)
        active_count = sum(
            1
            for ticket in self.store.list_all()
            if ticket.assignee == member.username and ticket.status in ACTIVE_STATUSES
        )
        if active_count:
            raise MemberHasActiveTicketsError(member.username, active_count)
        member.active = False
        return member

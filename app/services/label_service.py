from app.constants import MAX_LABELS_PER_TICKET
from app.exceptions import (
    DuplicateLabelError,
    InvalidSlugError,
    LabelAlreadyAttachedError,
    LabelLimitError,
    LabelNotFound,
    TicketClosedError,
    TicketNotFound,
)
from app.models import Label, Ticket, TicketStatus
from app.store import InMemoryStore
from app.text import is_valid_slug, slugify


class LabelService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def list_labels(self) -> list[Label]:
        return sorted(self.store.list_labels(), key=lambda label: label.id)

    def get_label(self, label_id: int) -> Label:
        label = self.store.get_label(label_id)
        if label is None:
            raise LabelNotFound(label_id)
        return label

    def create_label(self, name: str, slug: str | None = None) -> Label:
        resolved = slugify(slug or name)
        if not is_valid_slug(resolved):
            raise InvalidSlugError(slug or name)
        if self.store.get_label_by_slug(resolved):
            raise DuplicateLabelError(resolved)
        return self.store.create_label(name.strip(), resolved)

    def attach(self, ticket_id: int, label_id: int) -> Ticket:
        ticket = self._get_writable_ticket(ticket_id)
        label = self.get_label(label_id)
        if label.id in ticket.label_ids:
            raise LabelAlreadyAttachedError(ticket.id, label.id)
        if len(ticket.label_ids) >= MAX_LABELS_PER_TICKET:
            raise LabelLimitError(ticket.id, MAX_LABELS_PER_TICKET)
        ticket.label_ids.append(label.id)
        return ticket

    def detach(self, ticket_id: int, label_id: int) -> Ticket:
        ticket = self._get_writable_ticket(ticket_id)
        self.get_label(label_id)
        ticket.label_ids = [item for item in ticket.label_ids if item != label_id]
        return ticket

    def _get_writable_ticket(self, ticket_id: int) -> Ticket:
        ticket = self.store.get(ticket_id)
        if ticket is None:
            raise TicketNotFound(ticket_id)
        if ticket.status == TicketStatus.CLOSED:
            raise TicketClosedError(ticket.id, "label")
        return ticket

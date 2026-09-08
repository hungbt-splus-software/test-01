from app.models import Priority, Ticket, TicketStatus


class InMemoryStore:
    """Process-local store. Enough for dummy CRUD and unit tests."""

    def __init__(self) -> None:
        self.tickets: dict[int, Ticket] = {}
        self._next_id = 1
        self._seed()

    def _seed(self) -> None:
        first = self.create_ticket(
            title="Welcome to Desk",
            description="Dummy ticket so the board is not empty.",
            priority=Priority.LOW,
            assignee="maya",
        )
        first.add_comment("Looks good, we can use this as a fixture.", "kai")

        second = self.create_ticket(
            title="Broken login banner",
            description="Banner overflows on narrow screens.",
            priority=Priority.HIGH,
            assignee="linh",
        )
        second.status = TicketStatus.IN_PROGRESS

    def create_ticket(
        self,
        title: str,
        description: str,
        priority: Priority,
        assignee: str | None,
    ) -> Ticket:
        ticket = Ticket(
            id=self._next_id,
            title=title,
            description=description,
            priority=priority,
            assignee=assignee,
        )
        self.tickets[ticket.id] = ticket
        self._next_id += 1
        return ticket

    def get(self, ticket_id: int) -> Ticket | None:
        return self.tickets.get(ticket_id)

    def list_all(self) -> list[Ticket]:
        return list(self.tickets.values())

    def delete(self, ticket_id: int) -> None:
        self.tickets.pop(ticket_id, None)

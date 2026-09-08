class DeskError(Exception):
    """Base error for domain rules."""


class TicketNotFound(DeskError):
    def __init__(self, ticket_id: int) -> None:
        self.ticket_id = ticket_id
        super().__init__(f"Ticket {ticket_id} was not found")


class InvalidStatusTransition(DeskError):
    def __init__(self, current: str, target: str) -> None:
        self.current = current
        self.target = target
        super().__init__(f"Cannot move ticket from {current} to {target}")


class TicketClosedError(DeskError):
    def __init__(self, ticket_id: int, action: str) -> None:
        self.ticket_id = ticket_id
        self.action = action
        super().__init__(f"Cannot {action} closed ticket {ticket_id}")

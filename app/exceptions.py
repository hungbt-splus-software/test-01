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


class MemberNotFound(DeskError):
    def __init__(self, key: int | str) -> None:
        self.key = key
        super().__init__(f"Member {key} was not found")


class MemberInactiveError(DeskError):
    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Member {username} is inactive")


class DuplicateMemberError(DeskError):
    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Member {username} already exists")


class InvalidUsernameError(DeskError):
    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Invalid username {username}")


class MemberHasActiveTicketsError(DeskError):
    def __init__(self, username: str, count: int) -> None:
        self.username = username
        self.count = count
        super().__init__(f"Cannot deactivate {username}: {count} active ticket(s)")


class ProjectNotFound(DeskError):
    def __init__(self, key: int | str) -> None:
        self.key = key
        super().__init__(f"Project {key} was not found")


class ProjectArchivedError(DeskError):
    def __init__(self, project_id: int, action: str) -> None:
        self.project_id = project_id
        self.action = action
        super().__init__(f"Cannot {action} archived project {project_id}")


class DuplicateProjectError(DeskError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Project slug {slug} already exists")


class InvalidSlugError(DeskError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Invalid slug {slug}")


class ProjectHasOpenTicketsError(DeskError):
    def __init__(self, project_id: int, count: int) -> None:
        self.project_id = project_id
        self.count = count
        super().__init__(f"Cannot archive project {project_id}: {count} open ticket(s)")


class LabelNotFound(DeskError):
    def __init__(self, key: int | str) -> None:
        self.key = key
        super().__init__(f"Label {key} was not found")


class DuplicateLabelError(DeskError):
    def __init__(self, slug: str) -> None:
        self.slug = slug
        super().__init__(f"Label {slug} already exists")


class LabelAlreadyAttachedError(DeskError):
    def __init__(self, ticket_id: int, label_id: int) -> None:
        self.ticket_id = ticket_id
        self.label_id = label_id
        super().__init__(f"Label {label_id} is already on ticket {ticket_id}")


class LabelLimitError(DeskError):
    def __init__(self, ticket_id: int, limit: int) -> None:
        self.ticket_id = ticket_id
        self.limit = limit
        super().__init__(f"Ticket {ticket_id} already has {limit} labels")


class InvalidWorklogError(DeskError):
    def __init__(self, hours: float) -> None:
        self.hours = hours
        super().__init__(f"Worklog hours {hours} must be > 0 and <= 12")


class WorklogLimitError(DeskError):
    def __init__(self, ticket_id: int, total: float, limit: float) -> None:
        self.ticket_id = ticket_id
        self.total = total
        self.limit = limit
        super().__init__(f"Ticket {ticket_id} cannot exceed {limit} logged hours (now {total})")

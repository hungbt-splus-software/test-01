from app.models import Label, Member, Priority, Project, Ticket, TicketStatus
from app.sla import due_at_for


class InMemoryStore:
    """Process-local store. Enough for dummy CRUD and unit tests."""

    def __init__(self) -> None:
        self.tickets: dict[int, Ticket] = {}
        self.members: dict[int, Member] = {}
        self.projects: dict[int, Project] = {}
        self.labels: dict[int, Label] = {}
        self._next_ticket_id = 1
        self._next_member_id = 1
        self._next_project_id = 1
        self._next_label_id = 1
        self._seed()

    def _seed(self) -> None:
        maya = self.create_member("maya", "Maya Chen")
        linh = self.create_member("linh", "Linh Tran")
        self.create_member("kai", "Kai Nguyen")

        website = self.create_project("Website", "website")
        self.create_project("Mobile", "mobile")

        ui = self.create_label("UI", "ui")
        self.create_label("Backend", "backend")
        urgent = self.create_label("Urgent", "urgent")

        first = self.create_ticket(
            title="Welcome to Desk",
            description="Dummy ticket so the board is not empty.",
            priority=Priority.LOW,
            assignee=maya.username,
            project_id=website.id,
        )
        first.label_ids = [ui.id]
        first.add_comment("Looks good, we can use this as a fixture.", "kai")

        second = self.create_ticket(
            title="Broken login banner",
            description="Banner overflows on narrow screens.",
            priority=Priority.HIGH,
            assignee=linh.username,
            project_id=website.id,
        )
        second.status = TicketStatus.IN_PROGRESS
        second.label_ids = [ui.id, urgent.id]
        second.add_worklog(1.5, "linh", "Reproduce on 320px width")

        later = self.create_ticket(
            title="Bump copy on empty state",
            description="Shorten the empty-board sentence.",
            priority=Priority.MEDIUM,
            assignee=maya.username,
            project_id=website.id,
        )
        later.status = TicketStatus.RESOLVED

    def create_member(self, username: str, display_name: str) -> Member:
        member = Member(
            id=self._next_member_id,
            username=username,
            display_name=display_name,
        )
        self.members[member.id] = member
        self._next_member_id += 1
        return member

    def get_member(self, member_id: int) -> Member | None:
        return self.members.get(member_id)

    def get_member_by_username(self, username: str) -> Member | None:
        needle = username.lower()
        for member in self.members.values():
            if member.username == needle:
                return member
        return None

    def list_members(self) -> list[Member]:
        return list(self.members.values())

    def create_project(self, name: str, slug: str) -> Project:
        project = Project(id=self._next_project_id, name=name, slug=slug)
        self.projects[project.id] = project
        self._next_project_id += 1
        return project

    def get_project(self, project_id: int) -> Project | None:
        return self.projects.get(project_id)

    def get_project_by_slug(self, slug: str) -> Project | None:
        for project in self.projects.values():
            if project.slug == slug:
                return project
        return None

    def list_projects(self) -> list[Project]:
        return list(self.projects.values())

    def create_label(self, name: str, slug: str) -> Label:
        label = Label(id=self._next_label_id, name=name, slug=slug)
        self.labels[label.id] = label
        self._next_label_id += 1
        return label

    def get_label(self, label_id: int) -> Label | None:
        return self.labels.get(label_id)

    def get_label_by_slug(self, slug: str) -> Label | None:
        for label in self.labels.values():
            if label.slug == slug:
                return label
        return None

    def list_labels(self) -> list[Label]:
        return list(self.labels.values())

    def create_ticket(
        self,
        title: str,
        description: str,
        priority: Priority,
        assignee: str | None,
        project_id: int | None = None,
    ) -> Ticket:
        ticket = Ticket(
            id=self._next_ticket_id,
            title=title,
            description=description,
            priority=priority,
            assignee=assignee,
            project_id=project_id,
        )
        ticket.due_at = due_at_for(ticket.created_at, ticket.priority)
        self.tickets[ticket.id] = ticket
        self._next_ticket_id += 1
        return ticket

    def get(self, ticket_id: int) -> Ticket | None:
        return self.tickets.get(ticket_id)

    def list_all(self) -> list[Ticket]:
        return list(self.tickets.values())

    def delete(self, ticket_id: int) -> None:
        self.tickets.pop(ticket_id, None)

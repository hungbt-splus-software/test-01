from app.exceptions import (
    DuplicateProjectError,
    InvalidSlugError,
    ProjectArchivedError,
    ProjectHasOpenTicketsError,
    ProjectNotFound,
)
from app.models import Project, TicketStatus
from app.store import InMemoryStore
from app.text import is_valid_slug, slugify

OPENISH_STATUSES = {TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED}


class ProjectService:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def list_projects(self, archived: bool | None = None) -> list[Project]:
        projects = self.store.list_projects()
        if archived is not None:
            projects = [project for project in projects if project.archived is archived]
        return sorted(projects, key=lambda project: project.id)

    def get_project(self, project_id: int) -> Project:
        project = self.store.get_project(project_id)
        if project is None:
            raise ProjectNotFound(project_id)
        return project

    def create_project(self, name: str, slug: str | None = None) -> Project:
        resolved = slugify(slug or name)
        if not is_valid_slug(resolved):
            raise InvalidSlugError(slug or name)
        if self.store.get_project_by_slug(resolved):
            raise DuplicateProjectError(resolved)
        return self.store.create_project(name.strip(), resolved)

    def archive(self, project_id: int) -> Project:
        project = self.get_project(project_id)
        if project.archived:
            raise ProjectArchivedError(project_id, "archive")
        open_count = sum(
            1
            for ticket in self.store.list_all()
            if ticket.project_id == project.id and ticket.status in OPENISH_STATUSES
        )
        if open_count:
            raise ProjectHasOpenTicketsError(project.id, open_count)
        project.archived = True
        return project

import dataclasses

from .project import Project


@dataclasses.dataclass
class Workflow:
    id: int
    name: str
    project: Project
    timezone: str
    config: dict
    revision: str = ""
    createdAt: str = ""
    deletedAt: str = ""
    updatedAt: str = ""

    def __post_init__(self):
        self.id = int(self.id)
        self.project = Project(**self.project)

    @property
    def created_at(self):
        return self.createdAt

    @property
    def deleted_at(self):
        return self.deletedAt

    @property
    def updated_at(self):
        return self.updatedAt
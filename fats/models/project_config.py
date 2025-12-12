from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from ..utils.sqlite import Base


class ProjectConfig(Base):
    __tablename__ = "project_config"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str]
    version: Mapped[str]

    __table_args__ = (UniqueConstraint("name", "version", name="uix_name_version"),)

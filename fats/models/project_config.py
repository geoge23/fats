from sqlalchemy import JSON, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from fats.utils import json_str_list
from ..utils.sqlite import Base


class ProjectConfig(Base):
    __tablename__ = "project_config"

    name: Mapped[str]
    version: Mapped[str]
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    desired_secrets: Mapped[json_str_list] = mapped_column(JSON, default=list)

    __table_args__ = (UniqueConstraint("name", "version", name="uix_name_version"),)

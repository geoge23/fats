from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..utils import Base


class ServiceEntry(Base):
    __tablename__ = "service_entry"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    service_number: Mapped[int]
    container_id: Mapped[str]
    hostname: Mapped[str]
    port: Mapped[int]

    project_config_id: Mapped[int] = mapped_column(
        ForeignKey("project_config.id"), nullable=False
    )

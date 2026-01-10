from sqlalchemy.orm import Mapped, mapped_column
from ..utils import Base


class Secret(Base):
    __tablename__ = "secret"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, init=False)
    name: Mapped[str]
    value: Mapped[str]

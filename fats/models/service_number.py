from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped, mapped_column

from ..utils import Base, AsyncSessionLocal, log


class _ServiceNumber(Base):
    __tablename__ = "service_number"
    number: Mapped[int]
    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=False, init=True, default=1
    )  # Singleton, always 1


_current_service_number: Optional[int] = None


async def get_service_number() -> int:
    global _current_service_number
    """Retrieve a service number from the database that represents this execution of the program"""
    # get the singleton service number entry from the db and record it
    if _current_service_number is not None:
        return _current_service_number

    async with AsyncSessionLocal() as session:
        result = (
            await session.execute(select(_ServiceNumber).limit(1))
        ).scalar_one_or_none()
        if result is None:
            log("This must be the first execution, creating service number entry...")
            service_number_entry = _ServiceNumber(id=1, number=1)
            session.add(service_number_entry)
            await session.commit()
            _current_service_number = 1
            return 1
        else:
            _current_service_number = result.number + 1
            result.number = _current_service_number
            await session.commit()
            log(f"Retrieved service number {_current_service_number} from database")
            return _current_service_number

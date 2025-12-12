from datetime import timedelta
from .runner import setup_application_containers
from .scheduler import Schedule

create_containers_schedule = Schedule(
    friendly_name="Create Desired Application Containers",
    interval=timedelta(minutes=3),
    action=setup_application_containers,
)

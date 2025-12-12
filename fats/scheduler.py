import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine

from .utils import log

_schedules: list["Schedule"] = []


@dataclass
class Schedule:
    interval: timedelta
    action: Callable[[], Coroutine[Any, Any, Any]]  # callable
    friendly_name: str = "Unnamed Schedule"
    last_run: datetime = datetime.min

    def __post_init__(self):
        global _schedules
        _schedules.append(self)


async def _log_completion_of_task(task: asyncio.Task[Any], friendly_name: str):
    try:
        await task
        log(f"Scheduled action completed: {friendly_name}")
    except Exception as e:
        log(f"Scheduled action {friendly_name} raised an exception: {e}")


async def _scheduler_thread():
    """
    When executed in a separate task, this will run scheduled actions at their specified intervals
    """

    async with asyncio.TaskGroup() as tg:
        while True:
            now = datetime.now()
            for schedule in _schedules:
                if now - schedule.last_run >= schedule.interval:
                    log(f"Running scheduled action: {schedule.friendly_name}")
                    task = tg.create_task(schedule.action())
                    tg.create_task(
                        _log_completion_of_task(task, schedule.friendly_name)
                    )
                    schedule.last_run = now

            await asyncio.sleep(1)


def start_scheduler():
    """
    Start the scheduler thread in the background
    """
    log("Starting scheduler...")
    asyncio.create_task(_scheduler_thread())


def request_early_schedule_execution(schedule: Schedule):
    """
    Request that a schedule be executed as soon as possible
    """
    schedule.last_run = datetime.min

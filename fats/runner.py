# Find available application containers based on apps in the db
# Ensure they are running and given a PORT
# Record them in a service entry in the db

from asyncio import Task, TaskGroup
import re
from typing import List
from sqlalchemy import select
from random import randint

from fats.network import create_or_get_fats_network
from fats.models.project_config import ProjectConfig
from fats.models.service_entry import ServiceEntry
from fats.models.service_number import get_service_number
from fats.utils import AsyncSessionLocal, log, run


async def does_container_exist(container_name: str) -> bool:
    does_container_exist_proc = await run(
        "docker",
        "ps",
        "-q",
        "-f",
        f"name={container_name}",
    )
    await does_container_exist_proc.wait()
    assert (
        does_container_exist_proc.returncode == 0
    ), "Failed to check if container exists"
    assert (
        does_container_exist_proc.stdout is not None
    ), "Failed to get container existence output"
    container_exists = (
        await does_container_exist_proc.stdout.read()
    ).decode().strip() != ""

    return container_exists


async def homogenize_or_destroy_service_entry(entry: ServiceEntry) -> bool:
    """
    Given a service entry that is orphaned (i.e., from a different service number),
    either homogenize it to match the current desired state or destroy it if it's no longer needed.

    Returns True if we were able to homogenize and its corresponding project can be considered running, false if not.
    """
    current_service_number = await get_service_number()

    async with AsyncSessionLocal() as session:
        # refetch to ensure we operate on the latest state
        tracked_entry = await session.get(ServiceEntry, entry.id)
        project = await session.get(ProjectConfig, entry.project_config_id)

        if tracked_entry is None:
            return False

        # If the project no longer exists or a container with this hostname does not exist, drop the container and delete the entry
        if project is None or not await does_container_exist(entry.hostname):
            log(
                f"Destroying service entry {entry.id} for project config {entry.project_config_id} as it is no longer valid."
            )
            proc = await run("docker", "rm", "-f", entry.container_id)
            await proc.wait()
            await session.delete(tracked_entry)
            await session.commit()
            return False

        # Otherwise, we can homogenize. Just update the service number
        tracked_entry.service_number = current_service_number
        await session.commit()
        log(
            f"Homogenized service entry {entry.id} for project config {entry.project_config_id} to service number {current_service_number}."
        )
        return True


async def create_container_for_app(
    app: ProjectConfig, service_number: int
) -> ServiceEntry:
    # Use docker to create a container for the app
    # Record the container ID and port in a new ServiceEntry

    # generate a random userspace port
    port = randint(20000, 60000)

    name_version_sanitized = re.sub(r'[^a-zA-Z0-9-]+', '', app.name + app.version)
    salt = randint(1000, 9999)

    container_name = f"fats-{name_version_sanitized}-{salt}"

    proc = await run(
        "docker",
        "run",
        "-d",
        "--name",
        container_name,
        "--network",
        await create_or_get_fats_network(),
        "-e",
        f"FATS_SERVICE_NUMBER={service_number}",
        "-e",
        f"FATS_PROJECT_CONFIG_ID={app.id}",
        "-e",
        f"PORT={port}",
        f"{app.name}:{app.version}",
    )

    await proc.wait()

    assert proc.returncode == 0, "Failed to start container"
    assert proc.stdout is not None, "Failed to get container ID"
    container_id = (await proc.stdout.read()).decode().strip()

    log(f"Started container {container_name} with ID {container_id} on port {port}")

    return ServiceEntry(
        service_number=service_number,
        container_id=container_id,
        hostname=container_name,
        port=port,
        project_config_id=app.id,
    )


async def setup_application_containers():
    """
    Idempotently ensure that application containers are running for all desired apps
    Also ensure all service entries directly match a real, running container
    """
    # First, let's find any app containers that have service entries. We should check if they run from other versions of fats
    current_service_number = await get_service_number()
    async with AsyncSessionLocal() as session:
        svc_entries = (await session.execute(select(ServiceEntry))).scalars().all()
        desired_apps = (await session.execute(select(ProjectConfig))).scalars().all()

        hm_desired_apps = {app.id: app for app in desired_apps}

    for entry in svc_entries:
        if entry.service_number != current_service_number:
            # This service entry is from a different fats execution and therefore orphaned
            # We should see if we can homogenize it or destroy it
            did_homogenize = await homogenize_or_destroy_service_entry(entry)
            if did_homogenize:
                # If we homogenized, we can consider this app as already running
                del hm_desired_apps[entry.project_config_id]
            continue

        # Otherwise, we should check if the service entry matches a desired app
        # and check it off our list if its already present

        if entry.project_config_id in hm_desired_apps:
            del hm_desired_apps[entry.project_config_id]

    log(
        f"{len(hm_desired_apps)} applications need new containers out of {len(desired_apps)} desired applications."
    )

    # Ok, for those that remain, let's create new containers and service entries
    async with TaskGroup() as tg:
        se_tasks: List[Task[ServiceEntry]] = []
        for app in hm_desired_apps.values():
            se_tasks.append(
                tg.create_task(create_container_for_app(app, current_service_number))
            )

    # Now let's add all these to the db
    async with AsyncSessionLocal() as session:
        for se_task in se_tasks:
            service_entry = se_task.result()
            session.add(service_entry)
        await session.commit()

    # All done!
    return

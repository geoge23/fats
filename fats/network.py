import re
from socket import gethostname
from .utils import run, log

_does_network_exist_cache = False


async def create_or_get_fats_network() -> str:
    """Creates the FATS Docker network if it doesn't exist, or returns the existing one."""
    network_name = "fats_network"
    global _does_network_exist_cache
    if _does_network_exist_cache:
        return network_name
    # Check if the network already exists
    proc = await run(
        "docker",
        "network",
        "ls",
        "--filter",
        f"name={network_name}",
        "--format",
        "{{.Name}}",
    )
    await proc.wait()
    assert proc.stdout is not None, "Failed to get stdout from docker network ls"
    output = (await proc.stdout.read()).decode().strip()

    if network_name in output.splitlines():
        _does_network_exist_cache = True
        return network_name

    # Create the network
    proc = await run("docker", "network", "create", network_name)
    await proc.wait()
    assert proc.returncode == 0, "Failed to create FATS network"
    log(f"Created FATS network '{network_name}'.")
    return network_name


def determine_self_container_id() -> str:
    # Let's see if our hostname looks like a container ID
    hostname = gethostname()
    if len(hostname) == 12 and re.match(r"^[0-9a-f]+$", hostname):
        return hostname

    raise RuntimeError("Unable to determine self container ID from hostname.")


async def connect_self_to_network():
    """Connects the current container to the FATS network."""
    network_name = await create_or_get_fats_network()
    container_id = determine_self_container_id()
    proc = await run("docker", "network", "connect", network_name, container_id)
    await proc.wait()
    assert proc.returncode == 0, "Failed to connect self to FATS network"
    log(f"Connected container '{container_id}' to FATS network '{network_name}'.")
    pass

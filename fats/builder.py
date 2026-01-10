# receive and unpack zip
# create railpack plan
# ask kindly for buildx to build the railpack
# docker buildx build \
#   --build-arg BUILDKIT_SYNTAX="ghcr.io/railwayapp/railpack-frontend" \
#   -f /path/to/railpack-plan.json \
#   /path/to/app/to/build

from pathlib import Path
import tempfile
from typing import List
from aiofiles import os
import aiofiles
import httpx
import tarfile

from .models.project_config import ProjectConfig
from .utils import log, run
from sys import platform
import re
import logging
import configparser
import os as sync_os
import shutil

logger = logging.getLogger(__name__)


# From https://github.com/opencontainers/distribution-spec/blob/9d1b92567f2c7e5061a82e70b6fecbb1b0498b71/spec.md#pulling-manifests
DOCKER_NAME_REGEX = re.compile(
    r"[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*(\/[a-z0-9]+((\.|_|__|-+)[a-z0-9]+)*)*"
)

GLOBAL_TEMP_DIR = Path(tempfile.mkdtemp(prefix="fats_"))


def validate_docker(name: str, version: str) -> None:
    if not DOCKER_NAME_REGEX.fullmatch(name) or len(name) > 255:
        raise ValueError(f"Invalid docker name: {name}")
    if not re.fullmatch(DOCKER_NAME_REGEX, version) or len(version) > 128:
        raise ValueError(f"Invalid docker version: {version}")


async def retrieve_railpack_bin() -> Path:
    """
    Retrieve the path to the railpack binary. If not found, download it.
    """
    target_path = Path("/usr/local/bin/railpack")
    # check if unix, if not kill
    if platform != "linux":
        raise EnvironmentError("Unsupported platform. Only Linux is supported.")

    # check if we have perms for /usr/local/bin
    if not await os.access("/usr/local/bin", sync_os.W_OK):
        # otherwise use temp dir
        target_path = GLOBAL_TEMP_DIR / "railpack"

    if target_path.exists():
        return target_path

    # determine architecture for the railpack binary release naming
    machine = sync_os.uname().machine.lower()
    if machine in ("aarch64", "arm64"):
        arch = "arm64"
    elif machine in ("x86_64", "amd64"):
        arch = "x86_64"
    else:
        raise EnvironmentError(f"Unsupported architecture: {machine}")

    version_tag = "v0.15.1"
    url = f"https://github.com/railwayapp/railpack/releases/download/{version_tag}/railpack-{version_tag}-{arch}-unknown-linux-musl.tar.gz"
    async with httpx.AsyncClient().stream(
        "GET", url, timeout=30, follow_redirects=True
    ) as response:
        response.raise_for_status()
        tarball_path = GLOBAL_TEMP_DIR / "railpack.tar.gz"
        async with aiofiles.open(tarball_path, "wb") as out_file:
            async for chunk in response.aiter_bytes():
                await out_file.write(chunk)

    # extract tarball
    with tarfile.open(tarball_path, "r:gz") as tar:
        railpack_bin = tar.extractfile("railpack")
        if not railpack_bin:
            raise FileNotFoundError("railpack binary not found in the tarball.")
        with open(target_path, "wb") as f:
            f.write(railpack_bin.read())
    target_path.chmod(0o755)
    return target_path


def parse_options_or_else(dir: Path) -> ProjectConfig:
    # look for an options.ini file in the root of the tarball
    # try to come up with name= and version= or just make a name up from the dir name
    config = configparser.ConfigParser()
    options_path = dir / "options.ini"
    options = ProjectConfig(name=dir.name, version="0.0.1")
    if options_path.exists():
        config.read(options_path)
        if "name" in config["fats"]:
            options.name = config["fats"]["name"]
        if "version" in config["fats"]:
            options.version = config["fats"]["version"]
        if "desired_secrets" in config["fats"]:
            secrets_list = [
                s.strip()
                for s in config["fats"]["desired_secrets"].split(",")
                if s.strip()
            ]
            options.desired_secrets = secrets_list
        # if "fats.service_requests" in config:
        #     # get all service requests
        #     service_requests = ServiceRequests()
        #     for key in config["fats.service_requests"]:
        #         if hasattr(service_requests, key):
        #             setattr(
        #                 service_requests,
        #                 key,
        #                 config.getboolean("fats.service_requests", key),
        #             )
        #         else:
        #             raise ValueError(
        #                 f"Unknown service request: {key}. What are you trying to do?"
        #             )
        #     options.service_requests = service_requests
    return options


def _determine_correct_buildx_command() -> List[str]:
    # In railpack with aqua:docker/buildx, the buildx binary is called docker-cli-plugin-docker-buildx
    docker_buildx_path = shutil.which("docker-cli-plugin-docker-buildx")
    if docker_buildx_path:
        return [docker_buildx_path]
    # Fallback to just 'docker buildx'
    return ["docker", "buildx"]


async def build_railpack_from_tarball(tar_path: Path) -> ProjectConfig:
    temp_dir = Path(tempfile.mkdtemp())

    # extract tarball to temp dir
    log(f"Extracting tarball {tar_path} to {temp_dir}")
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(path=temp_dir)

    # detect if tarball has a single root folder, if so, use that as the temp_dir
    extracted_items = list(temp_dir.iterdir())
    if len(extracted_items) == 1 and extracted_items[0].is_dir():
        temp_dir = extracted_items[0]

    log(f"Extracted tarball to {temp_dir}")
    project_config = parse_options_or_else(temp_dir)
    log(f"Project config: {project_config}")

    # run railpack plan
    railpack_proc = await run(
        str(await retrieve_railpack_bin()),
        "prepare",
        str(temp_dir),
        "--plan-out",
        str(temp_dir / "railpack-plan.json"),
        "--info-out",
        str(temp_dir / "railpack-info.json"),
        steal_and_print_output=True,
    )
    await railpack_proc.wait()
    assert railpack_proc.returncode == 0, "Railpack prepare command failed"
    log("Railpack prepare command executed. Preparing buildx")

    validate_docker(project_config.name, project_config.version)

    tag = f"{project_config.name}:{project_config.version}"
    docker_proc = await run(
        *_determine_correct_buildx_command(),
        "build",
        "--build-arg",
        "BUILDKIT_SYNTAX=ghcr.io/railwayapp/railpack-frontend",
        "--tag",
        tag,
        "--progress=plain",
        "-f",
        str(temp_dir / "railpack-plan.json"),
        str(temp_dir),
        steal_and_print_output=True,
    )
    await docker_proc.wait()
    assert docker_proc.returncode == 0, "Docker buildx command failed"
    log("Docker buildx command executed.")

    return project_config

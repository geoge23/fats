# goal: take zip files of repos
# takes repos, auto builds nixpacks
# runs nixpacks and forwards http requests to them

from pathlib import Path
import tempfile
from fats.network import connect_self_to_network
from quart import Quart, request
import aiofiles
from sqlalchemy.exc import IntegrityError

from fats.secrets import upsert_secret

from .scheduler import request_early_schedule_execution, start_scheduler
from .utils.sqlite import create_tables

from .builder import build_railpack_from_tarball
from .utils import AsyncSessionLocal, log
from .schedules import create_containers_schedule
from .proxy import proxy_blueprint

app = Quart(__name__)


@app.before_serving
async def startup():
    await create_tables()
    await connect_self_to_network()
    start_scheduler()


@app.post("/mgmt/tar-upload")
async def handle_tar_upload():
    # stream store the tar to a file
    log("Receiving tar upload...")
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as temp_tar:
        async with aiofiles.open(temp_tar.name, "wb") as out_file:
            async for chunk in request.body:
                await out_file.write(chunk)

    log(f"Received tar upload, stored to {temp_tar.name}")

    # call builder to build the railpack from the tar
    project_config = await build_railpack_from_tarball(Path(temp_tar.name))

    # record the existence of the ProjectConfig in persistent sqlite
    async with AsyncSessionLocal() as session:
        try:
            session.add(project_config)
            await session.commit()
        except IntegrityError:
            # Already exists, lets overwrite
            log(
                f"ProjectConfig {project_config.name}:{project_config.version} already exists, overwriting..."
            )
            await session.rollback()
            existing = await session.get(type(project_config), project_config.id)
            if existing:
                for attr in vars(project_config):
                    setattr(existing, attr, getattr(project_config, attr))
                await session.commit()

    # Let's kindly ask the scheduler to run an early execution of the container setup
    request_early_schedule_execution(create_containers_schedule)

    return "Upload received", 200


@app.post("/mgmt/secret/<secret_name>")
async def handle_secret(secret_name: str):
    secret_data = await request.get_data()
    if not secret_data:
        return "Invalid secret value", 400
    secret_value = (
        secret_data.decode()
        if isinstance(secret_data, bytes | bytearray)
        else str(secret_data)
    )
    await upsert_secret(secret_name, secret_value)
    return "Secret uploaded", 200


app.register_blueprint(proxy_blueprint, url_prefix="/app")

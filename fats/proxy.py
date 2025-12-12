# Take incoming requests and proxy them to the appropriate application container based on
# the path and the service entries in the database


from typing import AsyncGenerator, Dict, NamedTuple
from async_lru import alru_cache
from httpx import AsyncClient
from quart import Blueprint, Response, request
from sqlalchemy import select
from werkzeug.datastructures import Headers

from .models.project_config import ProjectConfig
from .models.service_entry import ServiceEntry
from .utils import AsyncSessionLocal, debug
from urllib.parse import urlunsplit


# Direct copy from internal urllib parse
class Components(NamedTuple):
    scheme: str
    netloc: str
    url: str
    query: str
    fragment: str


_client = AsyncClient(
    timeout=None,  # Disable timeouts for long-lived connections,
    follow_redirects=True,
)

proxy_blueprint = Blueprint("proxy", __name__)

# These are not to be forwarded by the proxy
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}


@alru_cache(ttl=300)
async def get_target_from_app_name(app_name: str) -> None | ServiceEntry:
    # Parse the app_name to extract project name and optional version
    if ":" in app_name:
        name, version = app_name.split(":", 1)
    else:
        name, version = app_name, None

    target = None

    async with AsyncSessionLocal() as session:
        if version is None:
            # If no version specified, get the latest version, first looking for :latest, then sorted lexicographically
            q = (
                select(ProjectConfig)
                .where(ProjectConfig.name == name)
                .order_by(ProjectConfig.version.desc())
            )
            results = (await session.execute(q)).scalars().all()
            if results:
                latest = next((p for p in results if p.version == "latest"), None)
                target = latest if latest is not None else results[0]
        else:
            q = select(ProjectConfig).where(
                ProjectConfig.name == name, ProjectConfig.version == version
            )
            result = (await session.execute(q)).scalars().first()
            target = result

        if target is None:
            return None

        # Now, find a service entry for this project config

        q = select(ServiceEntry).where(ServiceEntry.project_config_id == target.id)
        service_entry = (await session.execute(q)).scalars().first()
        if service_entry is None:
            return None

        return service_entry


def construct_target_url(service_entry: ServiceEntry, path: str, query: str) -> str:
    netloc = service_entry.hostname + ":" + str(service_entry.port)
    components = Components(
        scheme="http",
        netloc=netloc,
        url="/" + path,
        query=query,
        fragment="",
    )
    return urlunsplit(components)


def prepare_headers_for_proxy(original_headers_wz: Headers) -> Dict[str, str]:
    headers: Dict[str, str] = {}
    original_headers = dict(original_headers_wz)
    for key, value in original_headers.items():
        if key.lower() not in HOP_BY_HOP_HEADERS:
            headers[key] = value
    return headers


@proxy_blueprint.route(
    "/<string:app>",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    defaults={"path": ""},
)
@proxy_blueprint.route(
    "/<string:app>/",
    defaults={"path": ""},
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
@proxy_blueprint.route(
    "/<string:app>/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"]
)
async def proxy_request(app: str, path: str):
    # Let's find and proxy to an appropriate service entry based on the path
    # The <app> will look like either /{project.name}/... or /{project.name}:{project.version}/...

    service_entry = await get_target_from_app_name(app)
    if service_entry is None:
        return "Application not found", 404

    target_url = construct_target_url(
        service_entry, path, request.query_string.decode()
    )
    headers = prepare_headers_for_proxy(request.headers)

    upstream_ip, remote_addr = (
        request.headers.get("X-Forwarded-For"),
        request.remote_addr,
    )
    upstream_proto = request.headers.get("X-Forwarded-Proto")
    headers["X-Forwarded-For"] = upstream_ip or remote_addr or ""
    headers["X-Forwarded-Proto"] = upstream_proto or request.scheme

    debug("/%s/%s -> %s", app, path, target_url)
    debug("Headers: %s", headers)

    async def _stream_request_body():
        async for chunk in request.body:
            yield chunk

    downstream_req = _client.build_request(
        method=request.method,
        url=target_url,
        headers=headers,
        content=_stream_request_body(),
    )

    downstream_resp = await _client.send(downstream_req, stream=True)

    downstream_headers = {
        key: value
        for key, value in downstream_resp.headers.items()
        if key.lower() not in HOP_BY_HOP_HEADERS
    }

    async def _stream_response_body() -> AsyncGenerator[bytes, None]:
        async for chunk in downstream_resp.aiter_bytes():
            yield chunk
        await downstream_resp.aclose()

    return Response(
        _stream_response_body(),
        status=downstream_resp.status_code,
        headers=downstream_headers,
    )


@proxy_blueprint.after_app_serving
async def shutdown_proxy():
    await _client.aclose()

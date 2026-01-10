from sqlalchemy import select
from fats.utils import AsyncSessionLocal
from fats.models.secret import Secret


async def upsert_secret(secret_name: str, secret_value: str):
    async with AsyncSessionLocal() as session:
        secret = await session.execute(select(Secret).where(Secret.name == secret_name))
        secret = secret.scalars().first()
        if secret:
            secret.value = secret_value
        else:
            secret = Secret(name=secret_name, value=secret_value)
            session.add(secret)
        await session.commit()


async def get_secret(secret_name: str) -> str | None:
    async with AsyncSessionLocal() as session:
        secret = await session.execute(select(Secret).where(Secret.name == secret_name))
        secret = secret.scalars().first()
        if secret:
            return secret.value
        return None

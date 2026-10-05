import asyncio
from datetime import UTC, datetime
from sqlalchemy import select
from app.db.models import GenerationOutput
from app.db.session import AsyncSessionFactory, close_database_engine
from app.storage import LocalArtifactStorage

async def cleanup():
    count=0
    async with AsyncSessionFactory() as session:
        outputs=(await session.execute(select(GenerationOutput).where(GenerationOutput.deleted_at.is_(None),GenerationOutput.expires_at<=datetime.now(UTC)))).scalars().all()
        storage=LocalArtifactStorage()
        for output in outputs:storage.delete(output.object_path);output.deleted_at=datetime.now(UTC);count+=1
        await session.commit()
    await close_database_engine();print(f"Cleaned {count} expired artifacts.")
if __name__=="__main__":asyncio.run(cleanup())

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.session import database_engine


@dataclass(frozen=True)
class DatabaseHealthResult:
    status: str
    connected: bool
    message: str

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "connected": self.connected,
            "message": self.message,
        }


async def check_database_health(
    engine: AsyncEngine = database_engine,
) -> DatabaseHealthResult:
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT 1")
            )

            scalar_value = result.scalar_one()

            if scalar_value != 1:
                return DatabaseHealthResult(
                    status="unhealthy",
                    connected=False,
                    message=(
                        "Database health query returned "
                        "an unexpected result."
                    ),
                )

        return DatabaseHealthResult(
            status="healthy",
            connected=True,
            message="Database connection is available.",
        )

    except SQLAlchemyError:
        return DatabaseHealthResult(
            status="unhealthy",
            connected=False,
            message="Database connection is unavailable.",
        )

    except OSError:
        return DatabaseHealthResult(
            status="unhealthy",
            connected=False,
            message="Database connection is unavailable.",
        )
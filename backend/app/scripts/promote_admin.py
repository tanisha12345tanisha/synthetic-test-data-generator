import argparse
import asyncio

from app.db.models import UserRole
from app.db.session import AsyncSessionFactory, close_database_engine
from app.repositories.user import UserRepository


async def promote(email: str) -> None:
    async with AsyncSessionFactory() as session:
        user = await UserRepository(session).get_by_email(email)
        if user is None:
            raise SystemExit("User account not found.")
        user.role = UserRole.ADMIN
        await session.commit()
        print(f"Promoted {user.email} to admin.")
    await close_database_engine()


def main() -> None:
    parser = argparse.ArgumentParser(description="Promote an existing user to admin.")
    parser.add_argument("email")
    args = parser.parse_args()
    asyncio.run(promote(args.email))


if __name__ == "__main__":
    main()

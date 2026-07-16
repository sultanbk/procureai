import asyncio
import os
import shutil
import structlog
from backend.core.db import engine, Base
# Import all models to ensure they are registered on Base
from backend.models.audit import *

logger = structlog.get_logger()

async def clear_database():
    logger.info("Dropping all database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database reset successfully.")
    except Exception as e:
        logger.error("Failed to reset database", error=str(e))

def clear_directory_contents(dir_path: str):
    if not os.path.exists(dir_path):
        return
    logger.info(f"Clearing contents of directory: {dir_path}")
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        try:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
        except Exception as e:
            logger.error(f"Failed to delete {item_path}", error=str(e))

def recreate_subdirs(parent_dir: str, subdirs: list[str]):
    for s in subdirs:
        os.makedirs(os.path.join(parent_dir, s), exist_ok=True)

async def main():
    await clear_database()
    clear_directory_contents("data/uploads")
    clear_directory_contents("watched_invoices")
    recreate_subdirs("watched_invoices", ["processed", "unmatched"])
    logger.info("All library and watched directories cleared.")

if __name__ == "__main__":
    asyncio.run(main())

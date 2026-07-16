import asyncio
import structlog
from backend.core.db import engine, Base
# Import model to ensure it is registered on Base.metadata
from backend.models.audit import Audit, SupplierScore

logger = structlog.get_logger()

async def init_db():
    logger.info("Initializing database tables...")
    try:
        async with engine.begin() as conn:
            # Create all tables registered on the Declarative Base
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully in procureai.db.")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))

if __name__ == "__main__":
    asyncio.run(init_db())

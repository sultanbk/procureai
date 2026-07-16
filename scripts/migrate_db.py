import asyncio
import structlog
from sqlalchemy import text
from backend.core.db import engine

logger = structlog.get_logger()

async def migrate():
    logger.info("Starting database migration...")
    async with engine.begin() as conn:
        # Check contracts columns
        res = await conn.execute(text("PRAGMA table_info(contracts)"))
        columns = [row[1] for row in res.fetchall()]
        
        if "file_hash" not in columns:
            logger.info("Adding file_hash column to contracts table...")
            await conn.execute(text("ALTER TABLE contracts ADD COLUMN file_hash TEXT"))
            await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_contracts_file_hash ON contracts(file_hash)"))
            
        if "version" not in columns:
            logger.info("Adding version column to contracts table...")
            await conn.execute(text("ALTER TABLE contracts ADD COLUMN version INTEGER DEFAULT 1"))
            
        if "valid_from" not in columns:
            logger.info("Adding valid_from column to contracts table...")
            await conn.execute(text("ALTER TABLE contracts ADD COLUMN valid_from DATETIME"))
            
        if "valid_until" not in columns:
            logger.info("Adding valid_until column to contracts table...")
            await conn.execute(text("ALTER TABLE contracts ADD COLUMN valid_until DATETIME"))
            
        if "rulebook" not in columns:
            logger.info("Adding rulebook column to contracts table...")
            await conn.execute(text("ALTER TABLE contracts ADD COLUMN rulebook TEXT"))

        # Check contract_chunks columns
        res = await conn.execute(text("PRAGMA table_info(contract_chunks)"))
        cc_columns = [row[1] for row in res.fetchall()]
        
        if "contract_id" not in cc_columns:
            logger.info("Adding contract_id column to contract_chunks table...")
            await conn.execute(text("ALTER TABLE contract_chunks ADD COLUMN contract_id TEXT"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_contract_chunks_contract_id ON contract_chunks(contract_id)"))
            
    logger.info("Database migration completed.")

if __name__ == "__main__":
    asyncio.run(migrate())

import asyncio
import asyncpg

async def migrate():
    conn = await asyncpg.connect(
        user="postgres",
        password="postgres123",
        host="localhost",
        database="warsim"
    )
    
    # 1. Campaign Events Log
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            campaign_id UUID REFERENCES campaigns(id),
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            name TEXT NOT NULL,
            event_type TEXT,
            effect_data TEXT -- JSON string of modifiers applied
        );
    """)
    
    # 2. Add AI Strategy Logging
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS ai_strategy_logs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            campaign_id UUID REFERENCES campaigns(id),
            node_id UUID REFERENCES campaign_nodes(id),
            prediction_data JSONB,
            suggestion_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Add Snapshot Support to Campaigns
    await conn.execute("""
        ALTER TABLE campaigns ADD COLUMN IF NOT EXISTS snapshot JSONB;
    """)

    print("Phase 6 Migration complete.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

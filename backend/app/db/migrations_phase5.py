import asyncio
import asyncpg
import logging

async def migrate():
    conn = await asyncpg.connect(
        user="postgres",
        password="postgres123",
        host="localhost",
        database="warsim"
    )
    
    # Enable PostGIS if not already
    await conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    
    # 1. Campaigns Table
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT NOT NULL,
            era TEXT,
            start_date TIMESTAMP,
            current_sim_date TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
    """)
    
    # 2. Campaign Nodes (Strategic Cities/Forts/Battle Locations)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS campaign_nodes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            campaign_id UUID REFERENCES campaigns(id),
            name TEXT NOT NULL,
            pos GEOGRAPHY(POINT),
            node_type TEXT, -- City, Fort, Battlefield
            defensive_value FLOAT DEFAULT 1.0,
            control_faction TEXT
        );
    """)
    
    # 3. Strategic Units (Divisions/Corps moving on the map)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS strategic_units (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            campaign_id UUID REFERENCES campaigns(id),
            faction TEXT NOT NULL,
            name TEXT NOT NULL,
            commander TEXT,
            strength FLOAT,
            morale FLOAT DEFAULT 100.0,
            fatigue FLOAT DEFAULT 0.0,
            supply FLOAT DEFAULT 100.0,
            current_pos GEOGRAPHY(POINT),
            target_node_id UUID REFERENCES campaign_nodes(id),
            state TEXT DEFAULT 'Idle' -- Idle, Marching, Engaged, Routed
        );
    """)
    
    # 4. Link Battle to Campaign Node
    await conn.execute("""
        ALTER TABLE battles ADD COLUMN IF NOT EXISTS campaign_id UUID REFERENCES campaigns(id);
        ALTER TABLE battles ADD COLUMN IF NOT EXISTS node_id UUID REFERENCES campaign_nodes(id);
    """)
    
    print("Migration completed successfully.")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

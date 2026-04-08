import asyncio
import asyncpg
import uuid
from datetime import datetime

async def seed_campaign():
    conn = await asyncpg.connect(
        user="postgres",
        password="postgres123",
        host="localhost",
        database="warsim"
    )
    
    # 1. Create Campaign
    campaign_id = await conn.fetchval("""
        INSERT INTO campaigns (name, era, start_date, current_sim_date)
        VALUES ($1, $2, $3, $4)
        RETURNING id
    """, "Maryland Campaign 1862", "American Civil War", datetime(1862, 9, 3), datetime(1862, 9, 3))
    
    # 2. Add Nodes
    nodes = [
        ("Frederick", "City", [-77.41, 39.41]),
        ("Antietam", "Battlefield", [-77.74, 39.47]),
        ("Washington D.C.", "Fort", [-77.03, 38.90])
    ]
    
    node_ids = []
    for name, n_type, pos in nodes:
        nid = await conn.fetchval("""
            INSERT INTO campaign_nodes (campaign_id, name, node_type, pos, control_faction)
            VALUES ($1, $2, $3, ST_SetSRID(ST_Point($4, $5), 4326), $6)
            RETURNING id
        """, campaign_id, name, n_type, pos[0], pos[1], "Union" if "Washington" in name else "Confederate")
        node_ids.append(nid)
    
    # 3. Add Strategic Units
    # Army of Northern Virginia
    await conn.execute("""
        INSERT INTO strategic_units (campaign_id, faction, name, commander, strength, current_pos, target_node_id, state)
        VALUES ($1, $2, $3, $4, $5, ST_SetSRID(ST_Point($6, $7), 4326), $8, $9)
    """, campaign_id, "Confederate", "Army of Northern Virginia", "Gen. R.E. Lee", 55000, -77.41, 39.41, node_ids[1], "Marching")
    
    # Army of the Potomac
    await conn.execute("""
        INSERT INTO strategic_units (campaign_id, faction, name, commander, strength, current_pos, target_node_id, state)
        VALUES ($1, $2, $3, $4, $5, ST_SetSRID(ST_Point($6, $7), 4326), $8, $9)
    """, campaign_id, "Union", "Army of the Potomac", "Gen. G. McClellan", 87000, -77.03, 38.90, node_ids[1], "Marching")

    print(f"Seed complete. Campaign ID: {campaign_id}")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_campaign())

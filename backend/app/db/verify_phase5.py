import asyncio
import asyncpg
import requests

async def verify():
    # 1. Test Advance Time via API
    campaign_id = "c27a0a66-530d-42e1-b73d-d803173ee371"
    print(f"Advancing campaign {campaign_id}...")
    
    for i in range(3):
        res = requests.post(f"http://localhost:8000/api/campaigns/{campaign_id}/advance")
        print(f"Advance {i+1}: {res.status_code}")

    # 2. Check DB for Attrition and Movement
    conn = await asyncpg.connect(
        user="postgres",
        password="postgres123",
        host="localhost",
        database="warsim"
    )
    
    rows = await conn.fetch("""
        SELECT name, strength, ST_AsText(current_pos::geometry) as pos 
        FROM strategic_units 
        WHERE campaign_id = $1
    """, campaign_id)
    
    for r in rows:
        print(f"Unit: {r['name']} | Strength: {r['strength']} | Pos: {r['pos']}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(verify())

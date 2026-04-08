import asyncio
import asyncpg
import json

async def test_db():
    db_pool = await asyncpg.create_pool(
        user="postgres", password="postgres123", host="localhost", database="warsim"
    )
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, faction, commander, initial_strength, 
                   ST_X(spawn_pos) as lng, ST_Y(spawn_pos) as lat
            FROM armies WHERE battle_id=$1::uuid
        """, "a1b2c3d4-1111-4444-aaaa-000000000001")
        print("Rows loaded:", len(rows))
        for r in rows:
            print(r)
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(test_db())

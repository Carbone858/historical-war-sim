import asyncio
import asyncpg
import json
import os
from pathlib import Path

async def import_battle(pack_path: str, db_url: str):
    conn = await asyncpg.connect(db_url)
    try:
        manifest = json.load(open(f"{pack_path}/manifest.json"))
        
        # 1. Insert battle metadata
        await conn.execute("""
            INSERT INTO battles (id, name, year, start_date, end_date, center, is_verified, war_name, terrain_type, source_id)
            VALUES ($1, $2, $3, $4, $5, ST_SetSRID(ST_MakePoint($6, $7), 4326), $8, $9, $10, $11)
            ON CONFLICT (id) DO UPDATE SET name=$2, year=$3, war_name=$9, terrain_type=$10
        """, 
            manifest['id'], manifest['name'], manifest['year'],
            f"{manifest['year']}-01-01", f"{manifest['year']}-12-31",
            (manifest['map_bounds']['east'] + manifest['map_bounds']['west'])/2,
            (manifest['map_bounds']['north'] + manifest['map_bounds']['south'])/2,
            manifest['verified'], manifest.get('war_name', manifest.get('era', '')), 
            manifest['terrain_type'], 'src-nps-gettysburg'
        )
        
        print(f"✅ Imported {manifest['name']} successfully.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python import_battle.py <battle_pack_path>")
        sys.exit(1)
    
    pack = sys.argv[1]
    db = "postgresql://postgres:postgres123@localhost/warsim"
    asyncio.run(import_battle(pack, db))
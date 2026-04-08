import asyncio
import logging
from app.simulation.terrain import TerrainData

logging.basicConfig(level=logging.INFO)

async def test_terrain():
    bounds = {
        "north": 39.84, "south": 39.80,
        "east": -77.20, "west": -77.25
    }
    terrain = TerrainData("a1b2c3d4-1111-4444-aaaa-000000000001", bounds)
    await terrain.load()
    
    print("Elevation array shape:", terrain.elevation_data.shape if terrain.elevation_data is not None else None)
    
    # Test getting elevation at specific float
    el1 = terrain.get_elevation_at(-77.22, 39.82)
    el2 = terrain.get_elevation_at(-77.21, 39.82)
    print("Elevation roughly mid-Gettysburg:", el1)
    print("Elevation slightly east:", el2)

if __name__ == "__main__":
    asyncio.run(test_terrain())

import asyncio
import logging
import numpy as np
from app.simulation.terrain import TerrainData

logging.basicConfig(level=logging.INFO)

async def test_los():
    bounds = {
        "north": 39.84, "south": 39.80,
        "east": -77.20, "west": -77.25
    }
    battle_id = "a1b2c3d4-1111-4444-aaaa-000000000001"
    terrain = TerrainData(battle_id, bounds)
    await terrain.load()
    
    if terrain.elevation_data is None:
        print("Failed to load terrain data.")
        return

    # Find two points with a hill in between
    # Gettysburg terrain at 39.82 roughly has Culp's Hill and Cemetery Hill
    # Point A: Low ground
    # Point B: Other side of a potential ridge
    pos1 = [-77.22, 39.82] 
    pos2 = [-77.23, 39.82] 
    
    blocked = terrain.is_los_blocked(pos1, pos2)
    print(f"LoS between {pos1} and {pos2} blocked: {blocked}")
    
    # Try a point on a peak vs a point behind it
    # Find a peak in the data
    flat_idx = np.argmax(terrain.elevation_data)
    r, c = np.unravel_index(flat_idx, terrain.elevation_data.shape)
    
    # Peak coords
    x_peak, y_peak = terrain.transform * (r, c)
    peak_lng, peak_lat = terrain.proj_transformer.transform(x_peak, y_peak, direction=pyproj.enums.TransformDirection.INVERSE)
    
    print(f"Peak found at {peak_lng}, {peak_lat} with elevation {terrain.elevation_data[r, c]}")

if __name__ == "__main__":
    import pyproj
    asyncio.run(test_los())

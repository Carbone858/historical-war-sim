import time
import asyncio
from app.simulation.engine import BattleEngine

class MockTerrain:
    def __init__(self, *args, **kwargs): pass
    async def load(self): pass
    def get_movement_penalty(self, *args): return 1.0
    def get_elevation_at(self, *args): return 0.0
    def is_los_blocked(self, *args): return False

async def run_stress_test():
    print("--- 10,000 Unit Stress Test (Melee Scenario) ---")
    
    # Initialize Engine
    bounds = {"north": 39.84, "south": 39.80, "east": -77.20, "west": -77.25}
    engine = BattleEngine("stress_test", bounds)
    engine.terrain = MockTerrain() # Bypass rasterio
    
    # Create 10,000 Regiments in close proximity to maximize spatial hashing/combat load
    print("Initializing 10,000 units...")
    for i in range(2500):
        faction = "Union" if i < 1250 else "Confederate"
        engine.add_army(
            id=f"st_{i}",
            faction=faction,
            commander=f"Cmdr_{i}",
            initial_strength=400,
            pos=[-77.225, 39.825] # Everyone in the same melee zone
        )
    
    print(f"Total Regiments: {len(engine.flat_regiments)}")
    
    # Measure 10 Ticks
    total_time = 0
    num_ticks = 10
    
    print(f"Running {num_ticks} simulation ticks...")
    for t in range(num_ticks):
        start = time.perf_counter()
        engine.step()
        end = time.perf_counter()
        
        tick_duration = end - start
        total_time += tick_duration
        print(f"Tick {t+1}: {tick_duration*1000:.2f}ms")
    
    avg_tick = (total_time / num_ticks) * 1000
    print(f"\nAverage Tick Time: {avg_tick:.2f}ms")
    
    if avg_tick < 1000:
        print("✅ SUCCESS: Tick time is well below 1.0s budget.")
    else:
        print("❌ FAILURE: Performance bottleneck detected.")

if __name__ == "__main__":
    asyncio.run(run_stress_test())

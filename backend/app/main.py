from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import asyncpg
import json

app = FastAPI(title="WarSim Platform - Scalable Edition")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

db_pool = None

@app.on_event("startup")
async def startup():
    global db_pool
    db_pool = await asyncpg.create_pool(
        user="postgres",
        password="postgres123",
        host="localhost",
        database="warsim"
    )

class ConfigDrivenSim:
    def __init__(self, battle_id: str):
        self.battle_id = battle_id
        self.config = {}
        self.units = {}
        self.tick = 0
        self.running = False

    async def load(self):
        async with db_pool.acquire() as conn:
            # Load battle config
            row = await conn.fetchrow("SELECT * FROM battles WHERE id=$1", self.battle_id)
            if row:
                self.config = {
                    "tick_duration_seconds": 3600,
                    "supply_consumption_rate": 0.005,
                    "morale_decay_rate": 0.02
                }
            
            # Load units
            rows = await conn.fetch("""
                SELECT id, faction, commander, initial_strength, 
                       ST_X(spawn_pos) as lng, ST_Y(spawn_pos) as lat
                FROM armies WHERE battle_id=$1
            """, self.battle_id)
            
            for r in rows:
                self.units[r['id']] = {
                    "id": r['id'],
                    "faction": r['faction'],
                    "commander": r['commander'],
                    "pos": [r['lng'], r['lat']],
                    "strength": r['initial_strength'],
                    "morale": 100,
                    "supply": 100
                }

    async def run(self, ws):
        await self.load()
        self.running = True
        
        while self.running and self.tick < 72:
            self._step()
            await ws.send_json({
                "battle_id": self.battle_id,
                "tick": self.tick,
                "is_hypothetical": False,
                "armies": self.units
            })
            await asyncio.sleep(1)
            self.tick += 1

    def _step(self):
        for uid, u in self.units.items():
            # Simple movement toward center
            if "Union" in u['faction']:
                u['pos'][0] += 0.0005
            else:
                u['pos'][0] -= 0.0005
            
            u['supply'] = max(0, u['supply'] - 0.2)
            u['morale'] = max(0, u['morale'] - 0.1 if u['supply'] < 50 else 0)

@app.websocket("/ws/sim/{battle_id}")
async def ws_sim(websocket: WebSocket, battle_id: str):
    await websocket.accept()
    sim = ConfigDrivenSim(battle_id)
    asyncio.create_task(sim.run(websocket))
    
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("action") == "pause":
                sim.running = False
            elif msg.get("action") == "resume":
                sim.running = True
                asyncio.create_task(sim.run(websocket))
    except WebSocketDisconnect:
        pass

@app.get("/api/battles")
async def list_battles():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, year, is_verified FROM battles ORDER BY year DESC")
        return [dict(r) for r in rows]

@app.get("/api/battles/{battle_id}/manifest")
async def get_battle_manifest(battle_id: str):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM battles WHERE id=$1", battle_id)
        if row:
            return {
                "id": row['id'],
                "name": row['name'],
                "year": row['year'],
                "is_verified": row['is_verified'],
                "map_bounds": {
                    "north": 39.84, "south": 39.80,
                    "east": -77.20, "west": -77.25
                },
                "era": "american_civil_war",
                "factions": ["Union", "Confederate"],
                "duration_hours": 72
            }
        return {"error": "Battle not found"}

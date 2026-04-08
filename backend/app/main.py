from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import asyncpg
import json
import uuid
import logging
from datetime import datetime
from app.simulation.engine import BattleEngine
from app.simulation.monte_carlo import MonteCarloAnalyzer
from app.campaign.manager import CampaignManager
from app.data.historical_fetcher import HistoricalFetcher
from app.ai.strategic_advisor import StrategicAdvisor
from app.services.event_dispatcher import EventDispatcher

logging.basicConfig(filename="backend_debug.log", level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

app = FastAPI(title="WarSim Platform - Scalable Edition")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

db_pool = None
campaign_manager = None
fetcher = None
advisor = None
event_dispatcher = None

@app.on_event("startup")
async def startup():
    global db_pool, campaign_manager, fetcher, advisor, event_dispatcher
    db_pool = await asyncpg.create_pool(
        user="postgres",
        password="postgres123",
        host="localhost",
        database="warsim"
    )
    campaign_manager = CampaignManager(db_pool)
    fetcher = HistoricalFetcher(db_pool)
    advisor = StrategicAdvisor()
    event_dispatcher = EventDispatcher(db_pool)
    
    # Start background event loop
    asyncio.create_task(event_dispatcher.run_loop())
    
    print("Connected to PostgreSQL and initialized Strategic AI Engine.")

class AsyncSimRunner:
    def __init__(self, battle_id: str):
        self.battle_id = battle_id
        # We will parse bounds and instantiate the engine in the async load() method.
        self.engine = None
        self.running = False
        self.tick = 0

    async def load(self):
        async with db_pool.acquire() as conn:
            # 1. Load Bounds
            row = await conn.fetchrow("SELECT * FROM battles WHERE id=$1", uuid.UUID(self.battle_id))
            bounds = {
                "north": 39.84, "south": 39.80, # Hardcoded fallback
                "east": -77.20, "west": -77.25
            }
            if row and 'bounds' in row and row['bounds']:
                # Hypothetical column support
                bounds = json.loads(row['bounds'])
            
            self.engine = BattleEngine(self.battle_id, bounds)
            await self.engine.load_historical_data()

            # 2. Load units from DB
            rows = await conn.fetch("""
                SELECT id, faction, commander, initial_strength, 
                       ST_X(spawn_pos::geometry) as lng, ST_Y(spawn_pos::geometry) as lat
                FROM armies WHERE battle_id=$1
            """, uuid.UUID(self.battle_id))
            
            for r in rows:
                self.engine.add_army(
                    id=str(r['id']),
                    faction=r['faction'],
                    commander=r['commander'],
                    initial_strength=r['initial_strength'],
                    pos=[r['lng'], r['lat']]
                )
            logging.info(f"Loaded {len(rows)} armies into engine.")

    async def run(self, ws):
        try:
            await self.load()
            self.running = True
            
            while self.running and self.tick < 72:
                self.tick = self.engine.step()
                
                # Check if we are serving a minimized/UE5 client
                state = self.engine.get_minimized_state() if getattr(self, 'minimized', False) else self.engine.get_state()
                
                await ws.send_json({
                    "battle_id": self.battle_id,
                    "tick": self.tick,
                    "is_hypothetical": False,
                    "armies": state,
                    "validation": self.engine.get_validation_report()
                })
                await asyncio.sleep(1)
        except Exception as e:
            logging.error(f"Simulation run error: {e}", exc_info=True)

@app.websocket("/ws/sim/{battle_id}")
async def ws_sim(websocket: WebSocket, battle_id: str):
    await websocket.accept()
    logging.info(f"Accepted WS for {battle_id}")
    try:
        battle_uuid = uuid.UUID(battle_id)
    except ValueError:
        logging.error(f"Invalid UUID: {battle_id}")
        await websocket.close(code=1003, reason="Invalid battle ID")
        return

    sim = AsyncSimRunner(battle_id)
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

@app.websocket("/ws/ue5/{battle_id}")
async def ws_ue5(websocket: WebSocket, battle_id: str):
    await websocket.accept()
    logging.info(f"Accepted UE5 High-Bandwidth WS for {battle_id}")
    
    sim = AsyncSimRunner(battle_id)
    sim.minimized = True # Use optimized array format
    asyncio.create_task(sim.run(websocket))
    
    try:
        while True:
            await websocket.receive_text() # Hold connection
    except WebSocketDisconnect:
        pass

@app.get("/api/battles")
async def list_battles():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, year, is_verified FROM battles ORDER BY year DESC")
        return [dict(r) for r in rows]

@app.get("/api/battles/{battle_id}/manifest")
async def get_battle_manifest(battle_id: str):
    try:
        battle_uuid = uuid.UUID(battle_id)
    except ValueError:
        return {"error": "Invalid battle ID format (must be UUID)"}

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM battles WHERE id=$1", battle_uuid)
        if row:
            return {
                "id": str(row['id']),
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

@app.post("/api/battles/{battle_id}/what-if")
async def run_what_if_analysis(battle_id: str, scenario: dict):
    # Fetch battle bounds from DB
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM battles WHERE id=$1", uuid.UUID(battle_id))
        if not row:
            return {"error": "Battle not found"}
            
        bounds = json.loads(row['bounds']) if ('bounds' in row and row['bounds']) else {
            "north": 39.84, "south": 39.80, "east": -77.20, "west": -77.25
        }
        
        # Load current armies from DB if not provided in scenario
        if 'armies' not in scenario:
            army_rows = await conn.fetch("""
                SELECT id, faction, commander, initial_strength as strength, 
                       ST_X(spawn_pos::geometry) as lng, ST_Y(spawn_pos::geometry) as lat
                FROM armies WHERE battle_id=$1
            """, uuid.UUID(battle_id))
            scenario['armies'] = []
            for r in army_rows:
                scenario['armies'].append({
                    "id": str(r['id']), "faction": r['faction'], 
                    "commander": r['commander'], "strength": r['strength'], 
                    "pos": [r['lng'], r['lat']]
                })
 
    mca = MonteCarloAnalyzer(battle_id, bounds, num_runs=scenario.get('num_runs', 20))
    results = await mca.run_scenario(scenario)
    return results

# --- Phase 5: Campaign Endpoints ---

@app.get("/api/campaigns")
async def list_campaigns():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM campaigns")
        return [
            {**dict(r), "id": str(r["id"])} for r in rows
        ]

@app.get("/api/campaigns/{id}/state")
async def get_campaign_state(id: str):
    async with db_pool.acquire() as conn:
        campaign_uuid = uuid.UUID(id)
        campaign = await conn.fetchrow("SELECT * FROM campaigns WHERE id=$1", campaign_uuid)
        nodes = await conn.fetch("SELECT *, ST_AsGeoJSON(pos)::json as geo FROM campaign_nodes WHERE campaign_id=$1", campaign_uuid)
        units = await conn.fetch("SELECT *, ST_AsGeoJSON(current_pos)::json as geo FROM strategic_units WHERE campaign_id=$1", campaign_uuid)
        
        return {
            "campaign": {**dict(campaign), "id": str(campaign["id"])},
            "nodes": [{**dict(n), "id": str(n["id"]), "campaign_id": str(n["campaign_id"])} for n in nodes],
            "units": [{**dict(u), "id": str(u["id"]), "campaign_id": str(u["campaign_id"])} for u in units]
        }

@app.post("/api/campaigns/{id}/advance")
async def advance_campaign_time(id: str):
    await campaign_manager.advance_campaign(uuid.UUID(id))
    return {"status": "success", "tick": "6h advanced"}

@app.post("/api/campaigns/{id}/node/{node_id}/initialize-tactical")
async def init_tactical_from_node(id: str, node_id: str, payload: dict):
    # Initialize high-fidelity battle from Wikidata OOB
    wikidata_id = payload.get("wikidata_id") # e.g. Q133162
    units = await campaign_manager.initialize_battle_from_node(id, node_id, wikidata_id)
    return {"status": "initialized", "unit_count": len(units)}

# --- Phase 6: AI & Order Endpoints ---

@app.get("/api/campaigns/{id}/ai-insights")
async def get_ai_insights(id: str):
    async with db_pool.acquire() as conn:
        campaign_uuid = uuid.UUID(id)
        # Fetch status of active fronts
        units = await conn.fetch("SELECT * FROM strategic_units WHERE campaign_id=$1", campaign_uuid)
        
        # Simple heuristic: look for nodes with opposing factions nearby
        # For now, return a general prediction
        prediction = advisor.predict_battle_outcome(
            [u for u in units if u['faction'] == 'Union'],
            [u for u in units if u['faction'] == 'Confederate']
        )
        return {
            "prediction": prediction,
            "suggestions": advisor.suggest_reinforcements({"node_id": "global", "enemy": [], "friendly": []}, [])
        }

@app.get("/api/campaigns/{id}/events")
async def get_campaign_events_log(id: str):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM campaign_events WHERE campaign_id=$1 ORDER BY timestamp DESC LIMIT 20", uuid.UUID(id))
        return [dict(r) for r in rows]

@app.post("/api/campaigns/{id}/snapshot")
async def save_campaign_snapshot(id: str):
    async with db_pool.acquire() as conn:
        campaign_uuid = uuid.UUID(id)
        # Capture all units and status into a JSON blob
        units = await conn.fetch("SELECT *, ST_AsText(current_pos::geometry) as pos_text FROM strategic_units WHERE campaign_id=$1", campaign_uuid)
        snapshot_data = {
            "timestamp": datetime.now().isoformat(),
            "units": [dict(u) for u in units]
        }
        await conn.execute("UPDATE campaigns SET snapshot = $1 WHERE id = $2", json.dumps(snapshot_data), campaign_uuid)
        return {"status": "snapshot_saved"}

@app.post("/api/campaigns/{id}/restore")
async def restore_campaign_snapshot(id: str):
    async with db_pool.acquire() as conn:
        campaign_uuid = uuid.UUID(id)
        campaign = await conn.fetchrow("SELECT snapshot FROM campaigns WHERE id=$1", campaign_uuid)
        if not campaign or not campaign['snapshot']:
            return {"error": "No snapshot found"}
        
        data = json.loads(campaign['snapshot'])
        for u in data['units']:
            await conn.execute("""
                UPDATE strategic_units 
                SET strength = $1, morale = $2, fatigue = $3, current_pos = ST_GeomFromText($4, 4326)
                WHERE id = $5
            """, u['strength'], u['morale'], u['fatigue'], u['pos_text'], uuid.UUID(u['id']))
            
        return {"status": "restored"}

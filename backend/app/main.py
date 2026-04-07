from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
import asyncio

app = FastAPI(title="WarSim Platform")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class MockSim:
    def __init__(self, battle_id):
        self.battle_id = battle_id
        self.running = False
        self.is_hypothetical = False
        self.tick = 0
    async def run(self, ws):
        self.running = True
        while self.running:
            snapshot = {
                "battle_id": self.battle_id, "tick": self.tick,
                "is_hypothetical": self.is_hypothetical,
                "armies": {
                    "u-101": {"pos": [-77.23 + self.tick*0.001, 39.83], "strength": 90000, "morale": 95, "supply": 98, "fatigue": 2, "faction": "Union"},
                    "c-102": {"pos": [-77.20 - self.tick*0.001, 39.81], "strength": 68000, "morale": 92, "supply": 95, "fatigue": 3, "faction": "Confederate"}
                }
            }
            await ws.send_json(snapshot)
            self.tick += 1
            await asyncio.sleep(1)

@app.websocket("/ws/sim/{battle_id}")
async def ws_sim(websocket: WebSocket, battle_id: str):
    await websocket.accept()
    sim = MockSim(battle_id)
    asyncio.create_task(sim.run(websocket))
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("action") == "pause": sim.running = False
            elif msg.get("action") == "resume":
                sim.running = True
                asyncio.create_task(sim.run(websocket))
            elif msg.get("action") == "whatif_toggle": sim.is_hypothetical = msg.get("enabled", False)
    except WebSocketDisconnect: pass

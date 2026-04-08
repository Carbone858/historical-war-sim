import asyncio
import websockets
import json

async def test_ws():
    uri = "ws://localhost:8000/ws/sim/a1b2c3d4-1111-4444-aaaa-000000000001"
    async with websockets.connect(uri) as websocket:
        # Start the sim
        await websocket.send(json.dumps({"action": "resume"}))
        
        for _ in range(3):
            msg = await websocket.recv()
            data = json.loads(msg)
            print(f"Tick: {data['tick']}, Engine State: {data['armies']}")

if __name__ == "__main__":
    asyncio.run(test_ws())

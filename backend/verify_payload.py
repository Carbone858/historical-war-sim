import asyncio
import websockets
import json

async def verify_realism_payload():
    url = "ws://localhost:8000/ws/sim/a1b2c3d4-1111-4444-aaaa-000000000001"
    try:
        async with websockets.connect(url) as websocket:
            print("Connected to WebSocket.")
            # Resume simulation if needed
            await websocket.send(json.dumps({"action": "resume"}))
            
            # Wait for a couple of ticks
            for i in range(3):
                msg = await websocket.recv()
                data = json.loads(msg)
                
                print(f"\n--- Tick {data.get('tick')} ---")
                
                # Verify Armies (Hierarchy check)
                armies = data.get("armies", {})
                print(f"Number of regiments: {len(armies)}")
                if armies:
                    first_reg = list(armies.values())[0]
                    print(f"First regiment check: {first_reg.get('name')} | State: {first_reg.get('state')} | Pos: {first_reg.get('pos')}")
                
                # Verify Validation Report
                validation = data.get("validation")
                if validation:
                    print(f"Validation Report present: Union {validation['union']['delta_percent']}% | Confed {validation['confederate']['delta_percent']}%")
                else:
                    print("ERROR: Validation report missing from payload!")
                
                await asyncio.sleep(0.5)
                
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_realism_payload())

import asyncio
import asyncpg
from app.ai.strategic_advisor import StrategicAdvisor

async def verify_strategic_ai():
    advisor = StrategicAdvisor()
    
    # Mock Battle: 50,000 Union vs 35,000 Confederate
    union = [{"unit_type": "Infantry", "strength": 50000}]
    rebel = [{"unit_type": "Infantry", "strength": 35000}]
    
    outcome = advisor.predict_battle_outcome(union, rebel)
    print(f"Lanchester Prediction (Union Attack): {outcome}")
    
    # Test Suggestions
    suggestions = advisor.suggest_reinforcements(
        {"node_id": "Antietam", "enemy": rebel, "friendly": [{"unit_type": "Infantry", "strength": 10000}]},
        [{"id": "reserve_1", "strength": 5000}]
    )
    print(f"AI Suggestions: {suggestions}")

async def verify_event_system():
    conn = await asyncpg.connect(user='postgres', password='postgres123', host='localhost', database='warsim')
    
    # Check if events are being logged
    count = await conn.fetchval("SELECT COUNT(*) FROM campaign_events")
    print(f"Logged Events Count: {count}")
    
    # Check for unit morale changes
    rows = await conn.fetch("SELECT name, morale FROM strategic_units LIMIT 5")
    for r in rows:
        print(f"Unit: {r['name']} | Morale: {r['morale']}")
        
    await conn.close()

if __name__ == "__main__":
    print("--- Phase 6 Verification ---")
    asyncio.run(verify_strategic_ai())
    asyncio.run(verify_event_system())

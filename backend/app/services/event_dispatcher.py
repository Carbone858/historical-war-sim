import asyncio
import logging
import random
import uuid
from datetime import datetime, timedelta
import asyncpg

class EventDispatcher:
    """Manages global campaign events and applies dynamic modifiers to units."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        # Historical event database (Mock for American Civil War)
        self.historical_events = [
            {"date": "1862-09-17 06:00:00", "name": "Morning Fog at Antietam", "type": "Weather", "scope": "Global", "effect": {"visibility": 0.3}},
            {"date": "1862-09-22 12:00:00", "name": "Emancipation Proclamation (Preliminary)", "type": "Political", "scope": "Union", "effect": {"morale": 15}},
        ]

    async def run_loop(self):
        """Main background loop to check for and trigger events."""
        while True:
            try:
                await self.check_and_trigger_events()
            except Exception as e:
                logging.error(f"EventDispatcher error: {e}")
            await asyncio.sleep(60) # Check every simulated minute (or mapped interval)

    async def check_and_trigger_events(self):
        """Matches current sim time against event database and rolls for stochastic events."""
        async with self.db_pool.acquire() as conn:
            campaigns = await conn.fetch("SELECT id, current_sim_date FROM campaigns WHERE is_active = TRUE")
            for camp in campaigns:
                await self._process_deterministic_events(conn, camp)
                await self._roll_stochastic_events(conn, camp)

    async def _process_deterministic_events(self, conn, camp):
        sim_time = camp['current_sim_date']
        for event in self.historical_events:
            event_time = datetime.strptime(event['date'], "%Y-%m-%d %H:%M:%S")
            # If simulated time has passed the event time, apply it
            if sim_time >= event_time:
                await self._apply_event_effect(conn, camp['id'], event)

    async def _roll_stochastic_events(self, conn, camp):
        """Rolls for minor stochastic events like disease or attrition spikes."""
        if random.random() < 0.05: # 5% chance per strategic tick
            event = {
                "name": "Dysentery Outbreak",
                "type": "Health",
                "scope": "Random",
                "effect": {"morale": -10, "strength_attrition": 0.02}
            }
            await self._apply_event_effect(conn, camp['id'], event)

    async def _apply_event_effect(self, conn, campaign_id: uuid.UUID, event: dict):
        """Applies event modifiers to strategic_units in the database."""
        logging.info(f"Triggering Event: {event['name']} for campaign {campaign_id}")
        
        # 1. Log to database
        await conn.execute("""
            INSERT INTO campaign_events (campaign_id, name, event_type, effect_data)
            VALUES ($1, $2, $3, $4)
        """, campaign_id, event['name'], event['type'], str(event['effect']))
        
        # 2. Apply stat changes to units
        if "morale" in event['effect']:
            await conn.execute("""
                UPDATE strategic_units 
                SET morale = LEAST(100.0, GREATEST(0.0, morale + $1))
                WHERE campaign_id = $2
            """, event['effect']['morale'], campaign_id)

        if "strength_attrition" in event['effect']:
            # Subtract a percentage of CURRENT strength
            await conn.execute("""
                UPDATE strategic_units 
                SET strength = strength * (1.0 - $1)
                WHERE campaign_id = $2
            """, event['effect']['strength_attrition'], campaign_id)

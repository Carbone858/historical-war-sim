import logging
import asyncio
from datetime import timedelta
from typing import List, Dict
import asyncpg
from app.data.historical_fetcher import HistoricalFetcher

class CampaignManager:
    """Manages high-level strategic state: timing, unit movement, and logistics."""
    
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.fetcher = HistoricalFetcher(db_pool)
        self.strategic_tick_hours = 6 # 1 tick = 6 hours of war time

    async def advance_campaign(self, campaign_id: str):
        """Processes one strategic tick for the campaign."""
        async with self.db_pool.acquire() as conn:
            # 1. Update Global Time
            await conn.execute("""
                UPDATE campaigns 
                SET current_sim_date = current_sim_date + interval '6 hours'
                WHERE id = $1
            """, campaign_id)
            
            # 2. Process Unit Movement & Attrition
            units = await conn.fetch("SELECT * FROM strategic_units WHERE campaign_id = $1", campaign_id)
            for unit in units:
                await self._process_unit_logic(conn, unit)
                
            logging.info(f"Campaign {campaign_id} advanced by {self.strategic_tick_hours} hours.")

    async def _process_unit_logic(self, conn, unit):
        """Handles movement interpolation and supply-based attrition."""
        # If marching, move towards target_node
        if unit['state'] == 'Marching' and unit['target_node_id']:
            # Simplified movement: update current_pos towards target_node point
            # In a real GIS app, we'd use ST_Project or similar.
            # Here we simulate with a simple 0.05 degree skip per tick.
            await conn.execute("""
                UPDATE strategic_units
                SET fatigue = LEAST(100.0, fatigue + 5.0),
                    strength = strength * 0.995, -- 0.5% attrition per march tick
                    current_pos = ST_SetSRID(ST_Point(
                        ST_X(current_pos::geometry) + (ST_X(target_node_pos::geometry) - ST_X(current_pos::geometry)) * 0.1,
                        ST_Y(current_pos::geometry) + (ST_Y(target_node_pos::geometry) - ST_Y(current_pos::geometry)) * 0.1
                    ), 4326)
                FROM (SELECT id, pos as target_node_pos FROM campaign_nodes) as nodes
                WHERE strategic_units.id = $1 AND nodes.id = strategic_units.target_node_id
            """, unit['id'])
            
        # Supply recovery if at a friendly node
        else:
            await conn.execute("""
                UPDATE strategic_units
                SET fatigue = GREATEST(0.0, fatigue - 10.0),
                    supply = LEAST(100.0, supply + 20.0)
                WHERE id = $1
            """, unit['id'])

    async def initialize_battle_from_node(self, campaign_id, node_id, wikidata_id):
        """Triggers a tactical simulation OOB fetch or state transfer for a strategic node."""
        async with self.db_pool.acquire() as conn:
            # 1. Create or ensure battle record exists
            # We use the node_id as the battle_id for consistency in this phase
            await conn.execute("""
                INSERT INTO battles (id, campaign_id, node_id, name, year, is_verified)
                SELECT $1, $2, $1, name, 1862, true 
                FROM campaign_nodes WHERE id = $1
                ON CONFLICT (id) DO NOTHING
            """, node_id, campaign_id)

            # 2. Check if there are StrategicUnits assigned to or near this node
            strategic_units = await conn.fetch("""
                SELECT * FROM strategic_units 
                WHERE campaign_id = $1 AND (target_node_id = $2 OR ST_Distance(current_pos, (SELECT pos FROM campaign_nodes WHERE id = $2)) < 5000)
            """, campaign_id, node_id)

            if strategic_units:
                logging.info(f"Seeding battle {node_id} from {len(strategic_units)} strategic units.")
                # Clear old armies for this node/battle to avoid duplicates
                await conn.execute("DELETE FROM armies WHERE battle_id = $1", node_id)
                
                for u in strategic_units:
                    # Map StrategicUnit -> Tactical Army/Regiment
                    # We spawn them slightly offset from the node center
                    await conn.execute("""
                        INSERT INTO armies (id, battle_id, faction, commander, initial_strength, name, unit_type, spawn_pos)
                        VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, 'Infantry', (SELECT pos FROM campaign_nodes WHERE id = $1))
                    """, node_id, u['faction'], u['commander'], u['strength'], u['name'])
                return strategic_units
            
            # 3. Fallback to Wikidata if no strategic units are present
            logging.info(f"No strategic units at node {node_id}. Falling back to Wikidata fetch for {wikidata_id}.")
            return await self.fetcher.get_cached_or_fetch(node_id, wikidata_id)

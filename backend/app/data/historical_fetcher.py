import requests
import logging
import uuid
from typing import List, Dict

class HistoricalFetcher:
    """Service to fetch and normalize military data from Wikidata/DBpedia."""
    
    WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"
    
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        self.user_agent = "WarSimHistoricalFetcher/1.0 (historical-war-sim project)"

    def fetch_battle_oob(self, battle_wikidata_id: str) -> List[Dict]:
        """
        Queries Wikidata for participants of a specific battle.
        battle_wikidata_id example: 'Q133162' (Gettysburg)
        """
        query = f"""
        SELECT ?unit ?unitLabel ?strength ?commanderLabel WHERE {{
          wd:{battle_wikidata_id} p:P710 ?statement.
          ?statement ps:P710 ?unit.
          OPTIONAL {{ ?statement pq:P2196 ?strength. }}
          OPTIONAL {{ ?unit wdt:P1027 ?commander. }}
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
        """
        try:
            logging.info(f"Fetching OOB for {battle_wikidata_id} from Wikidata...")
            response = requests.get(
                self.WIKIDATA_SPARQL_URL,
                params={'query': query, 'format': 'json'},
                headers={'User-Agent': self.user_agent},
                timeout=15
            )
            data = response.json()
            results = data.get('results', {}).get('bindings', [])
            return self._normalize_oob(results)
        except Exception as e:
            logging.error(f"Wikidata fetch error: {e}")
            return []

    def _normalize_oob(self, raw_results: List[Dict]) -> List[Dict]:
        """Maps Wikidata bindings to internal Regiment/Division schema with gap filling."""
        normalized = []
        for r in raw_results:
            # Procedural Gap Filling (Phase 5 rule: 400 men/regiment fallback)
            strength_raw = r.get('strength', {}).get('value')
            strength = int(strength_raw) if strength_raw else 400
            
            normalized.append({
                "external_id": r['unit']['value'].split('/')[-1],
                "name": r['unitLabel']['value'],
                "commander": r.get('commanderLabel', {}).get('value', "Unknown Commander"),
                "strength": strength,
                "unit_type": self._infer_unit_type(r['unitLabel']['value'])
            })
        return normalized

    def _infer_unit_type(self, name: str) -> str:
        """Heuristic to guess unit type from Wikipedia labels."""
        name_lower = name.lower()
        if "cavalry" in name_lower: return "Cavalry"
        if "artillery" in name_lower or "battery" in name_lower: return "Artillery"
        return "Infantry"

    async def get_cached_or_fetch(self, battle_id: str, wikidata_id: str):
        """Checks Postgres cache first, then fetches and populates db."""
        if not self.db_pool: return self.fetch_battle_oob(wikidata_id)
        
        async with self.db_pool.acquire() as conn:
            # 1. Check if we already have normalized data
            count = await conn.fetchval("SELECT COUNT(*) FROM armies WHERE battle_id=$1", battle_id)
            if count > 0:
                logging.info(f"Using cached OOB for battle {battle_id}")
                return await conn.fetch("SELECT * FROM armies WHERE battle_id=$1", battle_id)
            
            # 2. Fetch new
            units = self.fetch_battle_oob(wikidata_id)
            
            # 3. Populate Cache
            for u in units:
                faction = self._infer_faction(u['name'])
                await conn.execute("""
                    INSERT INTO armies (battle_id, faction, commander, initial_strength, name, unit_type)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, uuid.UUID(battle_id), faction, u['commander'], u['strength'], u['name'], u['unit_type'])
            
            return units

    def _infer_faction(self, name: str) -> str:
        """Heuristic to guess faction from unit name."""
        name_lower = name.lower()
        if any(w in name_lower for w in ["union", "federal", "u.s.", "united states", "pennsylvania", "new york", "massachusetts"]): return "Union"
        if any(w in name_lower for w in ["confederate", "rebel", "c.s.a.", "virginia", "georgia", "north carolina"]): return "Confederate"
        return "Unknown"

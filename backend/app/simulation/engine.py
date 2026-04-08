import simpy
import logging
from .agents import Regiment, Brigade, Division, Corps, Army
from .terrain import TerrainData
from .environment import WeatherSystem

class BattleEngine:
    def __init__(self, battle_id, bounds):
        self.battle_id = battle_id
        self.env = simpy.Environment()
        self.armies = {}
        self.terrain = TerrainData(battle_id, bounds)
        self.flat_regiments = []
        self.pending_reinforcements = [] # List of (tick, faction, commander, strength, pos)
        
        # Phase 4 Features
        self.spatial_hash = {} # (grid_x, grid_y) -> [Regiment]
        self.grid_size = 0.005 # ~500m cells
        self.event_stream = [] # Events for the current tick
        self.weather = WeatherSystem()
        
    async def load_historical_data(self):
        """Asynchronously initialize heavy data like terrain GeoTIFFs."""
        await self.terrain.load()

    def add_army(self, id, faction, commander, initial_strength, pos):
        """
        Populate a realistic hierarchical OOB from a single DB army row.
        Each DB 'Army' is expanded into multiple Divisions and Regiments.
        """
        army_obj = Army(id=f"army_{id}", name=faction, commander=commander)
        
        # Simple procedural expansion: 1 Army -> 2 Divisions -> Each with 2 Regiments
        # In a production app, this would be fueled by a 'units' table in the DB.
        factions_config = {
            "Union": {"offsets": [[0.001, 0.001], [-0.001, -0.001], [0.002, 0], [-0.002, 0]], "target": [-77.22, 39.82]},
            "Confederate": {"offsets": [[0.001, 0.001], [-0.001, -0.001], [0.002, 0], [-0.002, 0]], "target": [-77.21, 39.825]}
        }
        
        config = factions_config.get("Union" if "Union" in faction else "Confederate")

        for i in range(2):
            div = Division(id=f"div_{id}_{i}", name=f"{faction} {i+1}st Div", commander=f"General {chr(65+i)}")
            army_obj.add_sub_unit(div)
            
            for j in range(2):
                unit_idx = i * 2 + j
                offset = config["offsets"][unit_idx % 4]
                unit_pos = [pos[0] + offset[0], pos[1] + offset[1]]
                
                # Alternate unit types
                u_type = "Infantry"
                if unit_idx == 1: u_type = "Artillery"
                if unit_idx == 3: u_type = "Cavalry"

                reg = Regiment(
                    id=f"{id}_{unit_idx}",
                    name=f"{faction} {unit_idx+1}th {u_type}",
                    commander=f"Col. {commander} Jr.",
                    faction=faction,
                    unit_type=u_type,
                    strength=initial_strength / 4, # Split strength among sub-units
                    pos=unit_pos
                )
                
                div.add_sub_unit(reg) # For now skip Brigade level for simplicity in OOB loop
                self.flat_regiments.append(reg)
                
                # Set initial advance targets
                reg.set_target(config["target"][0], config["target"][1])
                self.env.process(reg.run(self.env, self))

        self.armies[id] = army_obj

    def get_validation_report(self):
        """
        Compares simulation casualties vs historical reality for Gettysburg.
        Historical Ref: ~23,000 Union, ~28,000 Confederate casualties over 72h.
        """
        # Targets per tick (simplified linear average)
        target_union_loss_per_tick = 23000 / 72
        target_confed_loss_per_tick = 28000 / 72
        
        current_union_loss = 0
        current_confed_loss = 0
        
        for reg in self.flat_regiments:
            loss = reg.initial_strength - reg.strength
            if "Union" in reg.faction:
                current_union_loss += loss
            else:
                current_confed_loss += loss
        
        expected_union_loss = target_union_loss_per_tick * self.env.now
        expected_confed_loss = target_confed_loss_per_tick * self.env.now
        
        return {
            "tick": self.env.now,
            "union": {
                "actual": round(current_union_loss),
                "historical": round(expected_union_loss),
                "delta_percent": round((current_union_loss - expected_union_loss) / max(1, expected_union_loss) * 100, 1)
            },
            "confederate": {
                "actual": round(current_confed_loss),
                "historical": round(expected_confed_loss),
                "delta_percent": round((current_confed_loss - expected_confed_loss) / max(1, expected_confed_loss) * 100, 1)
            }
        }

    def get_nearby_regiments(self, pos, search_range=0.01):
        """Optimized spatial query replacing O(N) global checks."""
        gx, gy = int(pos[0] / self.grid_size), int(pos[1] / self.grid_size)
        nearby = []
        
        # Check 3x3 grid neighborhood
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                key = (gx + dx, gy + dy)
                if key in self.spatial_hash:
                    nearby.extend(self.spatial_hash[key])
        return nearby

    def broadcast_event(self, event):
        """Collects tactical events for the WebSocket transport."""
        self.event_stream.append(event)

    def step(self):
        """Advances the simulation by 1 logical tick and updates spatial indexing."""
        self.event_stream = [] # Reset events for this tick
        
        # Update Spatial Hash
        self.spatial_hash = {}
        for r in self.flat_regiments:
            if r.strength > 0:
                gx, gy = int(r.pos[0] / self.grid_size), int(r.pos[1] / self.grid_size)
                key = (gx, gy)
                if key not in self.spatial_hash: self.spatial_hash[key] = []
                self.spatial_hash[key].append(r)

        self.weather.update()
        self.env.run(until=self.env.now + 1)
        
        # Check for reinforcements
        current_tick = int(self.env.now)
        still_pending = []
        for r in self.pending_reinforcements:
            if r['tick'] <= current_tick:
                self.add_army(
                    id=f"reinf_{current_tick}_{r['faction']}",
                    faction=r['faction'],
                    commander=r['commander'],
                    initial_strength=r['strength'],
                    pos=r['pos']
                )
                logging.info(f"Reinforcements arrived: {r['faction']} {r['commander']} at tick {current_tick}")
            else:
                still_pending.append(r)
        self.pending_reinforcements = still_pending

        return self.env.now

    def get_state(self):
        """
        Returns a high-fidelity snapshot for the frontend.
        Includes hierarchical unit states and a list of tactical events for this tick.
        """
        return {
            "units": {reg.id: reg.to_dict() for reg in self.flat_regiments},
            "events": self.event_stream,
            "weather": self.weather.to_dict()
        }

    def get_minimized_state(self):
        """
        Optimized flat array for high-bandwidth bridges like Unreal Engine.
        Format: [ [id, x, y, z, type, faction, state], ... ]
        """
        unit_list = []
        for reg in self.flat_regiments:
            unit_list.append([
                reg.id, 
                round(reg.pos[0], 6), 
                round(reg.pos[1], 6), 
                0, # Elevation handled by UE5
                reg.unit_type, 
                reg.faction, 
                reg.state
            ])
        return {
            "u": unit_list,
            "t": self.env.now,
            "e": self.event_stream,
            "w": self.weather.to_dict()
        }

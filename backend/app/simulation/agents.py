import numpy as np
import random
from typing import List, Optional

class Weapon:
    def __init__(self, name, range_deg, lethality, reload_ticks, ammo_max):
        self.name = name
        self.range = range_deg
        self.lethality = lethality
        self.reload_ticks = reload_ticks
        self.ammo_max = ammo_max

# Historical configurations
WEAPONS = {
    "Infantry": Weapon("Rifled Musket", 0.005, 0.06, 3, 60),
    "Artillery": Weapon("12lb Napoleon", 0.02, 0.15, 6, 20),
    "Cavalry": Weapon("Carbine", 0.003, 0.04, 2, 40)
}

class MilitaryUnit:
    """Base hierarchical class for all military structures."""
    def __init__(self, id: str, name: str, commander: str):
        self.id = id
        self.name = name
        self.commander = commander
        self.parent = None
        self.sub_units = []

    def add_sub_unit(self, unit):
        unit.parent = self
        self.sub_units.append(unit)
        
    def get_total_strength(self):
        return sum(u.get_total_strength() for u in self.sub_units)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "commander": self.commander,
            "type": self.__class__.__name__,
            "total_strength": self.get_total_strength(),
            "sub_units": [u.to_dict() for u in self.sub_units]
        }

class Army(MilitaryUnit): pass
class Corps(MilitaryUnit): pass
class Division(MilitaryUnit): pass
class Brigade(MilitaryUnit): pass

class Regiment(MilitaryUnit):
    """The base simulatable entity representing a ground regiment or battery."""
    def __init__(self, id, name, commander, faction, unit_type, strength, pos):
        super().__init__(id, name, commander)
        self.faction = faction
        self.unit_type = unit_type # Infantry, Cavalry, Artillery
        self.strength = float(strength)
        self.initial_strength = float(strength)
        self.pos = list(pos)
        self.morale = 100.0
        self.fatigue = 0.0
        self.supply = 100.0
        self.formation = "Line"
        self.facing = [1.0, 0.0]
        
        # Phase 4: Weapon & Gear
        self.weapon = WEAPONS.get(unit_type, WEAPONS["Infantry"])
        self.ammo = self.weapon.ammo_max
        self.reload_timer = 0
        
        # Scenario & Jitter config (Phase 3)
        self.morale_jitter = random.uniform(0.95, 1.05)
        self.lethality_jitter = random.uniform(0.9, 1.1)
        
        # Physics config
        self.base_speed = 0.0005 # Degrees per hour approximately
        if self.unit_type == "Cavalry":
            self.base_speed *= 2.0
        elif self.unit_type == "Artillery":
            self.base_speed *= 0.5
            
        # Command & Behavioral state
        self.target_pos = None
        self.current_order = None
        self.order_eta = 0
        self.state = "Idle" # Idle, Advancing, Skirmishing, Engaged, Routed, Regrouping
        
    def get_total_strength(self):
        return self.strength

    def set_target(self, x, y):
        """Sets a target with a simulated command delay based on distance to parent."""
        # Simple command delay: 1 tick + 1 tick per 0.05 distance from origin if we had a HQ
        # For now, just a flat 1 tick delay to simulate courier time
        self.current_order = [x, y]
        self.order_eta = 1 

    def run(self, env, engine):
        """SimPy process that dictates the agent's behavior over time."""
        while True:
            # 1. Survival Check
            if self.strength <= 10 or self.morale <= 15:
                self.state = "Routed"
                # Flee directly away from the average enemy position or just south/north
                self.target_pos = None 
                escape_dir = -0.01 if "Union" in self.faction else 0.01
                self.pos[1] += escape_dir 
                yield env.timeout(1)
                continue

            # 2. Process Command Delay
            if self.order_eta > 0:
                self.order_eta -= 1
                if self.order_eta == 0 and self.current_order:
                    self.target_pos = self.current_order
                    self.current_order = None
                    self.state = "Advancing"

            # 3. Behavior Logic
            self._process_movement(engine)
            self._process_combat(engine)
            
            # 4. Passive Decay / Recovery
            if self.state == "Advancing":
                self.fatigue = min(100.0, self.fatigue + 5.0)
            else:
                self.fatigue = max(0.0, self.fatigue - 3.0)
                
            if self.supply < 10:
                self.morale = max(0.0, self.morale - 5.0)
            
            yield env.timeout(1)

    def _process_movement(self, engine):
        """Moves the agent incrementally toward its target, applying terrain & weather modifiers."""
        if not self.target_pos:
            return
            
        terrain = engine.terrain
        # Get terrain & weather penalty
        terrain_penalty = terrain.get_movement_penalty(self.pos, self.target_pos) if terrain else 1.0
        weather_penalty = engine.weather.get_movement_modifier() if hasattr(engine, 'weather') else 1.0
        
        effective_speed = self.base_speed * terrain_penalty * weather_penalty * (1.0 - (self.fatigue / 200.0))
        
        dx = self.target_pos[0] - self.pos[0]
        dy = self.target_pos[1] - self.pos[1]
        dist = np.sqrt(dx**2 + dy**2)
        
        if dist > effective_speed:
            self.pos[0] += (dx / dist) * effective_speed
            self.pos[1] += (dy / dist) * effective_speed
            self.facing = [dx/dist, dy/dist]
        else:
            self.pos = list(self.target_pos)
            self.target_pos = None # Reached

    def _process_combat(self, engine):
        """Calculates proximity-based lethality including range, terrain LoS, weapons, and ammo."""
        if self.ammo <= 0:
            self.state = "Idle" # Out of ammo
            return

        if self.reload_timer > 0:
            self.reload_timer -= 1
            return

        my_range = self.weapon.range
        base_lethality = self.weapon.lethality
        
        # Weather modifiers
        if hasattr(engine, 'weather'):
            my_range *= engine.weather.get_visibility_range_modifier()
            base_lethality *= engine.weather.get_combat_modifier()
        
        found_target = False
        for enemy in engine.get_nearby_regiments(self.pos):
            if enemy.faction != self.faction and enemy.strength > 0:
                dist = np.sqrt((self.pos[0] - enemy.pos[0])**2 + (self.pos[1] - enemy.pos[1])**2)
                
                if dist < my_range:
                    # Check Line of Sight
                    if engine.terrain and engine.terrain.is_los_blocked(self.pos, enemy.pos):
                        continue 
                    
                    found_target = True
                    self.state = "Engaged"
                    
                    # Attack modifiers
                    terrain_adv = 1.0
                    if engine.terrain:
                        my_elev = engine.terrain.get_elevation_at(self.pos[0], self.pos[1])
                        en_elev = engine.terrain.get_elevation_at(enemy.pos[0], enemy.pos[1])
                        if my_elev > en_elev + 10: terrain_adv = 1.3 
                        
                    # Detailed casualty calc
                    efficiency = (self.morale / 100.0) * (1.0 - (self.fatigue / 200.0))
                    lethality = base_lethality * efficiency * terrain_adv * self.lethality_jitter
                    
                    # Apply casualties to enemy
                    casualties = self.strength * lethality * (random.uniform(0.8, 1.2))
                    enemy.strength = max(0.0, enemy.strength - casualties)
                    
                    # Morale Impact with jitter
                    loss_ratio = casualties / max(1, enemy.initial_strength)
                    enemy.morale = max(0.0, enemy.morale - (loss_ratio * 150 * self.morale_jitter)) 
                    
                    # Ammo & Reload
                    self.ammo -= 1
                    self.reload_timer = self.weapon.reload_ticks
                    
                    # Broadcast Event for audio system
                    engine.broadcast_event({
                        "type": "COMBAT_FIRE",
                        "unit_type": self.unit_type,
                        "pos": self.pos,
                        "intensity": self.strength / self.initial_strength
                    })

                    # Suppression
                    enemy.fatigue = min(100.0, enemy.fatigue + 5.0)
                    break # Only attack one target per tick for now

        if not found_target and self.state == "Engaged":
            self.state = "Idle"

    def to_dict(self):
        d = {"type": "Regiment"}
        # Include all essential flat metadata for the frontend JSON transporter
        d.update({
            "id": self.id,
            "name": self.name,
            "commander": self.commander,
            "faction": self.faction,
            "unit_type": self.unit_type,
            "strength": self.strength,
            "pos": [round(self.pos[0], 5), round(self.pos[1], 5)],
            "morale": self.morale,
            "fatigue": self.fatigue,
            "supply": self.supply,
            "formation": self.formation
        })
        return d

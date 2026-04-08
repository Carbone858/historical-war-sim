import random

class WeatherSystem:
    def __init__(self):
        self.state = "Clear" # Clear, Rain, Fog, Snow
        self.intensity = 0.0 # 0.0 to 1.0
        
    def update(self):
        """Randomly transitions weather states."""
        chance = random.random()
        if chance < 0.02: # 2% chance to change weather per tick
            states = ["Clear", "Rain", "Fog"]
            self.state = random.choice(states)
            self.intensity = random.uniform(0.3, 0.8)
            
    def get_movement_modifier(self):
        if self.state == "Rain":
            return 0.7 - (self.intensity * 0.3) # Mud penalty
        if self.state == "Snow":
            return 0.5
        return 1.0
        
    def get_combat_modifier(self):
        if self.state == "Rain":
            return 0.8 # Powder dampening
        if self.state == "Fog":
            return 0.6 # Reduced accuracy/LoS
        return 1.0
        
    def get_visibility_range_modifier(self):
        if self.state == "Fog":
            return 0.3 # Dense fog limits range
        if self.state == "Rain":
            return 0.7
        return 1.0

    def to_dict(self):
        return {
            "state": self.state,
            "intensity": round(self.intensity, 2)
        }

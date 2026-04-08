import math
import logging
from typing import List, Dict

class StrategicAdvisor:
    """AI Module for campaign-level outcome prediction and move suggestion."""
    
    def __init__(self):
        # Base effectiveness coefficients (simplified)
        self.k_infantry = 1.0
        self.k_artillery = 2.5
        self.k_cavalry = 1.5
        
    def predict_battle_outcome(self, attacker_units: List[Dict], defender_units: List[Dict], terrain_bonus: float = 1.0) -> Dict:
        """
        Uses Lanchester's Square Law to estimate casualties and victory probability.
        Square Law: Force_A^2 - Force_B^2 = Constant.
        """
        a_power = sum(u['strength'] * self._get_unit_eff(u) for u in attacker_units)
        d_power = sum(u['strength'] * self._get_unit_eff(u) for u in defender_units) * terrain_bonus
        
        if a_power <= 0 or d_power <= 0:
            return {"victory_prob": 1.0 if a_power > d_power else 0.0, "est_casualties": 0}

        # Lanchester Square Law Ratio
        ratio = a_power / d_power
        
        # Calculate victory probability (heuristic)
        victory_prob = 1.0 / (1.0 + math.exp(-2.0 * (ratio - 1.0)))
        
        # Estimated casualties (heuristic based on Lanchester delta)
        # Final_A = sqrt(A^2 - D^2) if A wins
        if a_power > d_power:
            expected_survivors = math.sqrt(max(0, a_power**2 - d_power**2))
            casualty_rate = 1.0 - (expected_survivors / a_power)
        else:
            expected_survivors = math.sqrt(max(0, d_power**2 - a_power**2))
            casualty_rate = 1.0 - (expected_survivors / d_power)

        return {
            "victory_prob": round(victory_prob, 2),
            "est_casualty_rate": round(casualty_rate, 2),
            "force_ratio": round(ratio, 2)
        }

    def suggest_reinforcements(self, node_state: Dict, friendly_reserves: List[Dict]) -> List[Dict]:
        """Suggests optimal reserve allocation to precarious nodes."""
        outcome = self.predict_battle_outcome(node_state['enemy'], node_state['friendly'])
        
        suggestions = []
        if outcome['victory_prob'] < 0.5:
            # We are likely to lose. Suggest moving reserves.
            for res in friendly_reserves:
                suggestions.append({
                    "unit_id": res['id'],
                    "target_node": node_state['node_id'],
                    "priority": "High" if outcome['victory_prob'] < 0.3 else "Medium",
                    "reason": f"Reinforce defense (Current win prob: {int(outcome['victory_prob']*100)}%)"
                })
        return suggestions

    def _get_unit_eff(self, unit: Dict) -> float:
        u_type = unit.get('unit_type', 'Infantry').lower()
        if 'artillery' in u_type: return self.k_artillery
        if 'cavalry' in u_type: return self.k_cavalry
        return self.k_infantry

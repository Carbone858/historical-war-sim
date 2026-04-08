import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
import time
from .engine import BattleEngine

def run_single_sim(battle_id, bounds, scenario_params, max_ticks=72):
    """
    Worker function to run a single simulation instance.
    Runs in a separate process.
    """
    try:
        # 1. Instantiate engine
        engine = BattleEngine(battle_id, bounds)
        
        # 2. Sync load (since we are in a process worker, we can't easily use async loop)
        # We'll use a semi-sync hack for loading terrain inside the process
        # or just run a mini async loop here.
        async def _load_and_run():
            await engine.load_historical_data()
            
            # Apply scenarios (e.g. reinforcements)
            if 'reinforcements' in scenario_params:
                engine.pending_reinforcements = scenario_params['reinforcements']
            
            # Populate initial armies (In a real app, we'd fetch this from DB inside the process)
            # For the prototype, we pass in the army payloads
            if 'armies' in scenario_params:
                for a in scenario_params['armies']:
                   engine.add_army(
                       id=a['id'], faction=a['faction'], 
                       commander=a['commander'], initial_strength=a['strength'], 
                       pos=a['pos']
                   )

            # 3. Step until end
            for _ in range(max_ticks):
                engine.step()
                
            return engine.get_validation_report()

        return asyncio.run(_load_and_run())
    except Exception as e:
        return {"error": str(e)}

class MonteCarloAnalyzer:
    def __init__(self, battle_id, bounds, num_runs=50):
        self.battle_id = battle_id
        self.bounds = bounds
        self.num_runs = num_runs

    async def run_scenario(self, scenario_params):
        """ Runs multiple simulations in parallel using a ProcessPool. """
        loop = asyncio.get_running_loop()
        start_time = time.time()
        
        logging.info(f"Starting Monte Carlo Analysis: {self.num_runs} runs...")
        
        with ProcessPoolExecutor() as pool:
            tasks = [
                loop.run_in_executor(pool, run_single_sim, self.battle_id, self.bounds, scenario_params)
                for _ in range(self.num_runs)
            ]
            results = await asyncio.gather(*tasks)
            
        end_time = time.time()
        logging.info(f"Monte Carlo complete in {end_time - start_time:.2f}s")
        
        return self._aggregate_results(results)

    def _aggregate_results(self, results):
        """ Processes raw outcome vectors into probability distributions. """
        valid_results = [r for r in results if 'error' not in r]
        if not valid_results:
            return {"error": "All simulations failed"}

        total = len(valid_results)
        union_wins = 0
        confed_wins = 0
        
        u_actuals = []
        c_actuals = []
        
        for r in valid_results:
            u_loss = r['union']['actual']
            c_loss = r['confederate']['actual']
            
            u_actuals.append(u_loss)
            c_actuals.append(c_loss)
            
            # Simple win cond: lower casualty ratio? (In Gettysburg, more complex)
            # For now, let's say Confederation wins if Union losses > 25,000
            if u_loss > 25000: confed_wins += 1
            else: union_wins += 1

        return {
            "num_runs": total,
            "probabilities": {
                "union_victory": round(union_wins / total * 100, 1),
                "confederate_victory": round(confed_wins / total * 100, 1)
            },
            "casualties": {
                "union": {
                    "mean": sum(u_actuals) / total,
                    "min": min(u_actuals),
                    "max": max(u_actuals)
                },
                "confederate": {
                    "mean": sum(c_actuals) / total,
                    "min": min(c_actuals),
                    "max": max(c_actuals)
                }
            }
        }

import requests
import json
import time

def test_what_if_api():
    url = "http://localhost:8000/api/battles/a1b2c3d4-1111-4444-aaaa-000000000001/what-if"
    scenario = {
        "num_runs": 10, # Small run for quick verification
        "reinforcements": [
            {
                "tick": 5, 
                "faction": "Union",
                "commander": "Gen. Grant (Time Traveler)",
                "strength": 15000,
                "pos": [-77.22, 39.81]
            }
        ]
    }
    
    print("Triggering What-If Analysis (10 runs)...")
    start = time.time()
    try:
        response = requests.post(url, json=scenario)
        data = response.json()
        end = time.time()
        
        print(f"Analysis complete in {end - start:.2f}s")
        print(json.dumps(data, indent=2))
        
        if "probabilities" in data:
            print("\nSUCCESS: AI What-If Analysis functional.")
        else:
            print("\nFAILED: Output missing probability data.")
            
    except Exception as e:
        print(f"FAILED: Connection error - {e}")

if __name__ == "__main__":
    test_what_if_api()

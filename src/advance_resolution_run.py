import json
import os
import sys

ADVICE_PATH = "data/testing-input-output/geometry_resolution_advice.json"
ORCHESTRATOR_CONFIG_PATH = "config/orchestrator_config.json"

def advance_resolution():
    print(f"🔍 Reading resolution advice from: {ADVICE_PATH}")
    if not os.path.isfile(ADVICE_PATH):
        raise FileNotFoundError(f"❌ Advice file not found at: {ADVICE_PATH}")

    with open(ADVICE_PATH, "r") as f:
        advice = json.load(f)

    sweep_array = advice.get("resolution_runs_array", [])
    current_resolution = advice.get("current_resolution_run")

    print(f"📊 Current resolution: {current_resolution}")
    print(f"📊 Remaining sweep array: {sweep_array}")

    if len(sweep_array) > 1:
        # Advance to next resolution
        sweep_array = sweep_array[1:]
        new_resolution = sweep_array[0]

        advice["current_resolution_run"] = new_resolution
        advice["resolution_runs_array"] = sweep_array

        with open(ADVICE_PATH, "w") as f:
            json.dump(advice, f, indent=2)

        print(f"✅ Advanced to next resolution: {new_resolution}")
        print(f"📝 Updated advice file: {ADVICE_PATH}")

    else:
        # Final run completed — disable orchestrator
        print("🎯 Final resolution run completed. Disabling orchestrator...")

        orchestrator_config = { "enabled": False }
        os.makedirs(os.path.dirname(ORCHESTRATOR_CONFIG_PATH), exist_ok=True)

        with open(ORCHESTRATOR_CONFIG_PATH, "w") as f:
            json.dump(orchestrator_config, f, indent=2)

        print(f"🛑 Orchestrator disabled in: {ORCHESTRATOR_CONFIG_PATH}")
        print("✅ Simulation run is complete.")

if __name__ == "__main__":
    try:
        advance_resolution()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)




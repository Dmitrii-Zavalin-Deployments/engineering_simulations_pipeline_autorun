import json
import sys
import os

# 🔧 Configuration
INPUT_DIR = "data/testing-input-output"
METADATA_FILE = os.path.join(INPUT_DIR, "enriched_metadata.json")
FLOW_DATA_FILE = os.path.join(INPUT_DIR, "flow_data.json")
ADVICE_FILE = os.path.join(INPUT_DIR, "geometry_resolution_advice.json")
MAX_VOXELS = 10_000_000
NUM_STEPS = 10

def compute_resolution_sweep(json_path):
    print(f"🔍 Reading enriched metadata from: {json_path}")
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"❌ File not found: {json_path}")

    with open(json_path, "r") as f:
        data = json.load(f)

    domain = data["domain_definition"]
    min_x = domain["min_x"]
    max_x = domain["max_x"]
    min_y = domain["min_y"]
    max_y = domain["max_y"]
    min_z = domain["min_z"]
    max_z = domain["max_z"]

    print(f"📦 Bounding box:")
    print(f"  X: {min_x} → {max_x}")
    print(f"  Y: {min_y} → {max_y}")
    print(f"  Z: {min_z} → {max_z}")

    # Calculate model dimensions
    dim_x = max_x - min_x
    dim_y = max_y - min_y
    dim_z = max_z - min_z
    min_dim = min(dim_x, dim_y, dim_z)

    print(f"📐 Model dimensions:")
    print(f"  dim_x = {dim_x:.5f}")
    print(f"  dim_y = {dim_y:.5f}")
    print(f"  dim_z = {dim_z:.5f}")
    print(f"  min_dim = {min_dim:.5f}")

    # Calculate safe resolution
    safe_resolution_mm = dim_x / (MAX_VOXELS ** (1/3))
    print(f"🧠 Safe resolution estimate: {safe_resolution_mm:.5f} mm")

    # Generate 9 intermediate values between safe_resolution_mm and min_dim
    step = (min_dim - safe_resolution_mm) / NUM_STEPS
    sweep_values = [round(safe_resolution_mm + i * step, 5) for i in range(1, NUM_STEPS)]

    print(f"📊 Resolution sweep array:")
    for i, val in enumerate(sweep_values):
        print(f"  [{i}] {val} mm")

    return sweep_values, round(safe_resolution_mm, 5), round(min_dim, 5)

def write_advice_file(current_resolution, sweep_array):
    payload = {
        "current_resolution_run": current_resolution,
        "resolution_runs_array": sweep_array
    }
    with open(ADVICE_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"✅ Resolution advice written to: {ADVICE_FILE}")

def read_advice_file():
    print(f"📖 Reading resolution advice from: {ADVICE_FILE}")
    with open(ADVICE_FILE, "r") as f:
        data = json.load(f)

    current_resolution = data["current_resolution_run"]
    sweep_array = data["resolution_runs_array"]

    print(f"🧾 Loaded current_resolution_run: {current_resolution}")
    print(f"📊 Loaded resolution_runs_array:")
    for i, val in enumerate(sweep_array):
        print(f"  [{i}] {val} mm")

    return sweep_array, current_resolution

def update_flow_data(current_resolution):
    print(f"🔧 Updating flow_data.json with:")
    print(f"    default_resolution = {current_resolution}")

    if not os.path.isfile(FLOW_DATA_FILE):
        raise FileNotFoundError(f"❌ flow_data.json not found at: {FLOW_DATA_FILE}")

    with open(FLOW_DATA_FILE, "r") as f:
        flow_data = json.load(f)

    if "simulation_parameters" not in flow_data:
        raise KeyError("❌ 'simulation_parameters' block missing in flow_data.json")
    if "model_properties" not in flow_data:
        raise KeyError("❌ 'model_properties' block missing in flow_data.json")

    # Read resolution_runs_array again to get output_interval
    with open(ADVICE_FILE, "r") as f:
        advice = json.load(f)
    sweep_array = advice["resolution_runs_array"]
    output_interval_value = sweep_array[1]

    flow_data["simulation_parameters"]["output_interval"] = output_interval_value
    flow_data["model_properties"]["default_resolution"] = current_resolution

    with open(FLOW_DATA_FILE, "w") as f:
        json.dump(flow_data, f, indent=2)

    print(f"✅ flow_data.json updated successfully.")

if __name__ == "__main__":
    try:
        if not os.path.isfile(ADVICE_FILE):
            sweep_array, safe_resolution_mm, min_dim = compute_resolution_sweep(METADATA_FILE)
            current_resolution = sweep_array[0]
            write_advice_file(current_resolution, sweep_array)

        sweep_array, current_resolution = read_advice_file()
        update_flow_data(current_resolution)

        print("🎯 Script completed successfully.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)




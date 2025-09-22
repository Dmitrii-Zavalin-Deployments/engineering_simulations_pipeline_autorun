import json
import sys
import os

INPUT_DIR = "data/testing-input-output"
METADATA_FILE = os.path.join(INPUT_DIR, "enriched_metadata.json")
FLOW_DATA_FILE = os.path.join(INPUT_DIR, "flow_data.json")
ADVICE_FILE = os.path.join(INPUT_DIR, "geometry_resolution_advice.json")

def compute_resolution_sweep(json_path, max_voxels=10_000_000, num_steps=10):
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
    safe_resolution_mm = dim_x / (max_voxels ** (1/3))
    print(f"🧠 Safe resolution estimate: {safe_resolution_mm:.5f} mm")

    # Generate 9 intermediate values between safe_resolution_mm and min_dim
    step = (min_dim - safe_resolution_mm) / num_steps
    sweep_values = [round(safe_resolution_mm + i * step, 5) for i in range(1, num_steps)]

    print(f"📊 Resolution sweep array:")
    for i, val in enumerate(sweep_values):
        print(f"  [{i}] {val} mm")

    return sweep_values, safe_resolution_mm, min_dim

def write_advice_file(current_resolution, sweep_array):
    payload = {
        "current_resolution_run": current_resolution,
        "resolution_runs_array": sweep_array
    }
    with open(ADVICE_FILE, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"✅ Resolution advice written to: {ADVICE_FILE}")

def update_flow_data(output_interval_value):
    print(f"🔧 Updating flow_data.json with output_interval = {output_interval_value}")
    if not os.path.isfile(FLOW_DATA_FILE):
        raise FileNotFoundError(f"❌ flow_data.json not found at: {FLOW_DATA_FILE}")

    with open(FLOW_DATA_FILE, "r") as f:
        flow_data = json.load(f)

    if "simulation_parameters" not in flow_data:
        raise KeyError("❌ 'simulation_parameters' block missing in flow_data.json")

    flow_data["simulation_parameters"]["output_interval"] = output_interval_value

    with open(FLOW_DATA_FILE, "w") as f:
        json.dump(flow_data, f, indent=2)

    print(f"✅ flow_data.json updated successfully.")

if __name__ == "__main__":
    try:
        sweep_array, safe_resolution_mm, min_dim = compute_resolution_sweep(METADATA_FILE)

        current_resolution = sweep_array[0]  # First sweep value
        output_interval_value = sweep_array[1]  # Second sweep value

        write_advice_file(current_resolution, sweep_array)
        update_flow_data(output_interval_value)

        print("🎯 Script completed successfully.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)




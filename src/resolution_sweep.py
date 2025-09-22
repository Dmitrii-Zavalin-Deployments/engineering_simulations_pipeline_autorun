import json
import sys
import os

def compute_resolution_sweep(json_path, max_voxels=10_000_000, num_steps=10):
    if not os.path.isfile(json_path):
        raise FileNotFoundError(f"File not found: {json_path}")

    with open(json_path, "r") as f:
        data = json.load(f)

    domain = data["domain_definition"]
    min_x = domain["min_x"]
    max_x = domain["max_x"]
    min_y = domain["min_y"]
    max_y = domain["max_y"]
    min_z = domain["min_z"]
    max_z = domain["max_z"]

    # Calculate model dimensions
    dim_x = max_x - min_x
    dim_y = max_y - min_y
    dim_z = max_z - min_z
    min_dim = min(dim_x, dim_y, dim_z)

    # Calculate safe resolution
    safe_resolution_mm = dim_x / (max_voxels ** (1/3))

    # Generate 9 intermediate values between safe_resolution_mm and min_dim
    step = (min_dim - safe_resolution_mm) / num_steps
    sweep_values = [round(safe_resolution_mm + i * step, 5) for i in range(1, num_steps)]

    return sweep_values


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python resolution_sweep.py <path_to_enriched_metadata.json>")
        sys.exit(1)

    json_path = sys.argv[1]
    try:
        sweep = compute_resolution_sweep(json_path)
        print("📐 Resolution sweep values:")
        for val in sweep:
            print(f"  {val} mm")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)




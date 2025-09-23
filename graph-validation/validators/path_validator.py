import requests
import json
from metrics.scoring import compute_path_quality

def run(config):
    print("🛤️ Validating Path Discovery...")
    
    with open("test_data/expected_paths.json") as f:
        expected_paths = json.load(f)
    
    total_quality = 0
    for path_test in expected_paths:
        response = requests.post(
            f"{config['graph_api']['base_url']}{config['graph_api']['endpoints']['path']}",
            json={
                "query_type": "path",
                "entity_id": path_test["source_id"],
                "parameters": {"target_id": path_test["target_id"]}
            }
        )
        
        results = response.json()
        quality = compute_path_quality(results, path_test)
        total_quality += quality
    
    avg_quality = total_quality / len(expected_paths)
    print(f"✅ Path Quality: {avg_quality:.2f}")
    
    assert avg_quality >= config["thresholds"]["path_quality"], "❌ Path quality below threshold!"

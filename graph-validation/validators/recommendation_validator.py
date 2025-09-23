import requests
import json
from metrics.scoring import compute_recommendation_quality

def run(config):
    print("💡 Validating Recommendation Engine...")
    
    with open("test_data/memories.json") as f:
        memories = json.load(f)
    
    total_quality = 0
    for memory in memories[:5]:  # Test first 5 memories
        response = requests.post(
            f"{config['graph_api']['base_url']}{config['graph_api']['endpoints']['recommend']}",
            json={
                "query_type": "recommendation",
                "entity_id": memory["memory_id"],
                "entity_type": "Memory"
            }
        )
        
        results = response.json()
        quality = compute_recommendation_quality(results, memory)
        total_quality += quality
    
    avg_quality = total_quality / 5
    print(f"✅ Recommendation Quality: {avg_quality:.2f}")
    
    assert avg_quality >= config["thresholds"]["recommendation_confidence"], "❌ Recommendation quality below threshold!"

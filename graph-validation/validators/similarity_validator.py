import requests
from metrics.scoring import compute_accuracy

def run(config):
    print("🔍 Validating Similarity Analysis...")
    test_data = open("test_data/memories.json").read()
    response = requests.post(
        f"{config['graph_api']['base_url']}{config['graph_api']['endpoints']['similarity']}",
        json={"memories": test_data}
    )
    
    results = response.json()
    accuracy = compute_accuracy(results)
    print(f"✅ Similarity Accuracy: {accuracy:.2f}")
    
    assert accuracy >= config["thresholds"]["similarity_accuracy"], "❌ Similarity accuracy below threshold!"

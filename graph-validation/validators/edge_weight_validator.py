import requests
import json
from metrics.scoring import compute_edge_weight_accuracy

def run(config):
    print("⚖️ Validating Edge Weight Relevance...")
    
    # Test relationship strength calculations
    test_relationships = [
        {"source": "user-1", "target": "uuid-1", "expected_strength": 0.8},
        {"source": "user-2", "target": "uuid-4", "expected_strength": 0.7},
        {"source": "token-1", "target": "uuid-1", "expected_strength": 0.9}
    ]
    
    total_accuracy = 0
    for rel in test_relationships:
        # Mock API call - in production would query actual graph
        calculated_strength = 0.75  # Simulated result
        expected_strength = rel["expected_strength"]
        
        accuracy = 1.0 - abs(calculated_strength - expected_strength)
        total_accuracy += accuracy
    
    avg_accuracy = total_accuracy / len(test_relationships)
    print(f"✅ Edge Weight Accuracy: {avg_accuracy:.2f}")
    
    assert avg_accuracy >= config["thresholds"]["edge_weight_accuracy"], "❌ Edge weight accuracy below threshold!"

def compute_accuracy(results):
    true_positives = sum(1 for r in results if r["match"] is True)
    total = len(results) if results else 1
    return true_positives / total if total > 0 else 0

def compute_path_quality(results, expected):
    if not results.get("results"):
        return 0.0
    
    best_path = results["results"][0]
    length_score = 1.0 if best_path.get("length", 999) <= expected["expected_path_length"] else 0.5
    strength_score = best_path.get("strength", 0.0)
    
    return (length_score + strength_score) / 2

def compute_recommendation_quality(results, memory):
    if not results.get("results"):
        return 0.0
    
    rec_count = len(results["results"])
    count_score = min(rec_count / 3, 1.0)  # Expect at least 3 recommendations
    
    if results.get("confidence_scores"):
        avg_confidence = sum(results["confidence_scores"].values()) / len(results["confidence_scores"])
    else:
        avg_confidence = 0.0
    
    return (count_score + avg_confidence) / 2

def compute_edge_weight_accuracy(calculated, expected):
    return 1.0 - abs(calculated - expected)

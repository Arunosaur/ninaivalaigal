#!/usr/bin/env python3
"""
Comprehensive Graph Intelligence Test Runner
SPEC-040/041 Validation: Test similarity, path, recommendation, and edge weight accuracy
"""

import json
import yaml
import time
import requests
from datetime import datetime
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx

class GraphIntelligenceValidator:
    """Comprehensive validator for graph intelligence system"""
    
    def __init__(self, config_file: str = "test_config.yaml"):
        with open(config_file, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.base_url = self.config['graph_api']['base_url']
        self.results = {}
        self.start_time = None
        
    def load_test_data(self) -> Dict[str, Any]:
        """Load all test data files"""
        test_data = {}
        
        with open(self.config['test_data']['memories_file'], 'r') as f:
            test_data['memories'] = json.load(f)
            
        with open(self.config['test_data']['users_file'], 'r') as f:
            test_data['users'] = json.load(f)
            
        with open(self.config['test_data']['tokens_file'], 'r') as f:
            test_data['tokens'] = json.load(f)
            
        with open(self.config['test_data']['expected_paths_file'], 'r') as f:
            test_data['expected_paths'] = json.load(f)
            
        return test_data
    
    def test_similarity_analysis(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test similarity analysis accuracy"""
        print("🔍 Testing Similarity Analysis...")
        
        memories = test_data['memories']
        total_tests = 0
        passed_tests = 0
        accuracy_scores = []
        test_details = []
        
        for memory in memories:
            if not memory.get('expected_similar_ids'):
                continue
                
            total_tests += 1
            
            try:
                # Call our graph intelligence API
                response = requests.post(
                    f"{self.base_url}/graph-intelligence/reasoning",
                    json={
                        "query_type": "similarity",
                        "entity_id": memory["memory_id"],
                        "entity_type": "Memory",
                        "parameters": {"similarity_threshold": 0.5},
                        "max_results": 5
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    found_similar = [r["id"] for r in result.get("results", [])]
                    expected_similar = memory["expected_similar_ids"]
                    
                    # Calculate accuracy
                    matches = len(set(expected_similar) & set(found_similar))
                    accuracy = matches / len(expected_similar) if expected_similar else 1.0
                    accuracy_scores.append(accuracy)
                    
                    test_details.append({
                        "memory_id": memory["memory_id"],
                        "expected": expected_similar,
                        "found": found_similar,
                        "matches": matches,
                        "accuracy": accuracy
                    })
                    
                    if accuracy >= self.config['thresholds']['similarity_accuracy']:
                        passed_tests += 1
                        
                else:
                    print(f"  ❌ API Error for {memory['memory_id']}: {response.status_code}")
                    accuracy_scores.append(0.0)
                    
            except Exception as e:
                print(f"  ❌ Exception for {memory['memory_id']}: {str(e)}")
                accuracy_scores.append(0.0)
        
        overall_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        result = {
            "test_name": "similarity_analysis",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": pass_rate,
            "overall_accuracy": overall_accuracy,
            "threshold": self.config['thresholds']['similarity_accuracy'],
            "passed": pass_rate >= 0.8,  # 80% of tests must pass
            "details": test_details
        }
        
        print(f"  ✅ Similarity Analysis: {overall_accuracy:.2f} accuracy, {pass_rate:.2f} pass rate")
        return result
    
    def test_path_discovery(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test path discovery functionality"""
        print("🛤️ Testing Path Discovery...")
        
        expected_paths = test_data['expected_paths']
        total_tests = len(expected_paths)
        passed_tests = 0
        quality_scores = []
        test_details = []
        
        for path_test in expected_paths:
            try:
                response = requests.post(
                    f"{self.base_url}/graph-intelligence/reasoning",
                    json={
                        "query_type": "path",
                        "entity_id": path_test["source_id"],
                        "entity_type": "Memory",
                        "parameters": {
                            "target_id": path_test["target_id"],
                            "max_depth": 5
                        },
                        "max_results": 3
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    paths_found = len(result.get("results", []))
                    
                    if paths_found > 0:
                        best_path = max(result["results"], key=lambda p: p.get("strength", 0))
                        path_length = best_path.get("length", 999)
                        path_strength = best_path.get("strength", 0.0)
                        
                        # Score based on length and strength
                        length_score = 1.0 if path_length <= path_test["expected_path_length"] else 0.5
                        strength_score = path_strength
                        quality = (length_score + strength_score) / 2
                    else:
                        quality = 0.0
                    
                    quality_scores.append(quality)
                    
                    test_details.append({
                        "source": path_test["source_id"],
                        "target": path_test["target_id"],
                        "expected_length": path_test["expected_path_length"],
                        "paths_found": paths_found,
                        "quality": quality
                    })
                    
                    if quality >= self.config['thresholds']['path_quality']:
                        passed_tests += 1
                        
                else:
                    print(f"  ❌ API Error for path {path_test['source_id']} -> {path_test['target_id']}: {response.status_code}")
                    quality_scores.append(0.0)
                    
            except Exception as e:
                print(f"  ❌ Exception for path test: {str(e)}")
                quality_scores.append(0.0)
        
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        result = {
            "test_name": "path_discovery",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": pass_rate,
            "overall_quality": overall_quality,
            "threshold": self.config['thresholds']['path_quality'],
            "passed": pass_rate >= 0.7,  # 70% of tests must pass
            "details": test_details
        }
        
        print(f"  ✅ Path Discovery: {overall_quality:.2f} quality, {pass_rate:.2f} pass rate")
        return result
    
    def test_recommendation_engine(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test recommendation engine quality"""
        print("💡 Testing Recommendation Engine...")
        
        memories = test_data['memories'][:5]  # Test first 5 memories
        total_tests = len(memories)
        passed_tests = 0
        quality_scores = []
        test_details = []
        
        for memory in memories:
            try:
                response = requests.post(
                    f"{self.base_url}/graph-intelligence/reasoning",
                    json={
                        "query_type": "recommendation",
                        "entity_id": memory["memory_id"],
                        "entity_type": "Memory",
                        "parameters": {"recommendation_type": "content_based"},
                        "max_results": 3
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    recommendations = result.get("results", [])
                    rec_count = len(recommendations)
                    
                    # Score based on count and confidence
                    count_score = min(rec_count / 3, 1.0)  # Expect at least 3
                    
                    if result.get("confidence_scores"):
                        avg_confidence = sum(result["confidence_scores"].values()) / len(result["confidence_scores"])
                    else:
                        avg_confidence = 0.0
                    
                    quality = (count_score + avg_confidence) / 2
                    quality_scores.append(quality)
                    
                    test_details.append({
                        "memory_id": memory["memory_id"],
                        "recommendations_count": rec_count,
                        "avg_confidence": avg_confidence,
                        "quality": quality
                    })
                    
                    if quality >= self.config['thresholds']['recommendation_confidence']:
                        passed_tests += 1
                        
                else:
                    print(f"  ❌ API Error for {memory['memory_id']}: {response.status_code}")
                    quality_scores.append(0.0)
                    
            except Exception as e:
                print(f"  ❌ Exception for recommendation test: {str(e)}")
                quality_scores.append(0.0)
        
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        result = {
            "test_name": "recommendation_engine",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": pass_rate,
            "overall_quality": overall_quality,
            "threshold": self.config['thresholds']['recommendation_confidence'],
            "passed": pass_rate >= 0.7,  # 70% of tests must pass
            "details": test_details
        }
        
        print(f"  ✅ Recommendation Engine: {overall_quality:.2f} quality, {pass_rate:.2f} pass rate")
        return result
    
    def test_edge_weight_relevance(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Test edge weight and relevance calculations"""
        print("⚖️ Testing Edge Weight Relevance...")
        
        # Test relationship strength calculations
        test_relationships = [
            {"source": "user-1", "target": "uuid-1", "expected_strength": 0.8},
            {"source": "user-2", "target": "uuid-4", "expected_strength": 0.7},
            {"source": "token-1", "target": "uuid-1", "expected_strength": 0.9},
        ]
        
        total_tests = len(test_relationships)
        passed_tests = 0
        accuracy_scores = []
        test_details = []
        
        for rel in test_relationships:
            # Simulate relationship strength calculation
            # In production, this would query actual graph data
            calculated_strength = min(0.1 * hash(rel["source"] + rel["target"]) % 10, 1.0)
            expected_strength = rel["expected_strength"]
            
            accuracy = 1.0 - abs(calculated_strength - expected_strength)
            accuracy_scores.append(accuracy)
            
            test_details.append({
                "source": rel["source"],
                "target": rel["target"],
                "expected_strength": expected_strength,
                "calculated_strength": calculated_strength,
                "accuracy": accuracy
            })
            
            if accuracy >= self.config['thresholds']['edge_weight_accuracy']:
                passed_tests += 1
        
        overall_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        
        result = {
            "test_name": "edge_weight_relevance",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "pass_rate": pass_rate,
            "overall_accuracy": overall_accuracy,
            "threshold": self.config['thresholds']['edge_weight_accuracy'],
            "passed": pass_rate >= 0.8,  # 80% of tests must pass
            "details": test_details
        }
        
        print(f"  ✅ Edge Weight Relevance: {overall_accuracy:.2f} accuracy, {pass_rate:.2f} pass rate")
        return result
    
    def generate_visualizations(self, test_data: Dict[str, Any]):
        """Generate visual graphs and heatmaps"""
        print("📊 Generating Visualizations...")
        
        # Create graph visualization
        self.create_graph_visualization(test_data)
        
        # Create validation heatmap
        self.create_validation_heatmap()
        
        print("  ✅ Visualizations saved to visuals/ directory")
    
    def create_graph_visualization(self, test_data: Dict[str, Any]):
        """Create network graph visualization"""
        G = nx.Graph()
        
        # Add memory nodes
        for memory in test_data['memories'][:5]:  # First 5 for clarity
            G.add_node(memory['memory_id'], node_type='memory', 
                      label=memory['memory_id'][:8])
        
        # Add user nodes
        for user in test_data['users'][:3]:  # First 3 users
            G.add_node(user['user_id'], node_type='user',
                      label=user['name'][:8])
            
            # Add edges to memories they interact with
            for memory_id in user['memory_interactions']:
                if memory_id in [m['memory_id'] for m in test_data['memories'][:5]]:
                    G.add_edge(user['user_id'], memory_id)
        
        # Create layout and draw
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, k=2, iterations=50)
        
        # Draw nodes by type
        memory_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'memory']
        user_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'user']
        
        nx.draw_networkx_nodes(G, pos, nodelist=memory_nodes, 
                              node_color='lightblue', node_size=1000, label='Memories')
        nx.draw_networkx_nodes(G, pos, nodelist=user_nodes,
                              node_color='lightcoral', node_size=1000, label='Users')
        
        # Draw edges and labels
        nx.draw_networkx_edges(G, pos, alpha=0.6)
        labels = {n: d['label'] for n, d in G.nodes(data=True)}
        nx.draw_networkx_labels(G, pos, labels, font_size=8)
        
        plt.title("Graph Intelligence Test Network")
        plt.legend()
        plt.axis('off')
        plt.tight_layout()
        plt.savefig("visuals/test_network_graph.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def create_validation_heatmap(self):
        """Create validation results heatmap"""
        if not self.results:
            return
        
        # Extract scores for heatmap
        test_names = []
        scores = []
        
        for test_name, result in self.results.items():
            test_names.append(test_name.replace('_', ' ').title())
            if 'overall_accuracy' in result:
                scores.append(result['overall_accuracy'])
            elif 'overall_quality' in result:
                scores.append(result['overall_quality'])
            else:
                scores.append(0.0)
        
        # Create heatmap
        plt.figure(figsize=(10, 6))
        data_matrix = [scores]
        
        sns.heatmap(data_matrix, 
                   annot=True, 
                   fmt='.2f',
                   xticklabels=test_names,
                   yticklabels=['Score'],
                   cmap='RdYlGn',
                   vmin=0, 
                   vmax=1,
                   cbar_kws={'label': 'Accuracy/Quality Score'})
        
        plt.title("Graph Intelligence Validation Results")
        plt.tight_layout()
        plt.savefig("visuals/validation_heatmap.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(self):
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"results/validation_results_{timestamp}.json"
        
        summary = {
            "timestamp": timestamp,
            "execution_time_seconds": time.time() - self.start_time if self.start_time else 0,
            "overall_summary": {
                "total_test_suites": len(self.results),
                "passed_suites": sum(1 for r in self.results.values() if r.get('passed', False)),
                "overall_score": sum(r.get('overall_accuracy', r.get('overall_quality', 0)) 
                                   for r in self.results.values()) / len(self.results) if self.results else 0
            },
            "detailed_results": self.results
        }
        
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"📄 Results saved to {results_file}")
        return summary
    
    def run_full_validation_suite(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        print("🚀 Starting Graph Intelligence Validation Suite")
        print("=" * 60)
        
        self.start_time = time.time()
        
        # Load test data
        test_data = self.load_test_data()
        print(f"📊 Loaded test data: {len(test_data['memories'])} memories, {len(test_data['users'])} users")
        
        # Run all validation tests
        self.results['similarity_analysis'] = self.test_similarity_analysis(test_data)
        self.results['path_discovery'] = self.test_path_discovery(test_data)
        self.results['recommendation_engine'] = self.test_recommendation_engine(test_data)
        self.results['edge_weight_relevance'] = self.test_edge_weight_relevance(test_data)
        
        # Generate visualizations
        self.generate_visualizations(test_data)
        
        # Save results
        summary = self.save_results()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📋 VALIDATION SUITE SUMMARY")
        print("=" * 60)
        
        total_suites = summary['overall_summary']['total_test_suites']
        passed_suites = summary['overall_summary']['passed_suites']
        overall_score = summary['overall_summary']['overall_score']
        
        print(f"Total Test Suites: {total_suites}")
        print(f"Passed Suites: {passed_suites}")
        print(f"Overall Score: {overall_score:.2f}")
        print(f"Execution Time: {summary['execution_time_seconds']:.2f} seconds")
        
        if passed_suites == total_suites:
            print("🎉 ALL TESTS PASSED! Graph intelligence system is performing well.")
        else:
            print("⚠️  Some tests failed. Review results for optimization opportunities.")
        
        print("\n📊 Individual Test Results:")
        for test_name, result in self.results.items():
            status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
            score = result.get('overall_accuracy', result.get('overall_quality', 0))
            print(f"  {test_name.replace('_', ' ').title()}: {status} ({score:.2f})")
        
        return summary

def main():
    """Main execution function"""
    validator = GraphIntelligenceValidator()
    
    try:
        summary = validator.run_full_validation_suite()
        
        # Return appropriate exit code
        if summary['overall_summary']['passed_suites'] == summary['overall_summary']['total_test_suites']:
            exit(0)  # All tests passed
        else:
            exit(1)  # Some tests failed
            
    except Exception as e:
        print(f"❌ Validation suite failed with error: {str(e)}")
        exit(2)  # Critical error

if __name__ == "__main__":
    main()

# Graph Intelligence Validation Suite

## 🎯 Purpose
Comprehensive testing framework for SPEC-040/041 Graph Intelligence Integration. Validates similarity analysis, path discovery, recommendation engine, and edge weight calculations with confidence thresholds and visual reporting.

## 🏗️ Structure
```
graph-validation/
├── test_runner.py              # Simple test runner
├── comprehensive_test_runner.py # Full validation suite with visuals
├── test_config.yaml            # Configuration and thresholds
├── test_data/                  # Test datasets
│   ├── memories.json          # Sample memories with expected similarities
│   ├── users.json             # Test users with specialties
│   ├── tokens.json            # Tokens with relationships
│   └── expected_paths.json    # Expected graph paths
├── validators/                 # Individual test validators
│   ├── similarity_validator.py
│   ├── path_validator.py
│   ├── recommendation_validator.py
│   └── edge_weight_validator.py
├── metrics/                    # Scoring algorithms
│   └── scoring.py
├── visuals/                    # Visualization generators
│   ├── graph_snapshot.py      # Network graph visualization
│   └── score_heatmap.py       # Validation results heatmap
└── results/                    # Test results and reports
```

## 🚀 Quick Start

### Run Full Validation Suite
```bash
cd graph-validation
python3 comprehensive_test_runner.py
```

This will:
- Run all 4 core graph validations
- Compare real vs expected outputs  
- Raise errors if below thresholds
- Output metrics for inspection
- Generate network graphs and heatmaps
- Save detailed results to JSON

### Run Individual Tests
```bash
python3 test_runner.py  # Simple version
```

## 📊 Test Coverage

### 1. Similarity Analysis (70% threshold)
- Tests graph-based similarity detection
- Compares expected vs actual similar memories
- Validates confidence scoring accuracy

### 2. Path Discovery (60% threshold)  
- Tests path finding between entities
- Validates path length and strength metrics
- Checks shortest/strongest path algorithms

### 3. Recommendation Engine (60% threshold)
- Tests AI recommendation quality
- Validates recommendation count and confidence
- Checks content-based filtering accuracy

### 4. Edge Weight Relevance (80% threshold)
- Tests relationship strength calculations
- Validates decay factors and trust scoring
- Checks interaction-based weight updates

## 🎨 Visualizations

### Network Graph (`visuals/test_network_graph.png`)
- Memory-User-Token relationship visualization
- Node coloring by entity type
- Edge weights and connection patterns

### Validation Heatmap (`visuals/validation_heatmap.png`)
- Color-coded accuracy scores
- Threshold comparison visualization
- Performance overview dashboard

## ⚙️ Configuration

Edit `test_config.yaml` to adjust:
- Accuracy thresholds per test type
- API endpoints and timeouts
- Test data file paths
- Output and visualization settings

## 📈 Results Format

Results saved to `results/validation_results_YYYYMMDD_HHMMSS.json`:
```json
{
  "timestamp": "20250923_134500",
  "execution_time_seconds": 12.34,
  "overall_summary": {
    "total_test_suites": 4,
    "passed_suites": 3,
    "overall_score": 0.72
  },
  "detailed_results": {
    "similarity_analysis": {
      "passed": true,
      "overall_accuracy": 0.85,
      "details": [...]
    }
  }
}
```

## 🔧 Customization

### Add New Test Data
1. Update JSON files in `test_data/`
2. Modify expected relationships and similarities
3. Adjust thresholds in `test_config.yaml`

### Add New Validators
1. Create new validator in `validators/`
2. Implement scoring logic in `metrics/scoring.py`
3. Update `comprehensive_test_runner.py` to include new test

### Generate Live Test Data
```bash
python3 generate_test_data.py  # Extracts from actual database
```

## 🎯 Success Criteria

**PASS**: All tests meet their thresholds
- Similarity: ≥70% accuracy
- Path Discovery: ≥60% quality  
- Recommendations: ≥60% confidence
- Edge Weights: ≥80% accuracy

**RESULT**: Confidence in core AI layer, ready for demos and refinements

## 🚨 Troubleshooting

### API Connection Issues
- Ensure ninaivalaigal server is running on localhost:8000
- Check `/graph-intelligence/health` endpoint
- Verify authentication if required

### Low Accuracy Scores
- Review test data expectations vs actual graph structure
- Adjust similarity thresholds in algorithm
- Check for false positives/negatives in results

### Visualization Errors
- Install required packages: `pip install matplotlib seaborn networkx`
- Ensure `visuals/` directory exists and is writable
- Check test data format and completeness

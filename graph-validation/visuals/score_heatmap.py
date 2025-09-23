import matplotlib.pyplot as plt
import seaborn as sns
import json

def plot_score_heatmap():
    data = {
        "Similarity": 0.72,
        "Path Discovery": 0.64,
        "Recommendations": 0.61,
        "Edge Weight": 0.85
    }
    
    labels = list(data.keys())
    scores = list(data.values())
    
    sns.heatmap([scores], annot=True, xticklabels=labels, yticklabels=["Accuracy"], cmap="YlOrRd", vmin=0, vmax=1)
    plt.title("Graph Validation Heatmap")
    plt.savefig("visuals/validation_heatmap.png")
    plt.show()

if __name__ == "__main__":
    plot_score_heatmap()

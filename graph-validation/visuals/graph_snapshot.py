import json
import networkx as nx
import matplotlib.pyplot as plt

def draw_graph_from_memories(file="test_data/memories.json"):
    with open(file) as f:
        data = json.load(f)
    
    G = nx.Graph()
    
    for mem in data:
        G.add_node(mem["memory_id"], label="memory", content=mem["content"])
        for token in mem["expected_tokens"]:
            token_id = f"token:{token}"
            G.add_node(token_id, label="token")
            G.add_edge(mem["memory_id"], token_id)
    
    pos = nx.spring_layout(G)
    labels = {n: n.split(":")[1] for n in G.nodes()}
    nx.draw(G, pos, labels=labels, with_labels=True, node_color='lightblue', node_size=1500)
    plt.title("Memory-Token Relationship Graph")
    plt.savefig("visuals/memory_token_graph.png")
    plt.show()

if __name__ == "__main__":
    draw_graph_from_memories()

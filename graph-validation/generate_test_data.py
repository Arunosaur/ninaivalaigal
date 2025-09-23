import json
import psycopg2

def fetch_sample_data():
    conn = psycopg2.connect("dbname=your_db user=your_user password=your_pw host=localhost")
    cur = conn.cursor()
    
    # Sample 5 memories and their tokens
    cur.execute("""
        SELECT m.memory_id, m.content, t.token_id, t.value
        FROM memory m
        JOIN memory_token mt ON m.memory_id = mt.memory_id
        JOIN token t ON t.token_id = mt.token_id
        LIMIT 5
    """)
    
    rows = cur.fetchall()
    memories = {}
    for mem_id, content, token_id, token_value in rows:
        if mem_id not in memories:
            memories[mem_id] = {
                "memory_id": mem_id,
                "content": content,
                "expected_similar_ids": [],  # Fill manually or via graph traversal
                "expected_tokens": []
            }
        memories[mem_id]["expected_tokens"].append(token_value)
    
    with open("test_data/memories.json", "w") as f:
        json.dump(list(memories.values()), f, indent=2)
    
    print("✅ Sample data written to test_data/memories.json")

if __name__ == "__main__":
    fetch_sample_data()

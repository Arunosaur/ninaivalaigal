CREATE TABLE IF NOT EXISTS memory_records (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[],
    created_at TIMESTAMP DEFAULT now()
);
-- pgvector basic vector search lab
-- Queries are intentionally kept on a single line for easy execution in psql.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS items (id bigserial PRIMARY KEY, name text, embedding vector(3));
INSERT INTO items (name, embedding) VALUES ('apple', '[1,0,0]');
INSERT INTO items (name, embedding) VALUES ('banana', '[0.9,0.1,0]');
INSERT INTO items (name, embedding) VALUES ('car', '[0,0,1]');
INSERT INTO items (name, embedding) VALUES ('big_apple', '[10,0,0]');
SELECT * FROM items;
-- <-> : L2 (Euclidean) distance
SELECT name, embedding <-> '[1,0,0]' AS l2_distance FROM items ORDER BY embedding <-> '[1,0,0]';
-- <=> : cosine distance = 1 - cosine similarity
SELECT name, embedding <=> '[1,0,0]' AS cosine_distance FROM items ORDER BY embedding <=> '[1,0,0]';
-- Top-2 vector similarity search
SELECT name, embedding, embedding <=> '[1,0,0]' AS distance FROM items ORDER BY embedding <=> '[1,0,0]' LIMIT 2;
-- Threshold search example
SELECT name, embedding <=> '[1,0,0]' AS distance FROM items WHERE embedding <=> '[1,0,0]' < 0.1 ORDER BY embedding <=> '[1,0,0]';

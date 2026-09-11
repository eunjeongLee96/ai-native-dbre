# pgvector Lab

PostgreSQL + pgvector hands-on lab for vector storage, similarity search, indexing, and performance experiments.

## Current Progress

- [x] PostgreSQL + pgvector lab environment
- [x] Enable `vector` extension
- [x] Create a table with a `vector` column
- [x] Store sample vectors
- [x] Run basic vector similarity search
- [x] Compare L2 distance and cosine distance
- [ ] Create and test HNSW index
- [ ] Create and test IVFFlat index
- [ ] Compare search performance with and without indexes

## 1. Enable pgvector

```sql
CREATE EXTENSION vector;
```

Verify:

```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```

Lab environment confirmed with pgvector `0.8.6`.

## 2. Create a Vector Table

```sql
CREATE TABLE items (id bigserial PRIMARY KEY, name text, embedding vector(3));
```

`vector(3)` means that each row stores a 3-dimensional vector.

## 3. Insert Sample Vectors

```sql
INSERT INTO items (name, embedding) VALUES ('apple', '[1,0,0]');
INSERT INTO items (name, embedding) VALUES ('banana', '[0.9,0.1,0]');
INSERT INTO items (name, embedding) VALUES ('car', '[0,0,1]');
INSERT INTO items (name, embedding) VALUES ('big_apple', '[10,0,0]');
```

The `big_apple` row is intentionally much larger than `apple` while pointing in the same direction. This makes the difference between L2 distance and cosine distance easy to see.

## 4. L2 Distance

pgvector operator:

```text
<-> = L2 (Euclidean) distance
```

```sql
SELECT name, embedding <-> '[1,0,0]' AS l2_distance FROM items ORDER BY embedding <-> '[1,0,0]';
```

L2 distance measures the actual geometric distance between vectors, so vector magnitude affects the result.

For example, `[1,0,0]` and `[10,0,0]` point in the same direction but have an L2 distance of `9`.

## 5. Cosine Distance

pgvector operator:

```text
<=> = cosine distance
```

```sql
SELECT name, embedding <=> '[1,0,0]' AS cosine_distance FROM items ORDER BY embedding <=> '[1,0,0]';
```

Cosine distance focuses on direction rather than magnitude.

```text
cosine distance = 1 - cosine similarity
```

Therefore:

- cosine distance `0` = same direction
- cosine distance `1` = perpendicular
- cosine distance `2` = opposite direction

`[1,0,0]` and `[10,0,0]` have cosine distance `0` because they point in exactly the same direction.

## 6. Basic Vector Similarity Search

A simple Top-K vector search is not a separate special SQL command. It is:

1. calculate distance from the query vector
2. sort by distance
3. return only the nearest K rows

```sql
SELECT name, embedding, embedding <=> '[1,0,0]' AS distance FROM items ORDER BY embedding <=> '[1,0,0]' LIMIT 2;
```

Core pattern:

```sql
ORDER BY embedding <=> query_vector LIMIT K
```

This is a basic **Top-K Vector Similarity Search**.

A threshold search is different. It filters by a maximum acceptable distance:

```sql
SELECT name, embedding <=> '[1,0,0]' AS distance FROM items WHERE embedding <=> '[1,0,0]' < 0.1 ORDER BY embedding <=> '[1,0,0]';
```

## Key Takeaways

### L2 vs Cosine

| Metric | pgvector operator | Main idea |
|---|---|---|
| L2 distance | `<->` | How far apart are the vectors? |
| Cosine distance | `<=>` | How different are their directions? |

### Similarity Search

Vector similarity search usually means finding the nearest vectors rather than requiring an exact match.

```text
Query Vector
    ↓
Distance Calculation
    ↓
ORDER BY distance
    ↓
LIMIT K
    ↓
Top-K nearest vectors
```

This pattern will later be used in RAG to retrieve the most relevant document chunks for a question.

## Next

HNSW index creation and search.

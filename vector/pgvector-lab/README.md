# pgvector Lab

PostgreSQL + pgvector hands-on lab for vector storage, similarity search, indexing, and performance experiments.

## Current Progress

- [x] PostgreSQL + pgvector lab environment
- [x] Enable `vector` extension
- [x] Create a table with a `vector` column
- [x] Store sample vectors
- [x] Run basic vector similarity search
- [x] Compare L2 distance and cosine distance
- [x] Create and test HNSW index
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

## 7. HNSW Index

HNSW is a special index designed for nearest-neighbor search over vector data.

> **HNSW = a vector-column ANN index.**
>
> **B-tree is mainly for equality/range search, while HNSW is for nearest-neighbor search.**

### Why is a separate vector index needed?

A normal PostgreSQL B-tree index is well suited to queries such as:

```sql
WHERE id = 100
WHERE created_at > ...
```

Vector search asks a different question:

```text
"Find the 10 vectors nearest to this query vector."
```

Without a vector index, PostgreSQL can calculate the distance between the query vector and stored vectors, sort the results, and return the Top-K. As the number of vectors grows, comparing against many rows becomes expensive.

HNSW provides an index structure designed specifically for this nearest-neighbor problem.

### HNSW

HNSW stands for:

```text
Hierarchical Navigable Small World
```

Conceptually, it organizes vectors as a graph-like structure in which nearby vectors are connected. During a search, it navigates promising neighbors instead of exhaustively comparing every stored vector.

```text
Full comparison
Query -> compare many/all vectors -> sort -> Top-K

HNSW
Query -> navigate promising neighbors -> Top-K candidates
```

HNSW is an **ANN (Approximate Nearest Neighbor)** index. The goal is to obtain very good nearest-neighbor results much faster at large scale, with a trade-off between search speed and recall.

### HNSW is not limited to Cosine and L2

HNSW is the **index structure**, while the operator class defines **how vector closeness is measured**. Cosine and L2 are only the two metrics used first in this lab.

For pgvector's `vector` type, HNSW supports these main distance/operator classes:

| Metric | Operator | HNSW operator class |
|---|---|---|
| L2 (Euclidean) distance | `<->` | `vector_l2_ops` |
| Inner Product | `<#>` | `vector_ip_ops` |
| Cosine distance | `<=>` | `vector_cosine_ops` |
| L1 (Manhattan) distance | `<+>` | `vector_l1_ops` |

Mental model:

```text
HNSW = How to search nearest neighbors efficiently

        + L2              -> vector_l2_ops
        + Cosine          -> vector_cosine_ops
        + Inner Product   -> vector_ip_ops
        + L1              -> vector_l1_ops
```

The lab focuses on **Cosine and L2** rather than expanding into every metric.

### Create Cosine and L2 HNSW indexes

Cosine:

```sql
CREATE INDEX item_embedding_hnsw_cosine_idx ON items USING hnsw (embedding vector_cosine_ops);
```

L2:

```sql
CREATE INDEX item_embedding_hnsw_l2_idx ON items USING hnsw (embedding vector_l2_ops);
```

### Execution plan experiment

The current `items` table has only 4 rows. With normal planner settings, PostgreSQL correctly judged that scanning four rows was cheaper than traversing an index.

Cosine query:

```sql
EXPLAIN SELECT name, embedding <=> '[1,0,0]' AS distance FROM items ORDER BY embedding <=> '[1,0,0]' LIMIT 2;
```

Observed plan:

```text
Limit
  -> Sort
       Sort Key: (embedding <=> '[1,0,0]'::vector)
       -> Seq Scan on items
```

This does **not** mean the HNSW index is invalid. It means the PostgreSQL planner estimated that a sequential scan was cheaper for a four-row table.

For diagnostic purposes only, sequential scans were disabled temporarily:

```sql
SET enable_seqscan = off;
```

The same Cosine query then used the Cosine HNSW index:

```text
Limit
  -> Index Scan using item_embedding_hnsw_cosine_idx on items
       Order By: (embedding <=> '[1,0,0]'::vector)
```

The L2 query also selected the matching L2 HNSW index:

```sql
EXPLAIN SELECT name, embedding <-> '[1,0,0]' AS distance FROM items ORDER BY embedding <-> '[1,0,0]' LIMIT 2;
```

Observed plan:

```text
Limit
  -> Index Scan using item_embedding_hnsw_l2_idx on items
       Order By: (embedding <-> '[1,0,0]'::vector)
```

This confirms the relationship between the distance operator and the HNSW operator class:

```text
<=> Cosine -> item_embedding_hnsw_cosine_idx
<-> L2     -> item_embedding_hnsw_l2_idx
```

After the diagnostic experiment, restore the normal planner setting:

```sql
SET enable_seqscan = on;
```

`enable_seqscan = off` is **not a performance tuning technique**. It was used here only to verify that PostgreSQL could use the newly created HNSW indexes. A proper performance comparison will use a larger dataset and allow the planner to choose the access path normally.

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

### Index mental model

```text
B-tree -> equality / range search
HNSW   -> nearest-neighbor vector search
```

### Planner lesson from the lab

```text
Index exists != PostgreSQL must use the index

Small table
-> Seq Scan can be cheaper

Large vector dataset + Top-K search
-> Vector index becomes useful
```

This pattern will later be used in RAG to retrieve the most relevant document chunks for a question.

## Next

Create and test an IVFFlat index, then compare vector-search performance with and without indexes on a larger dataset.

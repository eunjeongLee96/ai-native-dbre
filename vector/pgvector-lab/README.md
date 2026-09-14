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
- [x] Create and test IVFFlat index
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

A Top-K vector search calculates distance from the query vector, orders by distance, and returns the nearest K rows.

```sql
SELECT name, embedding, embedding <=> '[1,0,0]' AS distance FROM items ORDER BY embedding <=> '[1,0,0]' LIMIT 2;
```

Core pattern:

```sql
ORDER BY embedding <=> query_vector LIMIT K
```

A threshold search filters by a maximum acceptable distance:

```sql
SELECT name, embedding <=> '[1,0,0]' AS distance FROM items WHERE embedding <=> '[1,0,0]' < 0.1 ORDER BY embedding <=> '[1,0,0]';
```

## 7. HNSW Index

HNSW is an ANN index for nearest-neighbor search over vector data. HNSW stands for `Hierarchical Navigable Small World` and organizes vectors using graph-like neighbor connections, navigating promising neighbors during search rather than exhaustively comparing all vectors.

```text
Query -> navigate promising neighbors -> Top-K candidates
```

### Distance operator classes

HNSW is the index structure, while the operator class defines how vector closeness is measured.

| Metric | Operator | HNSW operator class |
|---|---|---|
| L2 (Euclidean) distance | `<->` | `vector_l2_ops` |
| Inner Product | `<#>` | `vector_ip_ops` |
| Cosine distance | `<=>` | `vector_cosine_ops` |
| L1 (Manhattan) distance | `<+>` | `vector_l1_ops` |

This lab focuses on Cosine and L2.

### Create Cosine and L2 HNSW indexes

```sql
CREATE INDEX item_embedding_hnsw_cosine_idx ON items USING hnsw (embedding vector_cosine_ops);
CREATE INDEX item_embedding_hnsw_l2_idx ON items USING hnsw (embedding vector_l2_ops);
```

### Execution plan verification

The sample dataset is intentionally minimal, so `enable_seqscan = off` was used only to verify index access paths. Performance benchmarking is handled separately with a larger dataset.

Cosine:

```text
Index Scan using item_embedding_hnsw_cosine_idx
Order By: (embedding <=> '[1,0,0]'::vector)
```

L2:

```text
Index Scan using item_embedding_hnsw_l2_idx
Order By: (embedding <-> '[1,0,0]'::vector)
```

The diagnostic setting was restored after verification:

```sql
SET enable_seqscan = on;
```

## 8. IVFFlat Index

IVFFlat is also an ANN vector index, but uses a partitioned search strategy rather than HNSW's graph navigation.

```text
All vectors
    ↓
Divide into lists
    ↓
Query Vector
    ↓
Probe selected lists
    ↓
Top-K
```

### `lists` and `probes`

```text
lists  = number of vector partitions
probes = number of partitions searched per query
```

Fewer probes reduce search work; more probes generally improve recall at additional search cost.

### Create Cosine and L2 IVFFlat indexes

```sql
CREATE INDEX item_embedding_ivfflat_cosine_idx ON items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 2);
CREATE INDEX item_embedding_ivfflat_l2_idx ON items USING ivfflat (embedding vector_l2_ops) WITH (lists = 2);
```

Search configuration used in the lab:

```sql
SET ivfflat.probes = 1;
```

### Execution plan verification

As with HNSW, `enable_seqscan = off` was used only to verify the expected index access paths on the minimal sample dataset.

L2:

```text
Index Scan using item_embedding_ivfflat_l2_idx
Order By: (embedding <-> '[1,0,0]'::vector)
```

Cosine:

```text
Index Scan using item_embedding_ivfflat_cosine_idx
Order By: (embedding <=> '[1,0,0]'::vector)
```

Operator-to-index mapping verified in the lab:

```text
<-> L2     -> item_embedding_ivfflat_l2_idx
<=> Cosine -> item_embedding_ivfflat_cosine_idx
```

### HNSW vs IVFFlat

| | HNSW | IVFFlat |
|---|---|---|
| Search strategy | Neighbor graph traversal | Probe selected vector partitions |
| Structure | Graph-like | Lists / clusters |
| ANN | Yes | Yes |
| Main search tuning | `ef_search` | `probes` |
| Main build/layout tuning | graph parameters | `lists` |

The current dataset is used for functional verification only. Performance benchmarking will use a larger vector dataset.

## Key Takeaways

```text
Vector Search
    ↓
Distance metric
    ↓
Top-K nearest neighbors
    ↓
ANN index
       ├─ HNSW    : neighbor graph traversal
       └─ IVFFlat : partition-based search
```

This pattern will later be used in RAG to retrieve relevant document chunks for a question.

## Next

Generate a larger vector dataset and benchmark no-index, HNSW, and IVFFlat search performance.

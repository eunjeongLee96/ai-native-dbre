# pgvector Lab

PostgreSQL + pgvector hands-on lab for vector storage, similarity search, indexing, and performance experiments.

## Phase 1 Status — Completed

Phase 1 is complete. The lab covered vector storage, L2/Cosine similarity search, HNSW and IVFFlat ANN indexes, and a 100,000-row execution-time benchmark.

## Current Progress

- [x] PostgreSQL + pgvector lab environment
- [x] Enable `vector` extension
- [x] Create a table with a `vector` column
- [x] Store sample vectors
- [x] Run basic vector similarity search
- [x] Compare L2 distance and cosine distance
- [x] Create and test HNSW index
- [x] Create and test IVFFlat index
- [x] Compare search performance with and without indexes

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

```text
<-> = L2 (Euclidean) distance
```

```sql
SELECT name, embedding <-> '[1,0,0]' AS l2_distance FROM items ORDER BY embedding <-> '[1,0,0]';
```

L2 distance measures geometric distance, so vector magnitude affects the result. `[1,0,0]` and `[10,0,0]` have an L2 distance of `9`.

## 5. Cosine Distance

```text
<=> = cosine distance
```

```sql
SELECT name, embedding <=> '[1,0,0]' AS cosine_distance FROM items ORDER BY embedding <=> '[1,0,0]';
```

```text
cosine distance = 1 - cosine similarity
```

- cosine distance `0` = same direction
- cosine distance `1` = perpendicular
- cosine distance `2` = opposite direction

`[1,0,0]` and `[10,0,0]` have cosine distance `0` because they point in the same direction.

## 6. Basic Vector Similarity Search

A Top-K vector search calculates distance, orders by distance, and returns the nearest K rows.

```sql
SELECT name, embedding, embedding <=> '[1,0,0]' AS distance FROM items ORDER BY embedding <=> '[1,0,0]' LIMIT 2;
```

Core pattern:

```sql
ORDER BY embedding <=> query_vector LIMIT K
```

Threshold search:

```sql
SELECT name, embedding <=> '[1,0,0]' AS distance FROM items WHERE embedding <=> '[1,0,0]' < 0.1 ORDER BY embedding <=> '[1,0,0]';
```

## 7. HNSW Index

HNSW is an ANN index for nearest-neighbor search over vector data. It uses graph-like neighbor connections and navigates promising candidates during search.

### Distance operator classes

| Metric | Operator | HNSW operator class |
|---|---|---|
| L2 | `<->` | `vector_l2_ops` |
| Inner Product | `<#>` | `vector_ip_ops` |
| Cosine | `<=>` | `vector_cosine_ops` |
| L1 | `<+>` | `vector_l1_ops` |

This lab focuses on Cosine and L2.

```sql
CREATE INDEX item_embedding_hnsw_cosine_idx ON items USING hnsw (embedding vector_cosine_ops);
CREATE INDEX item_embedding_hnsw_l2_idx ON items USING hnsw (embedding vector_l2_ops);
```

The four-row sample was too small for meaningful performance comparison, so index access paths were verified functionally before moving to the larger benchmark.

Observed access paths:

```text
Index Scan using item_embedding_hnsw_cosine_idx
Order By: (embedding <=> '[1,0,0]'::vector)
```

```text
Index Scan using item_embedding_hnsw_l2_idx
Order By: (embedding <-> '[1,0,0]'::vector)
```

## 8. IVFFlat Index

IVFFlat is also an ANN vector index, but uses partition-based search rather than graph traversal.

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

```sql
CREATE INDEX item_embedding_ivfflat_cosine_idx ON items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 2);
CREATE INDEX item_embedding_ivfflat_l2_idx ON items USING ivfflat (embedding vector_l2_ops) WITH (lists = 2);
```

```sql
SET ivfflat.probes = 1;
```

`ivfflat.probes` controls how many IVFFlat lists are searched for each query.

```text
lists = 2, probes = 1
-> divide the vector space into 2 lists
-> search 1 list per query
```

### HNSW vs IVFFlat

| | HNSW | IVFFlat |
|---|---|---|
| Search strategy | Neighbor graph traversal | Probe selected vector partitions |
| Structure | Graph-like | Lists / clusters |
| ANN | Yes | Yes |
| Main search tuning | `ef_search` | `probes` |
| Main build/layout tuning | graph parameters | `lists` |

## 9. Performance Benchmark — 100,000 Vectors

After the four-row functional tests, a separate benchmark table was created with 100,000 random vectors. The performance test was then run under normal PostgreSQL planner behavior without forcing an access path.

### Create benchmark dataset

```sql
CREATE TABLE items_bench (id bigserial PRIMARY KEY, embedding vector(3));
```

```sql
INSERT INTO items_bench (embedding) SELECT ARRAY[random(), random(), random()]::vector FROM generate_series(1,100000);
```

```sql
SELECT count(*) FROM items_bench;
```

Expected row count:

```text
100000
```

### Benchmark flow

```text
100,000 rows
      ↓
No Index measurement
      ↓
Create HNSW → measurement
      ↓
Drop HNSW
      ↓
Create IVFFlat → measurement
```

The same Cosine Top-K query was used for every measurement:

```sql
EXPLAIN ANALYZE SELECT id, embedding <=> '[0.5,0.5,0.5]' AS distance FROM items_bench ORDER BY embedding <=> '[0.5,0.5,0.5]' LIMIT 10;
```

Benchmark conditions:

- Dataset: 100,000 random `vector(3)` rows
- Distance: Cosine (`<=>`)
- Query vector: `[0.5,0.5,0.5]`
- Top-K: 10
- PostgreSQL planner: normal behavior, no forced scan path
- IVFFlat benchmark: `lists = 100`, `probes = 10`

### No Index

Observed execution path:

```text
Seq Scan on items_bench (100,000 rows)
    ↓
top-N heapsort
    ↓
LIMIT 10
```

Execution Time:

```text
31.350 ms
```

### HNSW

```sql
CREATE INDEX idx01_items_bench_hnsw_cosine ON items_bench USING hnsw (embedding vector_cosine_ops);
```

Observed execution path:

```text
Index Scan using idx01_items_bench_hnsw_cosine
    ↓
LIMIT 10
```

Execution Time:

```text
2.244 ms
```

### IVFFlat

After the HNSW measurement, the HNSW index was removed before testing IVFFlat.

```sql
DROP INDEX idx01_items_bench_hnsw_cosine;
```

```sql
CREATE INDEX idx02_items_bench_ivfflat_cosine ON items_bench USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

```sql
SET ivfflat.probes = 10;
```

Observed execution path:

```text
Index Scan using idx02_items_bench_ivfflat_cosine
    ↓
LIMIT 10
```

Execution Time:

```text
5.325 ms
```

### Results

| Search method | Access path | Execution Time | Relative to No Index |
|---|---|---:|---:|
| No Index | Seq Scan + top-N heapsort | 31.350 ms | 1.0x |
| HNSW | HNSW Index Scan | 2.244 ms | ~14.0x faster |
| IVFFlat (`lists=100`, `probes=10`) | IVFFlat Index Scan | 5.325 ms | ~5.9x faster |

Under this benchmark configuration, both ANN indexes reduced Top-K search time substantially compared with the no-index scan. HNSW was the fastest in this specific 100,000-row, 3-dimensional experiment. These timings are experiment-specific and should not be generalized across different vector dimensions, dataset sizes, hardware, or ANN tuning parameters.

## Key Takeaways

```text
PostgreSQL + pgvector
        ↓
Store vector data
        ↓
Choose distance metric
   ├─ L2
   └─ Cosine
        ↓
Top-K similarity search
        ↓
ANN index for scale
   ├─ HNSW
   └─ IVFFlat
        ↓
Verify with execution plans and benchmark
```

Phase 1 demonstrated how PostgreSQL can store vectors, perform similarity search, and use ANN indexes to accelerate Top-K retrieval. This becomes the retrieval foundation for Phase 2 RAG.

## Next — Phase 2: RAG

Use pgvector as the retrieval layer for a small RAG pipeline based on DB operations documents/runbooks.

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

### HNSW search idea

HNSW stands for `Hierarchical Navigable Small World`. Conceptually, it organizes vectors as a graph-like structure in which nearby vectors are connected. During a search, it navigates promising neighbors instead of exhaustively comparing every stored vector.

```text
Full comparison
Query -> compare many/all vectors -> sort -> Top-K

HNSW
Query -> navigate promising neighbors -> Top-K candidates
```

HNSW is an **ANN (Approximate Nearest Neighbor)** index.

### HNSW is not limited to Cosine and L2

HNSW is the **index structure**, while the operator class defines **how vector closeness is measured**.

| Metric | Operator | HNSW operator class |
|---|---|---|
| L2 (Euclidean) distance | `<->` | `vector_l2_ops` |
| Inner Product | `<#>` | `vector_ip_ops` |
| Cosine distance | `<=>` | `vector_cosine_ops` |
| L1 (Manhattan) distance | `<+>` | `vector_l1_ops` |

The lab focuses on **Cosine and L2** rather than expanding into every metric.

### Create Cosine and L2 HNSW indexes

```sql
CREATE INDEX item_embedding_hnsw_cosine_idx ON items USING hnsw (embedding vector_cosine_ops);
CREATE INDEX item_embedding_hnsw_l2_idx ON items USING hnsw (embedding vector_l2_ops);
```

### HNSW execution plan experiment

With only four rows, PostgreSQL chose `Seq Scan -> Sort -> Limit`. For diagnostic purposes, sequential scans were temporarily disabled with `SET enable_seqscan = off;`.

Cosine then used:

```text
Index Scan using item_embedding_hnsw_cosine_idx
Order By: (embedding <=> '[1,0,0]'::vector)
```

L2 used:

```text
Index Scan using item_embedding_hnsw_l2_idx
Order By: (embedding <-> '[1,0,0]'::vector)
```

After the experiment:

```sql
SET enable_seqscan = on;
```

`enable_seqscan = off` is used here only as a diagnostic technique, not as performance tuning.

## 8. IVFFlat Index

IVFFlat is also an **ANN (Approximate Nearest Neighbor)** vector index, but its search strategy is different from HNSW.

> **HNSW navigates connections between nearby vectors.**
>
> **IVFFlat divides the vector space into lists and searches only selected lists.**

Conceptually:

```text
All vectors
    ↓
Divide into lists (groups)
    ↓
Query Vector
    ↓
Choose nearby list(s)
    ↓
Compare vectors inside selected list(s)
    ↓
Top-K
```

### `lists` and `probes`

Two important IVFFlat settings are:

```text
lists  = how many groups the vector space is divided into
probes = how many of those groups are searched for a query
```

Searching fewer lists can be faster but can miss relevant neighbors. Searching more lists can improve recall but requires more work.

For this small lab, the indexes were created with two lists:

```sql
CREATE INDEX item_embedding_ivfflat_cosine_idx ON items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 2);
CREATE INDEX item_embedding_ivfflat_l2_idx ON items USING ivfflat (embedding vector_l2_ops) WITH (lists = 2);
```

The search was configured to probe one list:

```sql
SET ivfflat.probes = 1;
```

### IVFFlat execution plan experiment

As with HNSW, the four-row table was too small for PostgreSQL to prefer an index under normal planner settings.

Normal plan:

```text
Limit
  -> Sort
       -> Seq Scan on items
```

For diagnostic verification:

```sql
SET enable_seqscan = off;
```

L2 query:

```sql
EXPLAIN SELECT name, embedding <-> '[1,0,0]' AS distance FROM items ORDER BY embedding <-> '[1,0,0]' LIMIT 2;
```

Observed plan:

```text
Limit
  -> Index Scan using item_embedding_ivfflat_l2_idx on items
       Order By: (embedding <-> '[1,0,0]'::vector)
```

Cosine query:

```sql
EXPLAIN SELECT name, embedding <=> '[1,0,0]' AS distance FROM items ORDER BY embedding <=> '[1,0,0]' LIMIT 2;
```

Observed plan:

```text
Limit
  -> Index Scan using item_embedding_ivfflat_cosine_idx on items
       Order By: (embedding <=> '[1,0,0]'::vector)
```

This confirms that the distance operator is matched to the corresponding IVFFlat operator class/index:

```text
<-> L2     -> item_embedding_ivfflat_l2_idx
<=> Cosine -> item_embedding_ivfflat_cosine_idx
```

Restore the normal planner setting after the diagnostic experiment:

```sql
SET enable_seqscan = on;
```

### HNSW vs IVFFlat mental model

| | HNSW | IVFFlat |
|---|---|---|
| Search idea | Navigate nearby-vector connections | Search selected vector groups |
| Structure | Graph-like | Lists / clusters |
| ANN | Yes | Yes |
| Main search tuning | `ef_search` | `probes` |
| Main build/layout tuning | graph parameters | `lists` |

The current four-row dataset is enough to verify index creation and execution-plan compatibility, but it is **not sufficient for a meaningful performance comparison**.

## Key Takeaways

```text
Vector Search
    ↓
Distance metric
    ↓
Top-K nearest neighbors
    ↓
Vector index for scale
       ├─ HNSW    : navigate neighbor connections
       └─ IVFFlat : search selected vector groups
```

And from the PostgreSQL planner perspective:

```text
Index exists != PostgreSQL must use the index

Small table
-> Seq Scan can be cheaper

Large vector dataset + Top-K search
-> Vector indexes become useful
```

This pattern will later be used in RAG to retrieve the most relevant document chunks for a question.

## Next

Generate a larger vector dataset and compare search performance with no vector index, HNSW, and IVFFlat under normal PostgreSQL planner behavior.

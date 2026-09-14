# pgvector Lab

PostgreSQL + pgvector를 이용한 벡터 저장, 유사도 검색, 인덱스 및 검색 성능 실습

## Phase 1 상태 — 완료

PostgreSQL에 벡터 데이터 저장 → L2/Cosine 유사도 검색 → HNSW/IVFFlat ANN 인덱스 적용 → 100,000건 벡터 데이터 기준 검색 성능 비교 수행함.

## 진행 항목

- [x] PostgreSQL + pgvector 실습 환경 구성
- [x] `vector` Extension 활성화
- [x] `vector` 컬럼을 가진 테이블 생성
- [x] 샘플 벡터 데이터 저장
- [x] 기본 Vector Similarity Search 실행
- [x] L2 Distance와 Cosine Distance 비교
- [x] HNSW 인덱스 생성 및 검색
- [x] IVFFlat 인덱스 생성 및 검색
- [x] 인덱스 유무에 따른 검색 성능 비교

## 1. pgvector 활성화

```sql
CREATE EXTENSION vector;
```

설치 확인:

```sql
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
```

실습 환경 기준 pgvector `0.8.6` 설치 확인함.

## 2. Vector 테이블 생성

```sql
CREATE TABLE items (id bigserial PRIMARY KEY, name text, embedding vector(3));
```

`vector(3)` = 각 행에 3차원 벡터를 저장한다는 의미.

## 3. 샘플 Vector 데이터 저장

```sql
INSERT INTO items (name, embedding) VALUES ('apple', '[1,0,0]');
INSERT INTO items (name, embedding) VALUES ('banana', '[0.9,0.1,0]');
INSERT INTO items (name, embedding) VALUES ('car', '[0,0,1]');
INSERT INTO items (name, embedding) VALUES ('big_apple', '[10,0,0]');
```

`big_apple`은 `apple`과 같은 방향을 가리키지만 벡터 크기는 의도적으로 크게 설정함.
L2 Distance와 Cosine Distance가 벡터 크기를 다르게 취급하는 것을 확인하기 위한 데이터임.

## 4. L2 Distance

```text
<-> = L2 (Euclidean) Distance
```

```sql
SELECT name, embedding <-> '[1,0,0]' AS l2_distance FROM items ORDER BY embedding <-> '[1,0,0]';
```

L2 Distance는 벡터 사이의 실제 기하학적 거리를 측정함.
따라서 벡터의 방향뿐 아니라 **벡터 크기도 거리 계산 결과에 영향을 줌.**
`[1,0,0]`과 `[10,0,0]`은 같은 방향이지만 크기가 다르므로 L2 Distance = `9`가 됨.

## 5. Cosine Distance

```text
<=> = Cosine Distance
```

```sql
SELECT name, embedding <=> '[1,0,0]' AS cosine_distance FROM items ORDER BY embedding <=> '[1,0,0]';
```

```text
Cosine Distance = 1 - Cosine Similarity
```

- Cosine Distance `0` = 같은 방향을 의미함
- Cosine Distance `1` = 서로 직각인 방향을 의미함
- Cosine Distance `2` = 서로 반대 방향을 의미함

Cosine Distance는 벡터의 크기보다 방향의 유사성을 비교함.
따라서 `[1,0,0]`과 `[10,0,0]`은 크기는 다르지만 같은 방향이므로 Cosine Distance = `0`이 됨.

## 6. 기본 Vector Similarity Search

Top-K 벡터 검색은 Query Vector와 각 벡터 사이의 거리를 계산한 뒤, 가까운 순서대로 정렬하여 상위 K개를 반환함.

```sql
SELECT name, embedding, embedding <=> '[1,0,0]' AS distance FROM items ORDER BY embedding <=> '[1,0,0]' LIMIT 2;
```

핵심 패턴:

```sql
ORDER BY embedding <=> query_vector LIMIT K
```

즉, Query Vector와 가장 가까운 벡터 K개를 찾는 방식임.
특정 거리 이하의 데이터만 검색하는 조건도 적용 가능함.

```sql
SELECT name, embedding <=> '[1,0,0]' AS distance FROM items WHERE embedding <=> '[1,0,0]' < 0.1 ORDER BY embedding <=> '[1,0,0]';
```

## 7. HNSW 인덱스

HNSW는 벡터 데이터에서 가까운 이웃을 빠르게 찾기 위한 ANN(Approximate Nearest Neighbor) 인덱스임.
벡터들을 그래프 형태의 이웃 관계로 연결해 두고, 검색 시 가능성이 높은 이웃을 따라가며 후보를 탐색함.
전체 벡터를 하나씩 비교하는 방식보다 대용량 Top-K 검색을 빠르게 처리하기 위한 구조임.

### 거리별 Operator Class

| 거리 기준 | Operator | HNSW Operator Class |
|---|---|---|
| L2 | `<->` | `vector_l2_ops` |
| Inner Product | `<#>` | `vector_ip_ops` |
| Cosine | `<=>` | `vector_cosine_ops` |
| L1 | `<+>` | `vector_l1_ops` |

이번 실습에서는 Cosine과 L2 기준으로 HNSW 인덱스 사용을 확인함.

```sql
CREATE INDEX item_embedding_hnsw_cosine_idx ON items USING hnsw (embedding vector_cosine_ops);
CREATE INDEX item_embedding_hnsw_l2_idx ON items USING hnsw (embedding vector_l2_ops);
```

샘플 데이터 4건은 성능 차이를 측정하기에는 너무 적음.
따라서 이 단계에서는 HNSW 인덱스가 실제 검색 경로로 사용되는지만 확인하고, 성능 비교는 100,000건 데이터로 별도 수행함.

확인한 실행 경로:

```text
Index Scan using item_embedding_hnsw_cosine_idx
Order By: (embedding <=> '[1,0,0]'::vector)
```

```text
Index Scan using item_embedding_hnsw_l2_idx
Order By: (embedding <-> '[1,0,0]'::vector)
```

## 8. IVFFlat 인덱스

IVFFlat 역시 가까운 벡터를 빠르게 찾기 위한 ANN 인덱스임.
HNSW가 그래프의 이웃을 따라 탐색한다면, IVFFlat은 벡터 공간을 여러 List로 나눈 뒤 Query와 관련성이 높은 일부 List만 검색함.

```text
전체 Vector
    ↓
여러 List로 분할
    ↓
Query Vector
    ↓
선택된 List 검색
    ↓
Top-K 반환
```

### `lists`와 `probes`

```text
lists  = 벡터 공간을 몇 개의 List로 나눌지 결정함
probes = 한 번의 검색에서 몇 개의 List를 확인할지 결정함
```

```sql
CREATE INDEX item_embedding_ivfflat_cosine_idx ON items USING ivfflat (embedding vector_cosine_ops) WITH (lists = 2);
CREATE INDEX item_embedding_ivfflat_l2_idx ON items USING ivfflat (embedding vector_l2_ops) WITH (lists = 2);
```

```sql
SET ivfflat.probes = 1;
```

예를 들어 `lists = 2`, `probes = 1`이면 벡터 공간을 2개의 List로 나누고, Query마다 그중 1개의 List를 검색함.

### HNSW vs IVFFlat

| | HNSW | IVFFlat |
|---|---|---|
| 검색 방식 | 이웃 그래프를 따라 후보 탐색 | 관련성이 높은 Vector List를 선택해 탐색 |
| 구조 | Graph | Lists / Clusters |
| ANN | Yes | Yes |
| 주요 검색 조정값 | `ef_search` | `probes` |
| 주요 생성/구조 조정값 | Graph 관련 Parameter | `lists` |

## 9. 검색 성능 비교 — 100,000 Vectors

4건의 샘플 데이터로 기능을 확인한 뒤, 100,000개의 랜덤 벡터를 가진 별도 테이블을 생성함.
PostgreSQL Planner의 실행 경로를 강제로 변경하지 않고 일반적인 Planner 동작 상태에서 검색 성능을 측정함.

### 100,000건 테스트 데이터 생성

```sql
CREATE TABLE items_bench (id bigserial PRIMARY KEY, embedding vector(3));
```

```sql
INSERT INTO items_bench (embedding) SELECT ARRAY[random(), random(), random()]::vector FROM generate_series(1,100000);
```

```sql
SELECT count(*) FROM items_bench;
```

예상 Row 수: `100000`

### 실험 순서

```text
100,000 rows
      ↓
No Index 측정
      ↓
HNSW 생성 → 측정
      ↓
HNSW 삭제
      ↓
IVFFlat 생성 → 측정
```

인덱스별 결과를 같은 조건에서 비교하기 위해 모든 테스트에서 동일한 Cosine Top-K Query를 사용함.

```sql
EXPLAIN ANALYZE SELECT id, embedding <=> '[0.5,0.5,0.5]' AS distance FROM items_bench ORDER BY embedding <=> '[0.5,0.5,0.5]' LIMIT 10;
```

실험 조건:

- 데이터: 100,000건 랜덤 `vector(3)`
- 거리 기준: Cosine Distance (`<=>`)
- Query Vector: `[0.5,0.5,0.5]`
- Top-K: 10
- IVFFlat: `lists = 100`, `probes = 10`

### No Index

```text
Seq Scan on items_bench (100,000 rows)
    ↓
top-N heapsort
    ↓
LIMIT 10
Execution Time: 31.350 ms
```

인덱스가 없으므로 100,000건을 Seq Scan한 뒤 거리 기준으로 정렬하여 상위 10건을 찾음.

![No Index benchmark execution plan](images/benchmark-no-index.png)

### HNSW

```sql
CREATE INDEX idx01_items_bench_hnsw_cosine ON items_bench USING hnsw (embedding vector_cosine_ops);
```

```text
Index Scan using idx01_items_bench_hnsw_cosine
    ↓
LIMIT 10
Execution Time: 2.244 ms
```

HNSW Index Scan을 사용하면서 전체 데이터를 순차 검색하지 않고 가까운 후보를 빠르게 탐색함.

![HNSW benchmark execution plan](images/benchmark-hnsw.png)

### IVFFlat

HNSW 측정 후 HNSW 인덱스를 삭제하고 IVFFlat만 존재하는 상태에서 테스트함.

```sql
DROP INDEX idx01_items_bench_hnsw_cosine;
```

```sql
CREATE INDEX idx02_items_bench_ivfflat_cosine ON items_bench USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

```sql
SET ivfflat.probes = 10;
```

```text
Index Scan using idx02_items_bench_ivfflat_cosine
    ↓
LIMIT 10
Execution Time: 5.325 ms
```

100개의 List 중 `probes = 10`으로 설정하여 Query마다 10개의 List를 검색함.

![IVFFlat benchmark execution plan](images/benchmark-ivfflat.png)

### 결과

| 검색 방식 | 실행 경로 | Execution Time | No Index 대비 |
|---|---|---:|---:|
| No Index | Seq Scan + top-N heapsort | 31.350 ms | 1.0x |
| HNSW | HNSW Index Scan | 2.244 ms | 약 14.0배 빠름 |
| IVFFlat (`lists=100`, `probes=10`) | IVFFlat Index Scan | 5.325 ms | 약 5.9배 빠름 |

이번 실험에서는 두 ANN 인덱스 모두 No Index 전체 Scan보다 Top-K 검색 시간을 크게 줄여 줌.
HNSW는 약 2.244 ms로 가장 빠른 결과를 보였고, No Index 대비 약 14배 빠른 결과가 나옴.
IVFFlat 역시 약 5.325 ms로 No Index 대비 약 5.9배 빠른 결과가 나옴.

단, 이 결과는 100,000건·3차원 벡터·현재 실습 환경에서 측정한 결과임.
벡터 차원, 데이터 수, 하드웨어, ANN Parameter에 따라 성능 결과가 달라질 수 있음.

## 핵심 정리

```text
PostgreSQL + pgvector
        ↓
Vector 데이터 저장
        ↓
거리 기준 선택
   ├─ L2
   └─ Cosine
        ↓
Top-K Similarity Search
        ↓
대용량 검색을 위한 ANN Index
   ├─ HNSW
   └─ IVFFlat
        ↓
Execution Plan과 실행 시간으로 검증
```

Phase 1을 통해 PostgreSQL에 벡터를 저장하고, 벡터 사이의 거리를 이용해 유사한 데이터를 검색할 수 있음을 확인함.
또한 데이터가 많아질 경우 HNSW/IVFFlat 같은 ANN 인덱스를 사용하여 Top-K 검색을 빠르게 처리할 수 있음을 직접 확인함.

이 Vector Similarity Search 구조가 **Phase 2 RAG에서 관련 문서를 찾는 Retrieval 기반으로 사용됨.**

## Next — Phase 2: RAG

pgvector를 Retrieval 계층으로 사용하여 DB 운영 문서 / Runbook을 검색하고, 검색 결과를 LLM에 전달하여 답변을 생성하는 작은 RAG Pipeline 구현 예정.

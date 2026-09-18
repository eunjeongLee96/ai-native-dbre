# RAG Lab

DB 운영 문서를 기반으로 질문에 답하는 작은 RAG를 직접 구현하는 실습

## Phase 2 목표

> DB 운영 문서를 검색하고, 검색된 내용을 근거로 답변하는 작은 RAG 직접 구현

## 진행 순서

- [x] 1. RAG 전체 구조 이해
- [x] 2. 테스트용 DB 운영 문서 / Runbook 준비
- [x] 3. 문서를 Chunk로 분리
- [ ] 4. Chunk를 Embedding으로 변환
- [ ] 5. Embedding을 pgvector에 저장
- [ ] 6. 질문을 Embedding으로 변환
- [ ] 7. pgvector에서 관련 문서 검색
- [ ] 8. 검색된 문서를 LLM Context로 전달
- [ ] 9. 질문 → 검색 → 답변 전체 RAG 흐름 구현

---

# 1. RAG 전체 구조 이해

## RAG란?

RAG = **Retrieval-Augmented Generation**

LLM에게 질문만 바로 전달하는 방식이 아니라, 먼저 질문과 관련된 문서를 검색한 뒤 해당 문서를 Context로 함께 전달하여 답변을 생성하는 방식임.

```text
검색(Retrieval)
    ↓
관련 문서를 LLM Context에 추가(Augmented)
    ↓
답변 생성(Generation)
```

즉, **LLM이 원래 알고 있는 지식만 사용하는 것이 아니라 외부 문서를 찾아서 참고하도록 만드는 구조임.**

## 왜 RAG가 필요한가?

LLM은 PostgreSQL에 대한 일반적인 지식은 알고 있지만, 회사 내부 DB 운영 정책이나 Runbook처럼 학습 데이터에 포함되지 않은 정보는 알 수 없음.

예를 들어 다음과 같은 내부 운영 문서가 있다고 가정함.

```text
[Connection Spike 대응 Runbook]

1. active connection이 300을 초과하면 장애 상황으로 판단한다.
2. pg_stat_activity에서 application_name별 connection 수를 확인한다.
3. batch-api connection이 100개 이상이면 배치 서버를 우선 확인한다.
4. DBA 승인 없이 connection을 terminate하지 않는다.
```

사용자 질문 예시:

```text
DB 접속이 갑자기 많이 늘었어. 무엇을 확인해야 해?
```

LLM에게 질문만 전달하면 일반적인 PostgreSQL 지식을 이용해 답할 가능성이 높음.
하지만 관련 Runbook을 먼저 검색해서 함께 전달하면 **회사 내부 운영 기준을 근거로 답변할 수 있게 됨.**

---

## RAG의 사전 준비 과정

DB 운영 문서를 검색에 사용할 수 있도록 미리 다음 과정을 수행함.

```text
DB Runbook
    ↓
Chunk 분리
    ↓
Embedding 생성
    ↓
PostgreSQL + pgvector 저장
```

긴 문서를 검색하기 좋은 작은 단위인 Chunk로 나눈 뒤, 각 Chunk를 Embedding 모델에 전달하여 숫자 벡터로 변환함.

### 이번 Lab의 Chunk 분리 기준

현재 Prototype에서는 PostgreSQL Runbook 3개(`connection-spike.md`, `slow-sql.md`, `lock-wait.md`)를 검색 대상으로 사용함.

처음부터 Token 수를 계산하는 복잡한 Chunking을 적용하지 않고, **Runbook의 Markdown 섹션을 하나의 의미 단위로 보고 Chunk로 분리함.** 문서 구조 자체가 증상, 확인 항목, 가능한 원인, 대응처럼 의미별로 나뉘어 있으므로 첫 RAG 실험에서 검색 결과를 이해하기 쉬움.

예를 들어 `connection-spike.md`는 다음과 같이 분리함.

```text
connection-spike.md
    │
    ├─ Chunk 1 : 증상
    │    └─ Connection 수가 갑자기 증가한 상태와 영향
    │
    ├─ Chunk 2 : 확인 항목
    │    └─ pg_stat_activity, Application별 Connection,
    │       idle in transaction, 최근 변경 사항 확인
    │
    ├─ Chunk 3 : 가능한 원인
    │    └─ Batch, Connection Pool, Retry, 미종료 Transaction
    │
    └─ Chunk 4 : 대응
         └─ 원인 확인 후 조치하며 Session 종료는 DBA 승인 후 수행
```

각 Chunk에는 검색 결과를 추적할 수 있도록 원본 파일과 섹션 정보를 함께 저장할 예정임.

```text
source              section       chunk_no    content
-----------------------------------------------------------------
connection-spike.md 증상          1           평소보다 PostgreSQL...
connection-spike.md 확인 항목     2           현재 Connection 상태를...
connection-spike.md 가능한 원인   3           Batch 작업에서...
connection-spike.md 대응          4           Connection 증가 원인을...
```

`slow-sql.md`와 `lock-wait.md`도 동일하게 **증상 / 확인 항목 / 가능한 원인 / 대응** 섹션을 기준으로 Chunk를 생성함.

> [!IMPORTANT]
> **Chunking의 목적은 문서를 단순히 일정 길이로 자르는 것이 아니라, 사용자 질문과 관련된 내용을 의미 단위로 더 정확하게 검색할 수 있도록 나누는 것임.**

현재 Runbook은 짧고 구조가 명확하므로 섹션 기반 Chunking으로 시작함. 이후 문서가 길어지면 Token 길이, Chunk overlap 등의 방법이 필요한 시점에 확장함.

예시 문장:

```text
Connection Spike 발생 시 pg_stat_activity를 확인한다.
```

Embedding 결과 예시:

```text
[0.132, -0.721, 0.315, 0.028, ...]
```

Embedding은 문장의 의미를 숫자 벡터 형태로 표현한 값임.
의미가 비슷한 문장일수록 벡터 공간에서도 가까운 위치에 있도록 표현하는 것이 핵심임.

PostgreSQL에는 원문 Chunk와 해당 Embedding을 함께 저장함.

```text
content                           embedding
----------------------------------------------------
Connection Spike 발생 시...      [0.132, -0.721, ...]
Slow SQL 발생 시...               [0.812,  0.214, ...]
Lock Wait 발생 시...              [0.091, -0.332, ...]
```

---

## 사용자가 질문했을 때의 흐름

사용자 질문:

```text
DB 접속이 갑자기 많이 늘었어.
```

문서만 Embedding으로 변환하는 것이 아니라 **사용자 질문도 동일한 Embedding 모델을 이용해 벡터로 변환함.**

```text
질문
    ↓
Embedding
    ↓
[0.128, -0.703, 0.301, ...]
```

질문 벡터와 저장된 문서 벡터 사이의 거리를 비교하여 의미적으로 가까운 문서를 검색함.

예:

```sql
SELECT content
FROM rag_documents
ORDER BY embedding <=> query_embedding
LIMIT 3;
```

> [!IMPORTANT]
> **Phase 1에서 실습한 Vector Similarity Search를 실제 문서 검색에 사용하는 지점임.**

```text
질문 Embedding
    ↓
pgvector Similarity Search
    ↓
관련 Chunk Top-K 검색
```

질문과 의미가 가장 가까운 Chunk 몇 개를 찾는 과정이며, 여기까지가 **Retrieval**임.

---

## 검색 결과를 LLM에 전달

pgvector에서 검색된 문서를 사용자 질문과 함께 LLM Context로 전달함.

```text
다음 운영 문서를 참고해서 질문에 답하세요.

[검색된 문서]

Connection Spike 대응 Runbook

1. pg_stat_activity에서 application_name별 connection 수를 확인한다.
2. batch-api connection이 100개 이상이면 배치 서버를 우선 확인한다.
3. DBA 승인 없이 connection을 terminate하지 않는다.

[사용자 질문]

DB 접속이 갑자기 많이 늘었어. 무엇을 확인해야 해?
```

LLM은 검색된 Runbook을 참고하여 답변을 생성함.

답변 예시:

```text
먼저 pg_stat_activity에서 application_name별 connection 수를 확인합니다.
특히 batch-api connection이 100개 이상인지 확인해야 합니다.
Runbook 정책상 DBA 승인 없이 connection을 terminate해서는 안 됩니다.
```

즉, **검색 결과가 LLM의 답변 근거로 사용됨.**

---

## 전체 RAG 구조

```text
               [사전 준비]

DB Runbook
    ↓
Chunk
    ↓
Embedding
    ↓
PostgreSQL + pgvector


               [질문 발생]

사용자 질문
    ↓
Embedding
    ↓
pgvector Similarity Search
    ↓
관련 Chunk Top-K
    ↓
질문 + 검색된 Chunk
    ↓
LLM
    ↓
답변
```

사전 준비 단계에서는 **검색할 문서를 벡터로 만들어 저장**하고, 질문 발생 단계에서는 **질문 벡터와 가까운 문서를 찾아 LLM에게 전달**함.

## Phase 1과 Phase 2의 연결

### Phase 1

```text
Vector
   ↓
pgvector
   ↓
가까운 Vector 검색
```

PostgreSQL에 Vector를 저장하고 Cosine / L2 Distance를 이용하여 가까운 Vector를 검색하는 방법을 실습함.

### Phase 2

```text
문서
   ↓
Embedding
   ↓
pgvector 검색
   ↓
LLM
```

Phase 1에서 직접 실습한 Vector Similarity Search를 **DB 운영 문서 검색에 실제로 활용함.**

따라서 Phase 2의 핵심은 다음 세 요소를 연결하는 것임.

```text
Embedding → pgvector → LLM
```

- Embedding: 문장과 질문의 의미를 Vector로 변환함
- pgvector: 질문 Vector와 가까운 문서 Vector를 검색함
- LLM: 검색된 문서를 Context로 받아 최종 답변을 생성함

## 핵심 이해

> **LLM이 직접 pgvector를 검색하는 것이 아님.**
>
> 애플리케이션이 질문을 Embedding으로 변환함.
> → pgvector에서 관련 문서를 검색함.
> → 검색 결과를 LLM Context로 전달함.
> → LLM이 검색된 문서를 근거로 답변함.

즉, RAG는 단순히 LLM에 문서를 넣는 기능이 아니라 **검색(Retrieval)과 답변 생성(Generation)을 연결한 Pipeline임.**

다음 단계에서는 실제 검색 대상이 될 **DB 운영 Runbook을 작성함.**

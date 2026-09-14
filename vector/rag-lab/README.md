# RAG Lab

DB 운영 문서를 기반으로 질문에 답하는 작은 RAG를 직접 구현하는 실습

## Phase 2 목표

> DB 운영 문서를 기반으로 답변하는 작은 RAG 직접 구현

## 진행 순서

- [x] 1. RAG 전체 구조 이해
- [ ] 2. 테스트용 DB 운영 문서 / Runbook 준비
- [ ] 3. 문서를 Chunk로 분리
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

LLM에게 바로 질문하는 방식이 아니라, 먼저 질문과 관련된 문서를 검색한 뒤 해당 문서를 Context로 함께 전달하여 답변 생성.

```text
검색(Retrieval)
    ↓
관련 문서를 LLM Context에 추가(Augmented)
    ↓
답변 생성(Generation)
```

## 왜 RAG가 필요한가?

LLM은 PostgreSQL에 대한 일반적인 지식은 보유하지만, 회사 내부의 DB 운영 정책이나 Runbook처럼 학습 데이터에 포함되지 않은 정보는 알 수 없음.

예를 들어 다음과 같은 내부 운영 문서가 있다고 가정.

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

LLM이 내부 정책을 근거로 답하도록 하려면 관련 Runbook을 먼저 검색하여 함께 전달할 필요 있음.

---

## RAG의 사전 준비 과정

DB 운영 문서를 바로 pgvector에 저장하는 것이 아니라 다음 과정 수행.

```text
DB Runbook
    ↓
Chunk 분리
    ↓
Embedding 생성
    ↓
PostgreSQL + pgvector 저장
```

예시 문장:

```text
Connection Spike 발생 시 pg_stat_activity를 확인한다.
```

Embedding 모델에 전달하여 문장의 의미를 표현하는 숫자 벡터로 변환.

```text
[0.132, -0.721, 0.315, 0.028, ...]
```

PostgreSQL에는 원문과 Embedding을 함께 저장.

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

질문 역시 동일한 Embedding 모델을 사용하여 벡터로 변환.

```text
질문
    ↓
Embedding
    ↓
[0.128, -0.703, 0.301, ...]
```

질문 벡터를 이용하여 pgvector에서 의미적으로 가까운 문서 검색.

예:

```sql
SELECT content
FROM rag_documents
ORDER BY embedding <=> query_embedding
LIMIT 3;
```

이 과정은 Phase 1에서 실습한 **Vector Similarity Search**와 동일.

```text
질문 Embedding
    ↓
pgvector Similarity Search
    ↓
관련 Chunk Top-K 검색
```

여기까지가 **Retrieval**.

---

## 검색 결과를 LLM에 전달

검색된 문서를 사용자 질문과 함께 LLM에 전달.

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

LLM은 검색된 운영 문서를 근거로 답변 생성.

```text
먼저 pg_stat_activity에서 application_name별 connection 수를 확인합니다.
특히 batch-api connection이 100개 이상인지 확인해야 합니다.
Runbook 정책상 DBA 승인 없이 connection을 terminate해서는 안 됩니다.
```

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

## Phase 1과 Phase 2의 연결

### Phase 1

```text
Vector
   ↓
pgvector
   ↓
가까운 Vector 검색
```

PostgreSQL에 Vector를 저장하고 Cosine / L2 Distance를 이용하여 가까운 Vector를 검색하는 방법 실습.

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

Phase 1에서 실습한 Vector Similarity Search를 실제 DB 운영 문서 검색에 활용.

이번 Phase의 핵심은 다음 세 요소의 연결.

```text
Embedding → pgvector → LLM
```

## 핵심 이해

> LLM이 직접 pgvector를 검색하는 것이 아님.
>
> 애플리케이션이 질문을 Embedding으로 변환하고,
> pgvector에서 관련 문서를 검색한 뒤,
> 검색 결과를 LLM Context로 전달.

이 구조를 기반으로 다음 단계에서 실제 검색 대상이 될 **DB 운영 Runbook** 작성.

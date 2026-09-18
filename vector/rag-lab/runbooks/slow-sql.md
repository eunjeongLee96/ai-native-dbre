# Slow SQL

## 증상

평소보다 SQL 실행 시간이 증가하거나 장시간 실행되는 Query가 발생한 상태임.

Slow SQL이 지속되면 Connection 점유 시간이 길어지고 전체 DB 응답 시간에도 영향을 줄 수 있음.

## 확인 항목

`pg_stat_activity`에서 장시간 실행 중인 Query를 확인함.

```sql
SELECT pid,
       usename,
       application_name,
       now() - query_start AS running_time,
       state,
       wait_event_type,
       wait_event,
       query
FROM pg_stat_activity
WHERE state = 'active'
  AND pid <> pg_backend_pid()
ORDER BY query_start;
```

Query가 Lock을 기다리고 있는지 확인함.

실행 계획에서 대량 Scan이 발생하는지, 적절한 Index를 사용하고 있는지 확인함.

최근 데이터량 증가, 통계 정보 변화, SQL 또는 Index 변경 여부를 함께 확인함.

## 가능한 원인

- 필요한 Index가 없어 대량의 데이터를 Scan함.
- 실행 계획이 변경되어 비효율적인 접근 경로를 사용함.
- 데이터량 증가로 기존 SQL의 처리 비용이 커짐.
- 다른 Transaction의 Lock을 기다리면서 실행 시간이 증가함.

## 대응

SQL과 실행 계획을 먼저 확보하여 지연 원인을 확인함.

Index 생성 또는 삭제와 같은 변경 작업은 자동으로 수행하지 않음.

운영 DB 변경이 필요한 경우 영향도를 검토하고 DBA 승인 후 수행함.

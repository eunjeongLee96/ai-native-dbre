# Lock Wait

## 증상

Transaction이 다른 Transaction의 Lock 해제를 기다리면서 SQL 처리가 진행되지 않는 상태임.

Lock Wait이 길어지면 응답 시간이 증가하고 여러 Session으로 대기 상황이 확산될 수 있음.

## 확인 항목

`pg_stat_activity`에서 Lock을 기다리는 Session을 확인함.

```sql
SELECT pid,
       usename,
       application_name,
       state,
       wait_event_type,
       wait_event,
       query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';
```

필요한 경우 `pg_locks`를 함께 확인하여 Blocking Session과 Blocked Session의 관계를 파악함.

장시간 열린 Transaction이 존재하는지 확인함.

Application에서 여러 테이블이나 Row를 서로 다른 순서로 갱신하고 있는지도 확인함.

## 가능한 원인

- 장시간 Transaction이 Lock을 보유하고 있음.
- 여러 Transaction이 동일한 Row를 동시에 변경함.
- Transaction마다 데이터 갱신 순서가 달라 Lock 경합이 발생함.
- Transaction 종료가 지연되어 Lock이 장시간 유지됨.

## 대응

Blocking Session과 Blocked Session을 먼저 식별하고 어떤 작업에서 Lock이 발생했는지 확인함.

Session 강제 종료나 Transaction Rollback은 자동으로 수행하지 않음.

운영 Session 종료가 필요한 경우 영향도를 확인하고 DBA 승인 후 수행함.

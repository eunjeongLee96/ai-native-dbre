# Connection Spike

## 증상

평소보다 PostgreSQL Connection 수가 갑자기 증가한 상태임.

Connection 수가 지속적으로 증가하면 `max_connections`에 도달하여 새로운 Connection을 생성하지 못할 수 있음.

## 확인 항목

현재 Connection 상태를 `pg_stat_activity`에서 확인함.

```sql
SELECT application_name,
       state,
       count(*)
FROM pg_stat_activity
GROUP BY application_name, state
ORDER BY count(*) DESC;
```

특정 Application에서 Connection이 집중적으로 발생하는지 확인함.

`idle in transaction` 상태의 Connection이 장시간 유지되는지도 확인함.

최근 Application 배포, Batch 실행, Connection Pool 설정 변경 여부를 확인함.

## 가능한 원인

- Batch 작업에서 다수의 Connection을 생성함.
- Connection Pool 설정 오류로 Connection이 과도하게 생성됨.
- Application 장애로 Retry가 반복되면서 Connection이 증가함.
- Transaction이 종료되지 않아 Connection이 반환되지 않음.

## 대응

Connection 증가 원인을 먼저 확인함.

Application 또는 Connection Pool 문제인 경우 해당 설정을 확인함.

장시간 유지되는 비정상 Session이 있더라도 즉시 종료하지 않고 원인을 확인한 후 DBA 승인 하에 종료함.

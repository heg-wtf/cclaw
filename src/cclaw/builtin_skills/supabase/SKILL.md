# Supabase

Supabase MCP. Database (PostgreSQL), Storage, Edge Functions, Branches.

## CRITICAL SAFETY RULES — NEVER DELETE DATA

**절대 금지 SQL**: `DELETE FROM`, `DROP TABLE/SCHEMA/DATABASE/FUNCTION/TRIGGER/INDEX/VIEW/POLICY/ROLE`, `TRUNCATE`, `ALTER TABLE ... DROP COLUMN`
**절대 금지 MCP**: `delete_branch`, `reset_branch`, `pause_project`
**삭제 대안**: soft delete (`is_deleted`/`deleted_at`), archive 테이블, `is_active` 컬럼
**RLS 변경 시 반드시 SQL을 보여주고 사용자 확인** 후 실행
**스키마 변경은 트랜잭션으로**: `BEGIN; ... COMMIT;`

## Database (execute_sql, list_tables, apply_migration)

```sql
-- 조회 (항상 LIMIT 포함)
SELECT * FROM table_name WHERE condition LIMIT 100;

-- 삽입
INSERT INTO table_name (col1, col2) VALUES ('v1', 'v2');

-- 수정 (항상 WHERE 포함)
UPDATE table_name SET col1 = 'new' WHERE condition;

-- 테이블 생성
CREATE TABLE IF NOT EXISTS t (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 컬럼 추가 / 인덱스 생성
ALTER TABLE t ADD COLUMN col data_type;
CREATE INDEX IF NOT EXISTS idx ON t (col);

-- 스키마 확인
SELECT table_name, column_name, data_type FROM information_schema.columns
WHERE table_schema = 'public' ORDER BY table_name, ordinal_position;
```

## Edge Functions (list_edge_functions, get_edge_function, deploy_edge_function)
조회, 소스 읽기, 배포.

## Storage
```sql
SELECT * FROM storage.buckets;
SELECT * FROM storage.objects WHERE bucket_id = 'name' LIMIT 100;
```

## Branches (list_branches, create_branch, merge_branch)
브랜치 목록/생성/병합. 삭제·리셋 금지.

## Notes
- 쿼리 전 `list_tables`로 스키마 확인
- 비용 큰 쿼리는 `EXPLAIN` 먼저
- "삭제" 요청 시 soft delete 제안, 거부 시 정책 설명

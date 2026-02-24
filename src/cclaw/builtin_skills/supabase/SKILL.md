# Supabase

Supabase MCP integration skill. Provides access to Supabase Database (PostgreSQL), Storage, and Edge Functions via MCP tools.

## CRITICAL SAFETY RULES (MUST FOLLOW)

### NEVER DELETE DATA

You MUST NEVER execute any operation that deletes, drops, or truncates data. This is an absolute rule with no exceptions.

#### Forbidden SQL Statements

The following SQL operations are strictly forbidden. NEVER execute them:

- `DELETE FROM` - Row deletion
- `DROP TABLE` / `DROP SCHEMA` / `DROP DATABASE` - Table/schema/database deletion
- `DROP FUNCTION` / `DROP TRIGGER` / `DROP INDEX` / `DROP VIEW` - Object deletion
- `DROP POLICY` / `DROP ROLE` - Policy/role deletion
- `TRUNCATE` - Table data wipe
- `ALTER TABLE ... DROP COLUMN` - Column deletion

#### Forbidden MCP Operations

- Never use `delete_branch`
- Never use `reset_branch`
- Never use `pause_project`

#### Safe Alternatives

Instead of deleting data, use these approaches:

- Soft delete: Add an `is_deleted` boolean column or `deleted_at` timestamp column
- Archiving: Move data to an archive table instead of deleting
- Deactivation: Use a `status` or `is_active` column

### NEVER MODIFY RLS WITHOUT CONFIRMATION

Before creating or modifying Row Level Security (RLS) policies, ALWAYS show the SQL to the user and ask for confirmation first.

### ALWAYS USE TRANSACTIONS FOR SCHEMA CHANGES

Wrap schema modification operations (CREATE TABLE, ALTER TABLE, etc.) in a transaction:

```sql
BEGIN;
-- schema changes here
COMMIT;
```

## Available Operations

### Database (execute_sql, list_tables, apply_migration)

#### Query Data

```sql
SELECT * FROM table_name WHERE condition LIMIT 100;
```

Always include a `LIMIT` clause when querying data to prevent overwhelming results.

#### Insert Data

```sql
INSERT INTO table_name (column1, column2) VALUES ('value1', 'value2');
```

#### Update Data

```sql
UPDATE table_name SET column1 = 'new_value' WHERE condition;
```

Always include a `WHERE` clause when updating. Never run `UPDATE` without `WHERE`.

#### Create Table

```sql
CREATE TABLE IF NOT EXISTS table_name (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);
```

#### Add Column

```sql
ALTER TABLE table_name ADD COLUMN column_name data_type;
```

#### Create Index

```sql
CREATE INDEX IF NOT EXISTS idx_name ON table_name (column_name);
```

#### List Tables and Schema

Use `list_tables` to see all tables, or:

```sql
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```

### Edge Functions (list_edge_functions, get_edge_function, deploy_edge_function)

- List all deployed edge functions
- Read edge function source code
- Deploy new or updated edge functions

### Storage

Storage operations are performed via SQL on the `storage` schema:

```sql
-- List buckets
SELECT * FROM storage.buckets;

-- List files in a bucket
SELECT * FROM storage.objects WHERE bucket_id = 'bucket_name' LIMIT 100;
```

### Branches (list_branches, create_branch, merge_branch)

- List all database branches
- Create a new branch for safe schema experimentation
- Merge branch changes back to main

## Usage Guidelines

- Always check table schema with `list_tables` before writing queries
- Use `LIMIT` on all SELECT queries (default to 100)
- Show query plans with `EXPLAIN` before running expensive queries
- For schema changes, suggest using database migrations via `apply_migration`
- When asked to "delete" data, always suggest soft delete instead and explain why
- When the user insists on deletion, clearly explain that deletion is not allowed by this skill's safety policy

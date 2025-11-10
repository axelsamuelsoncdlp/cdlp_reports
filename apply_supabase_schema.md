# Supabase Setup Instructions

## 1. Create Environment Files

### Backend (.env)
Create `.env` in the project root:
```
SUPABASE_URL=https://ebfykqjmiomafwvnzflz.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImViZnlrcWptaW9tYWZ3dm56Zmx6Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTkxMDg4NSwiZXhwIjoyMDc3NDg2ODg1fQ.zFZfiK8gtGNbdeWrpdRzBOWSy3kegEOUdOuilvvuU7w
```

### Frontend (.env.local)
Create `frontend/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://ebfykqjmiomafwvnzflz.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImViZnlrcWptaW9tYWZ3dm56Zmx6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE5MTA4ODUsImV4cCI6MjA3NzQ4Njg4NX0.FIKauO9kwQooHz6ISmrxoVAT2Dvf9EKBxTic9BW-WRM
```

## 2. Apply SQL Schema

### Option A: Via Supabase Dashboard
1. Go to https://supabase.com/dashboard/project/ebfykqjmiomafwvnzflz
2. Click "SQL Editor" in the left sidebar
3. Click "New query"
4. Copy and paste the contents of `supabase_schema.sql`
5. Click "Run" (or press Cmd/Ctrl + Enter)

### Option B: Via Supabase CLI (if installed)
```bash
supabase db push --db-url "postgresql://postgres:[YOUR_PASSWORD]@db.ebfykqjmiomafwvnzflz.supabase.co:5432/postgres" < supabase_schema.sql
```

## 3. Verify Schema

After running the SQL, verify tables exist:
- `weeks`
- `budget_general`
- `budget_general_totals`
- `budget_markets_detailed`
- `budget_markets_totals`
- `sync_runs`

## 4. Test Sync Command

Once schema is applied and env vars are set:
```bash
weekly-report sync-supabase --week 2025-42
```

This will:
1. Compute budget and actuals data
2. Map to Supabase format
3. Batch upsert rows
4. Record sync status in `sync_runs`







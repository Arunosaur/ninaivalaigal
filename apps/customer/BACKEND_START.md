# Starting the Backend Server

**Quick Fix:** The frontend requires the backend API server to be running.

---

## The Problem

When you see:
- "Network Error" in the UI
- `ERR_CONNECTION_REFUSED` in console
- Empty black page on `/team/billing/payment-method`

**Cause:** Backend API server is not running.

---

## Quick Start Backend

### Option 1: Using Conda (Recommended)

```bash
# Activate conda environment
conda activate nina

# Navigate to server directory
cd server

# Start FastAPI server on port 13390 (for dev+apple)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Note:** If using Apple Container, the port mapping will expose 8000 → 13390.

### Option 2: Direct Start (Standalone)

```bash
cd server

# Set environment variables if needed
export NINAIVALAIGAL_DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
export NINAIVALAIGAL_JWT_SECRET="your-secret-key"

# Start on port 13390 directly
uvicorn main:app --host 0.0.0.0 --port 13390 --reload
```

---

## Verify Backend is Running

```bash
# Check if backend responds
curl http://localhost:13390/health

# Should return: {"status": "healthy", "service": "ninaivalaigal"}
```

---

## Port Configuration

**Frontend (apps/customer):**
- Runs on: `localhost:8101`
- Expects backend on: `localhost:13390` (auto-detected from port 8101)

**Backend (server):**
- Should run on: `localhost:13390` (for dev+apple)
- Or: `localhost:13370` (for dev+docker)

**Match:** Frontend port 8101 → Backend port 13390 ✅

---

## After Starting Backend

1. ✅ Backend should show: `INFO: Uvicorn running on http://0.0.0.0:8000`
2. ✅ Frontend should connect successfully
3. ✅ API calls should work
4. ✅ Payment pages should load

---

## Troubleshooting

### "Port already in use"

```bash
# Find process using port 13390
lsof -i :13390

# Kill it
kill -9 <PID>
```

### "Database connection failed"

Ensure PostgreSQL is running:
```bash
brew services start postgresql@15
# or
psql -U youruser -d yourdb
```

### Still Not Working?

Check:
- [ ] Backend logs for errors
- [ ] Database is accessible
- [ ] Environment variables are set
- [ ] Port 13390 is not blocked

---

## Full Stack Startup

For complete stack (PostgreSQL + Backend + Frontend):

1. **Start PostgreSQL:**
   ```bash
   brew services start postgresql@15
   ```

2. **Start Backend:**
   ```bash
   conda activate nina
   cd server
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Start Frontend (already running):**
   ```bash
   cd apps/customer
   npm run dev  # Port 8101
   ```

---

## Need More Help?

See:
- `docs/development/START_ALL_SERVERS.md`
- `services/core-api/README.md`

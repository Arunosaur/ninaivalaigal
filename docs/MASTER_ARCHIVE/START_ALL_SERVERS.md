# Ninaivalaigal Complete Server Startup Guide

## Prerequisites
- PostgreSQL installed via Homebrew
- Python 3.11+ with required packages
- Node.js (for potential frontend tooling)

## 🚀 Quick Start (All Servers)

**CURRENT SYSTEM STATUS (Updated September 15, 2025):**
- ✅ PostgreSQL 15.14 running on localhost:5432
- ✅ FastAPI backend running on localhost:13370 with CORS enabled
- ✅ Frontend static server running on localhost:8080
- ✅ All team/organization management APIs implemented and tested
- ✅ JWT authentication working end-to-end
- ✅ Database schema complete with proper constraints

### 1. Start PostgreSQL Database
```bash
# PostgreSQL 15 is required (not 14). Start manually due to permission issues:
LC_ALL="en_US.UTF-8" postgres -D /opt/homebrew/var/postgresql@15 &

# Alternative: Try brew services (may have permission issues)
brew services start postgresql@15

# Verify database is running
psql -U mem0user -d mem0db -c "SELECT version();"
```

### 2. Start FastAPI Backend Server
```bash
cd /Users/asrajag/Workspace/mem0/server

# Set environment variables (optional - has defaults)
export NINAIVALAIGAL_JWT_SECRET="your-secret-key-here"
export NINAIVALAIGAL_JWT_EXPIRATION_HOURS="168"  # 7 days
export NINAIVALAIGAL_DATABASE_URL="postgresql://mem0user:mem0pass@localhost:5432/mem0db"

# Start FastAPI server with auto-reload
uvicorn main:app --host 127.0.0.1 --port 13370 --reload

# Server will be available at: http://127.0.0.1:13370
# API documentation at: http://127.0.0.1:13370/docs
```

### 3. Start Frontend Web Server
```bash
cd /Users/asrajag/Workspace/mem0/frontend

# Start simple HTTP server for frontend
python3 -m http.server 8080
```

### 4. Start MCP Server (Optional - for VS Code integration)
```bash
cd /Users/asrajag/Workspace/mem0/server

# Start MCP server
python3 mcp_server.py
```

## 📋 Server Status Check

### Verify All Services Running
```bash
# Check PostgreSQL 15
lsof -i :5432
psql -U mem0user -d mem0db -c "SELECT version();"

# Check FastAPI Backend (health endpoint)
curl http://127.0.0.1:13370/

# Test API with authentication
curl -X GET http://127.0.0.1:13370/organizations -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Check Frontend
curl http://localhost:8080/

# Check MCP (if running)
lsof -i :8765
```

## 🌐 Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend UI** | http://localhost:8080/ | Main user interface |
| **Login Page** | http://localhost:8080/login.html | User authentication |
| **Dashboard** | http://localhost:8080/dashboard.html | User dashboard |
| **Team Management** | http://localhost:8080/team-management.html | Team operations |
| **Org Management** | http://localhost:8080/organization-management.html | Organization operations |
| **FastAPI Backend** | http://127.0.0.1:13370/ | API server |
| **API Docs** | http://127.0.0.1:13370/docs | Interactive API documentation |
| **Database** | postgresql://localhost:5432/mem0db | PostgreSQL database |

## 🔧 Troubleshooting

### PostgreSQL Issues
```bash
# If PostgreSQL won't start
brew services stop postgresql@15
brew services start postgresql@15

# Check PostgreSQL logs
tail -f /opt/homebrew/var/log/postgresql@15.log

# Reset PostgreSQL if needed
brew services restart postgresql@15

# Manual start with locale fix (recommended):
LC_ALL="en_US.UTF-8" postgres -D /opt/homebrew/var/postgresql@15
```

### FastAPI Issues
```bash
# Check if port 13370 is in use
lsof -i :13370

# Kill existing process if needed
kill $(lsof -t -i:13370)

# Check server logs
cd /Users/asrajag/Workspace/mem0/server
tail -f server.log
```

### Frontend Issues
```bash
# Check if port 8080 is in use
lsof -i :8080

# Kill existing process if needed
kill $(lsof -t -i:8080)

# Alternative frontend server
cd /Users/asrajag/Workspace/mem0/frontend
python3 -m http.server 3000  # Use different port
```

### CORS Issues
If frontend can't connect to backend:
- Ensure FastAPI server has CORS middleware enabled (already configured)
- Check browser console for CORS errors
- Verify API calls use full URLs: `http://127.0.0.1:13370/api/endpoint`

## 🔐 Authentication

### Test User Accounts

**Existing User:**
- **Email**: durai@example.com
- **Password**: password  # pragma: allowlist secret123 (note: may need to be reset)
- **User ID**: 8
- **Role**: user

**Test User (created during testing):**
- **Email**: test@example.com
- **Password**: password  # pragma: allowlist secret123
- **User ID**: 11
- **Role**: user

### Test Authentication
```bash
# Test signup API (create new user)
curl -X POST "http://127.0.0.1:13370/auth/signup/individual" \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password  # pragma: allowlist secret": "password123", "name": "New User"}'

# Test login API
curl -X POST "http://127.0.0.1:13370/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password  # pragma: allowlist secret": "password123"}'

# Test organization management (with JWT token  # pragma: allowlist secret from login)
curl -X GET "http://127.0.0.1:13370/organizations" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"

# Test team creation
curl -X POST "http://127.0.0.1:13370/teams" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Team", "organization_id": 1, "description": "Test team"}'
```

## 📊 Database Schema

### Key Tables
- `users` - User accounts and authentication
- `contexts` - Memory contexts with ownership
- `memories` - Stored memories and data
- `teams` - Team management
- `organizations` - Organization management
- `team_members` - Team membership and roles

### Database Connection
```bash
# Connect to database
psql -U mem0user -d mem0db

# Check table status
\dt

# View contexts
SELECT name, owner_id, scope, is_active FROM contexts;
```

## 🛠 Development Mode

### Auto-Reload Setup
```bash
# Terminal 1: Database
brew services start postgresql@14

# Terminal 2: Backend with auto-reload
cd /Users/asrajag/Workspace/mem0/server
uvicorn main:app --host 127.0.0.1 --port 13370 --reload

# Terminal 3: Frontend
cd /Users/asrajag/Workspace/mem0/frontend
python3 -m http.server 8080

# Terminal 4: CLI testing
cd /Users/asrajag/Workspace/mem0
./mem0 contexts  # Test CLI commands
```

## 🚦 Production Considerations

### Environment Variables
```bash
# Required for production
export NINAIVALAIGAL_JWT_SECRET="secure-random-secret-key"
export NINAIVALAIGAL_DATABASE_URL="postgresql://user:pass@host:port/db"
export NINAIVALAIGAL_JWT_EXPIRATION_HOURS="24"
```

### Security Checklist
- [ ] Change default JWT secret
- [ ] Use strong database password  # pragma: allowlist secrets
- [ ] Enable HTTPS in production
- [ ] Configure proper CORS origins
- [ ] Set up database backups
- [ ] Monitor server logs

## 📝 Startup Script

Create `start_all.sh`:
```bash
#!/bin/bash
echo "🚀 Starting Ninaivalaigal servers..."

# Start PostgreSQL 15 (manual start recommended)
echo "📊 Starting PostgreSQL 15..."
LC_ALL="en_US.UTF-8" postgres -D /opt/homebrew/var/postgresql@15 &
# Alternative: brew services start postgresql@15

# Wait for database
sleep 3

# Start FastAPI backend
echo "🔧 Starting FastAPI backend..."
cd /Users/asrajag/Workspace/mem0/server
uvicorn main:app --host 127.0.0.1 --port 13370 --reload &
FASTAPI_PID=$!

# Start frontend
echo "🌐 Starting frontend..."
cd /Users/asrajag/Workspace/mem0/frontend
python3 -m http.server 8080 &
FRONTEND_PID=$!

echo "✅ All servers started!"
echo "📱 Frontend: http://localhost:8080/"
echo "🔧 Backend: http://127.0.0.1:13370/"
echo "📚 API Docs: http://127.0.0.1:13370/docs"

# Keep script running
wait
```

Make executable: `chmod +x start_all.sh`

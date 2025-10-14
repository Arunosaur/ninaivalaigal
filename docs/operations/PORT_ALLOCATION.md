# 🔌 Port Allocation Guide

**Updated:** October 13, 2025  
**Purpose:** Avoid port conflicts between Developer A and Developer B work

---

## 📊 **Port Assignments**

| Port | Service | Owner | Status |
|------|---------|-------|--------|
| **3000** | Frontend Dev Server | Developer A | Reserved |
| **3500** | SPEC Dashboard (Docusaurus) | Documentation | ✅ Active |
| **13390** | Main API | Backend | ✅ Running |
| **11434** | Ollama LLM | Shared | ✅ Running |

---

## 🎯 **Why Port 3500?**

The SPEC Dashboard uses **port 3500** to avoid conflicts with:
- Developer A's frontend work (typically port 3000)
- Any React/Next.js development servers (default port 3000)
- Create React App defaults (port 3000)

---

## 🌐 **SPEC Dashboard Access**

```
http://localhost:3500/dashboard
http://localhost:3500/timeline
http://localhost:3500/timeline-gantt
http://localhost:3500/specs
```

---

## 🔧 **Changing the Port**

If you need to change the Docusaurus port:

### **Method 1: Edit package.json**
```json
{
  "scripts": {
    "start": "docusaurus start --port YOUR_PORT"
  }
}
```

### **Method 2: Command line**
```bash
cd docusaurus
npx docusaurus start --port YOUR_PORT
```

---

## 🚨 **Port Conflict Resolution**

If you see "Port already in use" error:

### **1. Check what's using the port**
```bash
lsof -i :3500
```

### **2. Kill the process**
```bash
kill -9 <PID>
```

### **3. Or use a different port**
```bash
npm start -- --port 3501
```

---

## 📋 **Container Port Mapping**

From Apple Container CLI:

| Container | Internal Port | Host Port | Purpose |
|-----------|---------------|-----------|---------|
| ninaivalaigal-dev-api | 8000 | 13390 | Main API |
| ninaivalaigal-dev-ui-admin | 3000 | varies | Admin UI |
| ninaivalaigal-dev-ui-customer | 3000 | varies | Customer UI |
| ollama | 11434 | 11434 | LLM service |
| nv-db | 5432 | varies | PostgreSQL |
| nv-redis | 6379 | varies | Redis |

---

## ✅ **Best Practices**

1. **Always check port availability** before starting a new service
2. **Document port assignments** when adding new services
3. **Use high ports (>3000)** for development tools to avoid conflicts
4. **Reserve 3000-3010** for Developer A's frontend work
5. **Use 3500+** for documentation and support tools

---

## 🎯 **Current Allocation**

### **Developer A (Frontend)**
- Ports: 3000-3010
- Purpose: React/Next.js development
- Tools: HMR, dev servers, Storybook

### **Developer B (Backend/Docs)**
- Port: 3500 (SPEC Dashboard)
- Purpose: Documentation, specs
- Tools: Docusaurus, static site generation

### **Shared Services**
- Port: 11434 (Ollama)
- Port: 13390 (Main API)
- Port: 6379 (Redis)
- Port: 5432 (PostgreSQL)

---

## 📝 **Quick Commands**

### **Check all listening ports**
```bash
lsof -i -P | grep LISTEN
```

### **Check specific port**
```bash
lsof -i :3500
```

### **Find available port**
```bash
# Check if port is free
nc -zv localhost 3500
```

### **Start dashboard on custom port**
```bash
cd docusaurus
npm start -- --port 3600
```

---

**Remember:** Keep this document updated when adding new services!

---

**Last Updated:** October 13, 2025  
**Dashboard Port:** 3500  
**Status:** ✅ No conflicts

# ninaivalaigal API Examples

This document provides working code examples for the ninaivalaigal API in curl, Python, and JavaScript.

## 1. Authentication

### Sign Up

**curl**
```bash
curl -X POST http://localhost:13390/auth/signup/individual \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "password": "SecurePass123!",
    "name": "Your Name"
  }'
```

**Python**
```python
import requests

response = requests.post(
    "http://localhost:13390/auth/signup/individual",
    json={
        "email": "you@example.com",
        "password": "SecurePass123!",
        "name": "Your Name"
    }
)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

axios.post("http://localhost:13390/auth/signup/individual", {
  email: "you@example.com",
  password: "SecurePass123!",
  name: "Your Name"
}).then(response => {
  console.log(response.data);
});
```

### Login

**curl**
```bash
curl -X POST http://localhost:13390/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "you@example.com",
    "password": "SecurePass123!"
  }'
```

**Python**
```python
import requests

response = requests.post(
    "http://localhost:13390/auth/login",
    json={
        "email": "you@example.com",
        "password": "SecurePass123!"
    }
)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

axios.post("http://localhost:13390/auth/login", {
  email: "you@example.com",
  password: "SecurePass123!"
}).then(response => {
  console.log(response.data);
});
```

### Refresh Token

**curl**
```bash
curl -X POST http://localhost:13390/auth/token/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

**Python**
```python
import requests

response = requests.post(
    "http://localhost:13390/auth/token/refresh",
    json={
        "refresh_token": "YOUR_REFRESH_TOKEN"
    }
)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

axios.post("http://localhost:13390/auth/token/refresh", {
  refresh_token: "YOUR_REFRESH_TOKEN"
}).then(response => {
  console.log(response.data);
});
```

## 2. Context Management

### Create Context

**curl**
```bash
curl -X POST http://localhost:13390/contexts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "description": "My personal project",
    "scope": "personal"
  }'
```

**Python**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

response = requests.post(
    "http://localhost:13390/contexts",
    headers=headers,
    json={
        "name": "my-project",
        "description": "My personal project",
        "scope": "personal"
    }
)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

const headers = {
  "Authorization": "Bearer YOUR_JWT_TOKEN"
};

axios.post("http://localhost:13390/contexts", {
  name: "my-project",
  description: "My personal project",
  scope: "personal"
}, { headers }).then(response => {
  console.log(response.data);
});
```

### List Contexts

**curl**
```bash
curl -X GET http://localhost:13390/contexts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

response = requests.get("http://localhost:13390/contexts", headers=headers)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

const headers = {
  "Authorization": "Bearer YOUR_JWT_TOKEN"
};

axios.get("http://localhost:13390/contexts", { headers }).then(response => {
  console.log(response.data);
});
```

### Share Context

**curl**
```bash
curl -X POST http://localhost:13390/contexts/1/share \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_type": "user",
    "target_id": 2,
    "permission_level": "read"
  }'
```

**Python**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

response = requests.post(
    "http://localhost:13390/contexts/1/share",
    headers=headers,
    json={
        "target_type": "user",
        "target_id": 2,
        "permission_level": "read"
    }
)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

const headers = {
  "Authorization": "Bearer YOUR_JWT_TOKEN"
};

axios.post("http://localhost:13390/contexts/1/share", {
  target_type: "user",
  target_id: 2,
  permission_level: "read"
}, { headers }).then(response => {
  console.log(response.data);
});
```

## 3. Memory Operations

### Store Memory

**curl**
```bash
curl -X POST http://localhost:13390/memory/remember \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "User prefers dark mode",
    "context_id": "user-preferences",
    "meta": {
      "user_id": "123",
      "timestamp": "2025-10-12",
      "confidence": 0.95
    }
  }'
```

**Python**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

response = requests.post(
    "http://localhost:13390/memory/remember",
    headers=headers,
    json={
        "text": "User prefers dark mode",
        "context_id": "user-preferences",
        "meta": {
            "user_id": "123",
            "timestamp": "2025-10-12",
            "confidence": 0.95
        }
    }
)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

const headers = {
  "Authorization": "Bearer YOUR_JWT_TOKEN"
};

axios.post("http://localhost:13390/memory/remember", {
  text: "User prefers dark mode",
  context_id: "user-preferences",
  meta: {
    user_id: "123",
    timestamp: "2025-10-12",
    confidence: 0.95
  }
}, { headers }).then(response => {
  console.log(response.data);
});
```

### Recall Memories

**curl**
```bash
curl -X GET "http://localhost:13390/memory/recall?query=user%20preferences&k=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

params = {
    "query": "user preferences",
    "k": 5
}

response = requests.get("http://localhost:13390/memory/recall", headers=headers, params=params)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

const headers = {
  "Authorization": "Bearer YOUR_JWT_TOKEN"
};

axios.get("http://localhost:13390/memory/recall", {
  headers,
  params: {
    query: "user preferences",
    k: 5
  }
}).then(response => {
  console.log(response.data);
});
```

### List Memories

**curl**
```bash
curl -X GET "http://localhost:13390/memory/memories?context_id=user-preferences" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

params = {
    "context_id": "user-preferences"
}

response = requests.get("http://localhost:13390/memory/memories", headers=headers, params=params)

print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

const headers = {
  "Authorization": "Bearer YOUR_JWT_TOKEN"
};

axios.get("http://localhost:13390/memory/memories", {
  headers,
  params: {
    context_id: "user-preferences"
  }
}).then(response => {
  console.log(response.data);
});
```

### Delete Memory

**curl**
```bash
curl -X DELETE http://localhost:13390/memory/memories/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Python**
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}

response = requests.delete("http://localhost:13390/memory/memories/1", headers=headers)

print(response.status_code)
```

**JavaScript**
```javascript
import axios from 'axios';

const headers = {
  "Authorization": "Bearer YOUR_JWT_TOKEN"
};

axios.delete("http://localhost:13390/memory/memories/1", { headers }).then(response => {
  console.log(response.status);
});
```

## 4. Error Handling

### Handling 401 Unauthorized

**Python**
```python
import requests

headers = {
    "Authorization": "Bearer INVALID_TOKEN"
}

response = requests.get("http://localhost:13390/memory/memories", headers=headers)

if response.status_code == 401:
    print("Unauthorized. Refreshing token...")
    refresh_response = requests.post(
        "http://localhost:13390/auth/token/refresh",
        json={"refresh_token": "YOUR_REFRESH_TOKEN"}
    )
    if refresh_response.status_code == 200:
        new_token = refresh_response.json()["access_token"]
        headers["Authorization"] = f"Bearer {new_token}"
        response = requests.get("http://localhost:13390/memory/memories", headers=headers)
        print(response.json())
    else:
        print("Failed to refresh token. Please log in again.")
else:
    print(response.json())
```

**JavaScript**
```javascript
import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://localhost:13390'
});

instance.interceptors.response.use(response => response, async error => {
  const originalRequest = error.config;
  if (error.response.status === 401 && !originalRequest._retry) {
    originalRequest._retry = true;
    const refreshToken = localStorage.getItem('refresh_token');
    const { data } = await axios.post('http://localhost:13390/auth/token/refresh', {
      refresh_token: refreshToken
    });
    axios.defaults.headers.common['Authorization'] = 'Bearer ' + data.access_token;
    return instance(originalRequest);
  }
  return Promise.reject(error);
});

instance.get('/memory/memories').then(response => {
  console.log(response.data);
});
```

## 5. Complete Application Example

This example shows a simple Python application that signs up, logs in, creates a context, stores a memory, and recalls it.

```python
import requests

BASE_URL = "http://localhost:13390"

# Sign up
signup_data = {
    "email": "testuser@example.com",
    "password": "password123",
    "name": "Test User"
}
signup_response = requests.post(f"{BASE_URL}/auth/signup/individual", json=signup_data)
print(f"Signup Response: {signup_response.json()}")

# Login
login_data = {
    "email": "testuser@example.com",
    "password": "password123"
}
login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
access_token = login_response.json()["user"]["jwt_token"]
refresh_token = login_response.json()["user"]["refresh_token"]
print(f"Login Response: {login_response.json()}")

headers = {
    "Authorization": f"Bearer {access_token}"
}

# Create Context
context_data = {
    "name": "my-test-project",
    "description": "A test project",
    "scope": "personal"
}
context_response = requests.post(f"{BASE_URL}/contexts", headers=headers, json=context_data)
context_id = context_response.json()["id"]
print(f"Context Response: {context_response.json()}")

# Store Memory
memory_data = {
    "text": "This is a test memory",
    "context_id": context_id,
}
memory_response = requests.post(f"{BASE_URL}/memory/remember", headers=headers, json=memory_data)
print(f"Memory Response: {memory_response.json()}")

# Recall Memories
recall_params = {
    "query": "test memory",
    "k": 1
}
recall_response = requests.get(f"{BASE_URL}/memory/recall", headers=headers, params=recall_params)
print(f"Recall Response: {recall_response.json()}")
```

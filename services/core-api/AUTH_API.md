# Core API - Authentication Endpoints

This document provides details on the authentication and authorization endpoints for the Core API service.

## Main Authentication Flow (`main_with_auth.py`)

These are the primary, recommended endpoints for user authentication.

### 1. User Signup

*   **Endpoint:** `POST /auth/signup`
*   **Description:** Creates a new user account.
*   **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "securepassword123",
      "name": "Test User",
      "account_type": "individual"
    }
    ```

### 3. User Login (Advanced)

*   **Endpoint:** `POST /auth/login`
*   **Description:** Authenticates a user and returns a JWT token, refresh token, and user information.
*   **Request Body:**
    ```json
    {
        "email": "user@example.com",
        "password": "password123"
    }
    ```
*   **Response (Success):**
    ```json
    {
        "success": true,
        "message": "Login successful",
        "user": {
            "user_id": "user_id",
            "email": "user@example.com",
            "refresh_token": "your_refresh_token",
            "refresh_token_expires": "iso_timestamp"
        }
    }
    ```

### 4. User Logout

*   **Endpoint:** `POST /auth/logout`
*   **Description:** Logs a user out and can revoke the refresh token.
*   **Request Body:**
    ```json
    {
        "refresh_token": "user_refresh_token"
    }
    ```
*   **Response (Success):**
    ```json
    {
        "success": true,
        "message": "Logout successful",
        "refresh_token_revoked": true
    }
    ```

---

## Protected Routes (`routers/protected_routes.py`)

These routes require a valid JWT token in the `Authorization` header as a Bearer token.

### 1. Get User Profile

*   **Endpoint:** `GET /protected/profile`
*   **Description:** Retrieves the profile of the currently authenticated user.
*   **Response (Success):**
    ```json
    {
        "success": true,
        "user": {
            "user_id": "user_id",
            "email": "user@example.com",
            "account_type": "individual",
            "role": "user"
        },
        "message": "Profile retrieved successfully"
    }
    ```

### 2. Get User Teams

*   **Endpoint:** `GET /protected/teams`
*   **Description:** Retrieves the teams for the currently authenticated user.
*   **Response (Success):**
    ```json
    {
        "success": true,
        "teams": [
            {"id": 1, "name": "My Team", "role": "admin"},
            {"id": 2, "name": "Project Alpha", "role": "member"}
        ],
        "user_id": "user_id"
    }
    ```
*   **Response (Success):**
    ```json
    {
      "success": true,
      "message": "User created successfully!",
      "user": {
        "id": "user_id_string",
        "email": "user@example.com",
        "name": "Test User",
        "account_type": "individual"
      },
      "jwt_token": "your_jwt_token",
      "token_type": "Bearer"
    }
    ```

### 2. User Login

*   **Endpoint:** `POST /auth/login`
*   **Description:** Authenticates a user and returns a JWT token.
*   **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "securepassword123"
    }
    ```
*   **Response (Success):**
    ```json
    {
      "success": true,
      "message": "Login successful!",
      "user": {
        "id": "user_id_string",
        "email": "user@example.com",
        "name": "Test User"
      },
      "jwt_token": "your_jwt_token",
      "token_type": "Bearer"
    }
    ```

---

## Deprecated GET-based Authentication (`routers/auth.py`)

These endpoints were created as a temporary workaround and may be deprecated in the future. They use GET requests with query parameters.

### 1. GET-based Login

*   **Endpoint:** `GET /auth-working/login`
*   **Description:** Logs in a user via query parameters.
*   **Query Parameters:**
    *   `email`: The user's email.
    *   `password`: The user's password.
*   **Example Request:**
    `GET /auth-working/login?email=user@example.com&password=secret`
*   **Response (Success):**
    ```json
    {
        "success": true,
        "message": "Login successful",
        "jwt_token": "your_jwt_token",
        "user_id": "user_id_string",
        "email": "user@example.com",
        "account_type": "individual",
        "role": "user",
        "expires_in": 86400,
        "token_type": "Bearer"
    }
    ```

### 2. Validate Token

*   **Endpoint:** `GET /auth-working/validate-token`
*   **Description:** Validates a JWT token.
*   **Query Parameters:**
    *   `token`: The JWT token to validate.
*   **Example Request:**
    `GET /auth-working/validate-token?token=your_jwt_token`
*   **Response (Success):**
    ```json
    {
        "valid": true,
        "user_id": "user_id_string",
        "email": "user@example.com",
        "account_type": "individual",
        "role": "user",
        "exp": 1678886400
    }
    ```
---

## Advanced Signup and Authentication (`routers/signup_api.py`)

These endpoints handle more complex signup flows, including individual and organizational accounts, email verification, and password resets.

### 1. Individual User Signup

*   **Endpoint:** `POST /auth/signup/individual`
*   **Description:** Signs up an individual user.
*   **Request Body:**
    ```json
    {
        "email": "individual@example.com",
        "password": "password123",
        "name": "Individual User"
    }
    ```
*   **Response (Success):**
    ```json
    {
        "success": true,
        "message": "Individual user account created successfully",
        "user": {
            "user_id": "user_id",
            "email": "individual@example.com"
        },
        "next_steps": [
            "verify_email",
            "create_first_context",
            "install_tools"
        ]
    }
    ```

### 2. Organization Signup

*   **Endpoint:** `POST /auth/signup/organization`
*   **Description:** Signs up a new organization and an admin user for it.
*   **Request Body:**
    ```json
    {
        "user": {
            "email": "admin@neworg.com",
            "password": "adminpassword",
            "name": "Admin User"
        },
        "organization": {
            "name": "New Organization",
            "domain": "neworg.com",
            "size": "10-50",
            "industry": "Tech"
        }
    }
    ```
*   **Response (Success):**
    ```json
    {
        "success": true,
        "message": "Organization and admin account created successfully",
        "user_id": "admin_user_id",
        "organization_id": "org_id",
        "role": "organization_admin",
        "jwt_token": "your_jwt_token",
        "setup_steps": [
            "verify_email",
            "setup_teams",
            "invite_members",
            "create_org_contexts"
        ]
    }
    ```

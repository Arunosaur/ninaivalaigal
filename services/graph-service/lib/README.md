# mem0-server

This is the Core Memory Server for the `mem0` project. It is a headless, API-driven server that provides a universal, cross-platform memory layer for AI agents and human developers.

## API Design (v0.1.0)

The server exposes a simple REST API for managing memories and contexts.

### Endpoints

*   **`POST /memory`**: Creates a new memory entry.
    *   **Body:**
        ```json
        {
            "context": "<context_name>",
            "payload": {
                "type": "<entry_type>",
                "source": "<source_application>",
                "data": { ... }
            }
        }
        ```

*   **`GET /memory`**: Retrieves all memories for a given context.
    *   **Query Parameters:**
        *   `context=<context_name>`
    *   **Response:**
        ```json
        [
            { ...memory_entry... },
            { ...memory_entry... }
        ]
        ```

*   **`POST /context`**: Switches the active context for a given client.
    *   **Body:**
        ```json
        {
            "client_id": "<unique_client_id>",
            "context": "<new_context_name>"
        }
        ```

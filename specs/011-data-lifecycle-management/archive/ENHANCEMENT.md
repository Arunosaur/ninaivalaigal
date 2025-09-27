# SPEC-011: Data Lifecycle Management (Enhanced)

## Objective
Extend the original memory lifecycle management to include automation of expiration, archival, purging, and notification.

## Enhancements

### Features

| Feature            | Description |
|--------------------|-------------|
| TTL Support        | Automatic expiration of short-lived memory |
| Archival Rules     | Move inactive memories to cold storage (separate table/provider) |
| Purging Policies   | Periodic deletion of outdated memory, by age or size |
| Notification       | Notify users before permanent deletion |
| Lifecycle Metrics  | Count of active/expired/deleted memories per scope |

### Implementation

- Add `expires_at` column in memory DB schema
- Background job (e.g., `memory_gc.py`) for periodic cleanup
- Archive to separate provider (`archive_memory_provider`)
- CLI Commands:
  ```bash
  mem0 archive --older-than 90d
  mem0 purge --scope org --expired
  ```

## Status
🔄 In Progress — enhancing existing SPEC-011

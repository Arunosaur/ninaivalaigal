# SPEC-043: Offline Memory Capture and Deferred Sync

## 📌 Overview
This SPEC enables offline memory recording in constrained or air-gapped environments. It supports deferred synchronization once connectivity is restored.

## 🎯 Goals
- Allow users to record memory offline in CLI or client applications.
- Securely queue offline memory events locally.
- Automatically synchronize upon reconnection or manual trigger.

## 🔍 Features
- Offline Mode Flag: `--offline` in CLI or automatic detection
- Local Disk Queue: Persistent storage of offline memory logs
- Secure Queue Encryption using user-scoped keys
- Deferred Sync Trigger: Manual `mem sync` or automatic background job
- Offline Mode UI Indicator for web/desktop clients
- Conflict Detection on Sync (timestamp and checksum-based)

## 🏗️ Components
- `offline_queue.py`: Enqueue and decrypt local memory events
- `mem_sync.py`: Deferred synchronization handler
- `mem_status.py`: Indicator for offline status and unsynced tokens

## 🔐 Security & Privacy
- Local storage encrypted at rest using Fernet or OS keyring
- Prevent unauthorized memory injection during deferred sync
- All offline tokens retain original timestamps for audit consistency

## 🔗 Dependencies
- SPEC-031: Relevance Ranking (offline tokens can also be scored)
- SPEC-042: Memory Synchronization

## 🧪 Testing
- Airplane mode testing for offline capture and recovery
- Simulated disconnects in CI to test robustness
- Edge cases: sync failure, partial corruption, replay protection

## 📁 Location
`specs/043-offline-memory-capture/`

## 🗓️ Status
Planned

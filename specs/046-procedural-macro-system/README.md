# SPEC-046: Procedural Memory System (Macro Recording via e^M Agent & Plugin)

## 🧠 Purpose
Enable users to record repeatable task flows as *procedural memory macros* using the `e^M` agent, local OS integrations, or browser plugins.

## 📦 Features
- Macro mode toggle in CLI (`e^M macro start`, `e^M macro stop`)
- Native key/mouse automation capture (AutoHotKey-like)
- Browser/IDE plugin for scoped macro capture
- Replay macros locally (`e^M macro run <name>`)
- Link macros to specific memory contexts
- Redis-backed procedural memory cache
- Audit trail for macro execution

## 🛠️ Implementation Plan
- CLI trigger for macro mode
- Agent and plugin listeners for keyboard/mouse capture
- Serialization of procedural steps
- Contextual linkage to memory card (ID/tag)
- Security and sandbox isolation for replay

## 🧪 Tests
- Repeatable automation validation (Excel, browser tasks)
- CLI replay execution
- Redis memory sync

## 🏁 Output
- `type: "macro"` in memory DB
- JSON macro steps with timestamp + trigger events
- CLI and Web UI macro runners

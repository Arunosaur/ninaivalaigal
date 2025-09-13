# Changelog

## [1.0.0-ninaivalaigal] - 2025-09-13

### 🎉 Major Release: Complete Rebranding to Ninaivalaigal

#### Brand Identity
- **Product Name**: mem0 → Ninaivalaigal (Tamil: memories/recollections)
- **Command Agent**: @mem0 → @e^M (exponential Memory)
- **Company**: Medhays (www.medhasys.com)
- **Vision**: Foundation for broader AI ecosystem (SmritiOS, TarangAI, Pragna, FluxMind)

#### Frontend UI
- Updated all HTML pages (signup.html, login.html, dashboard.html)
- Changed titles from "mem0" to "Ninaivalaigal"
- Updated descriptions from "AI Memory" to "e^M Memory"
- Rebranded welcome messages and navigation

#### CLI & Commands
- Created new CLI clients: `eM.py` and `client/eM`
- Command invocation: `mem0` → `eM`
- Updated all error messages and help text
- Preserved all existing functionality

#### Configuration & Environment
- New config file: `ninaivalaigal.config.json`
- Environment variables: `MEM0_*` → `NINAIVALAIGAL_*`
- Updated database connection strings
- JWT secret key variables updated

#### MCP Server
- Server name: "mem0" → "ninaivalaigal"
- Resource URIs: `mem0://` → `ninaivalaigal://`
- Updated MCP client configuration
- User ID environment: `MEM0_USER_ID` → `NINAIVALAIGAL_USER_ID`

#### Documentation
- Updated README.md with new brand identity
- Rebranded IDE testing guides
- All command references: `@mem0` → `@e^M`
- Created comprehensive rebranding completion report

#### Architecture Preserved
- FastAPI Server (port 13370) - REST API with JWT auth
- MCP Server (stdio) - Model Context Protocol for AI integration
- Dual-server architecture maintained
- All existing functionality preserved
- Database schema unchanged
- No data loss during transition

#### Migration Support
- Backward compatibility during transition
- Migration guide for existing users
- Environment variable mapping documented
- Configuration file transition support

---

## [2025-09-10] - VS Code Extension Context Isolation Fix

### Fixed
- **VS Code Extension Activation**: Fixed extension not activating due to incompatible activation events and TypeScript version conflicts
- **Context Isolation**: Extension now properly isolates memories by context when using `@e^M recall <context-name>`
- **Debug Output**: Added comprehensive debug logging showing CLI command execution, working directory, project context, exit codes, and raw/formatted output
- **TypeScript Compatibility**: Fixed @types/vscode version mismatch with VS Code engine requirements

### Added
- **Popup Notifications**: Added visible activation notifications for debugging extension loading
- **Context Commands**: Support for `@e^M context start <context-name>` to switch active context
- **Enhanced CLI Integration**: Improved command argument construction for proper context filtering

### Changed
- **Activation Event**: Changed from `onChatParticipant:ninaivalaigal` to `onStartupFinished` for better reliability
- **VS Code Engine**: Lowered minimum VS Code version requirement to 1.74.0
- **Server Port**: Updated to use port 13370 to avoid conflicts with other applications

### Technical Details
- Extension now properly detects workspace folder as default context
- CLI commands correctly constructed with `--context` flags
- Debug output shows complete command execution pipeline
- Context switching works for both recall and remember operations
- All changes properly packaged and version controlled

### Testing Verified
- Extension activation with popup notifications ✅
- Context isolation (`@e^M recall CIP-analysis`) ✅  
- Debug output visibility ✅
- Context switching (`@e^M context start CIP-analysis`) ✅
- CLI integration and command construction ✅

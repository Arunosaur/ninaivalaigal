# Changelog

## [2025-09-10] - VS Code Extension Context Isolation Fix

### Fixed
- **VS Code Extension Activation**: Fixed extension not activating due to incompatible activation events and TypeScript version conflicts
- **Context Isolation**: Extension now properly isolates memories by context when using `@mem0 recall <context-name>`
- **Debug Output**: Added comprehensive debug logging showing CLI command execution, working directory, project context, exit codes, and raw/formatted output
- **TypeScript Compatibility**: Fixed @types/vscode version mismatch with VS Code engine requirements

### Added
- **Popup Notifications**: Added visible activation notifications for debugging extension loading
- **Context Commands**: Support for `@mem0 context start <context-name>` to switch active context
- **Enhanced CLI Integration**: Improved command argument construction for proper context filtering

### Changed
- **Activation Event**: Changed from `onChatParticipant:mem0` to `onStartupFinished` for better reliability
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
- Context isolation (`@mem0 recall CIP-analysis`) ✅  
- Debug output visibility ✅
- Context switching (`@mem0 context start CIP-analysis`) ✅
- CLI integration and command construction ✅

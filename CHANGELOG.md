# Changelog

## [1.1.0] - 2025-09-16

### 🔒 Major Security Release: Multipart Upload Hardening

#### Multipart Security Framework
- **Hardened Starlette Adapter**: Stream-time per-part size enforcement with early abort
- **Part Count DoS Prevention**: Configurable limits (default: 256 parts) with HTTP 413 responses
- **Binary Masquerade Detection**: Enhanced magic byte detection (PE, ELF, Mach-O, Java, MP4 offset-aware)
- **Archive Blocking**: ZIP/RAR/7Z prevention on text-only endpoints with HTTP 415 responses
- **UTF-8 Validation**: Strict text encoding with UTF-16 detection and rejection
- **Content-Transfer-Encoding Guards**: Base64/quoted-printable blocking to prevent encoding bypasses

#### Security Controls Matrix
- **DoS Prevention**: Part count and size limits prevent resource exhaustion
- **Code Injection**: Magic byte detection blocks executable uploads  
- **Data Exfiltration**: Archive blocking prevents nested payload smuggling
- **Encoding Attacks**: CTE guards prevent base64/quoted-printable bypasses
- **Unicode Exploits**: Strict UTF-8 validation prevents encoding confusion

#### Filename Security
- **Unicode Normalization**: NFC normalization with path traversal prevention
- **Reserved Name Handling**: Windows reserved name protection (CON, PRN, AUX, etc.)
- **Content-Disposition Parsing**: RFC 5987 encoded filename support
- **Archive Detection**: Comprehensive extension validation with safety checks

#### Testing & Validation
- **Focused Testing Framework**: 6 hardening tests with MultiPartParser mocking
- **27/27 Tests Passing**: Complete security control validation
- **Isolated Unit Tests**: No external dependencies with fast execution
- **CI/CD Integration**: Ready for automated security validation

#### Monitoring & Health
- **Metrics Integration**: Bounded cardinality rejection reasons
- **Health Monitoring**: `/healthz/config` multipart validation
- **Boot Validation**: Production failure detection with actionable messages
- **Debug Support**: Comprehensive logging and troubleshooting guides

#### RBAC Policy Protection
- **Pre-commit Gate**: Prevents unnoticed RBAC matrix changes
- **Baseline Snapshots**: Automated policy drift detection
- **Privilege Escalation Detection**: Security-critical change validation
- **Manual Approval Workflow**: Configurable thresholds with bypass protection

#### Performance Characteristics
- **Stream Processing**: O(1) memory usage regardless of upload size
- **Early Abort**: Violations detected within first few KB
- **Minimal Overhead**: ~1-2ms per part for security validation
- **Bounded Cardinality**: Metrics labels limited to prevent explosion

### Added
- `server/security/multipart/starlette_adapter.py` - Hardened multipart adapter
- `server/utils/filename_sanitizer.py` - Filename security utilities
- `server/health/multipart_config.py` - Health monitoring integration
- `docs/security/MULTIPART_SECURITY_CONSOLIDATED.md` - Complete security guide
- `tests/test_starlette_adapter_hardening.py` - Focused security tests
- `tests/test_filename_sanitizer.py` - Filename safety validation

### Security Improvements
- Stream-time enforcement prevents memory exhaustion attacks
- Part count limiting blocks multipart DoS vectors
- Binary masquerade detection prevents executable smuggling
- Archive blocking on text endpoints prevents payload nesting
- UTF-8 validation with CTE guards prevents encoding bypasses
- RBAC policy snapshot gate prevents privilege drift

### Breaking Changes
- Multipart adapter surface changes require integration updates
- New HTTPException status codes (413, 415) for security violations
- Stricter validation may reject previously accepted uploads

### Migration Guide
- Update multipart handlers to use new `scan_with_starlette` function
- Add health check integration for production monitoring
- Review and adjust size/count limits for your use case
- Test existing uploads against new security controls

---

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

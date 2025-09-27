# SPEC-041: User-Controlled Memory Visibility and Sharing

## 📌 Overview
This SPEC introduces user-controlled visibility and sharing settings for memories, enabling flexible privacy and collaboration. It allows users to mark memories as **private**, **team-visible**, or **public**, and define fine-grained sharing rules per memory or collection.

## 🎯 Goals
- Give users complete control over who can view each memory.
- Enable per-memory sharing with individuals, teams, or entire organizations.
- Support both ephemeral and persistent sharing configurations.

## 🔍 Features
- Visibility Flags: `private`, `team`, `organization`, `public`
- Per-Memory Permissions UI in CLI and web dashboard
- Shareable Link Generation for public or temporary sharing
- Memory Collection Permissions (batch controls)
- Role-Based Access Support (integrates with SPEC-014 RBAC)
- Expiry-based access control (temporary links, session-only visibility)

## 🏗️ Implementation Plan
1. **Memory Schema Updates**: Add `visibility` and `shared_with` fields.
2. **ACL Enforcement**: Middleware and route protection based on visibility settings.
3. **UI Controls**: CLI and UI commands to mark memory visibility.
4. **Public Access API**: Controlled read-only routes for shared memories.
5. **Audit Logging**: Log all visibility changes for compliance.

## 🔐 Security Considerations
- Shared memory access tokens must be scoped and expirable.
- Prevent privilege escalation via forged visibility requests.
- Implement detailed audit trails (future synergy with SPEC-029).

## 🧱 Dependencies
- SPEC-014: RBAC and Permission Framework
- SPEC-029: Audit Logging
- SPEC-017: Memory Collections

## 📁 Location
`specs/041-memory-visibility-sharing/`

## 🗓️ Status
Planned

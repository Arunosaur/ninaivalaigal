# mem0 Project Vision

This document outlines the core vision and architectural principles for the `mem0` project. It serves as a permanent record of our goals to prevent agentic drift and ensure all development work remains aligned with the high-level objectives.

## Core Problem

AI development agents, including this one, lack long-term memory. They get lost in long conversations, forget key decisions, and lose track of the original requirements. This forces the user to constantly repeat themselves and correct the agent's course.

## The Vision

`mem0` is a **simple CCTV-like observer** that helps AI agents stay on target during agentic development. Like a security camera that just watches and records, mem0 quietly observes development activities across terminals, VS Code, JetBrains, and other editors.

### Core Philosophy: Simple Like CCTV

- **Just an Observer**: Silently watches and records when turned on
- **On/Off Switch**: Easy to start/stop - complexities hidden behind the scenes  
- **Multi-Context Support**: Handle multiple projects, but keep user experience minimal
- **AI Agent Helper**: Primary purpose is helping other AI agents maintain context

### Key Pillars

1.  **From Developer to Automation:** The system must capture the iterative, often messy, process of interactive development and transform it into structured, machine-readable data. This data will then be used to automatically generate documentation, reports, and—most importantly—automation scripts (e.g., Ansible playbooks).

2.  **From Individual to Team:** The system must be usable by a single developer on their local machine, but also be deployable as a shared, central service for an entire team. It must support multiple, distinct contexts for different projects and tasks.

3.  **From UI to CLI:** The core of the system will be a headless, API-driven server. All user interfaces (VS Code extensions, JetBrains plugins, terminal clients) will be thin clients that talk to this server. This ensures portability and consistency.

## The Agent's Commitment

I, the AI agent, will read this document before making any significant architectural decisions or starting any major new development task. It will serve as my anchor to ensure I do not deviate from our shared goals.


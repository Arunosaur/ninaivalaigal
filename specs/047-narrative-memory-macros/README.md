---
title: Untitled SPEC
---


# SPEC-047: Narrative Memory Macros (Screen + Voice Capture)

## 🎯 Purpose
Allow users to record *screen + audio walkthroughs* to be stored as narrative memories — useful for demos, training, and procedural storytelling.

## 📦 Features
- Start/stop screen + mic recording from UI or CLI (`e^M demo start`)
- Store demo as memory of type `demo`
- Associate transcription + timeline to memory
- Allow tagging, title, description, author
- Replay via web viewer

## 🛠️ Implementation Plan
- Native screen/audio recorder integration (OBS, browser API, ffmpeg)
- Timeline + audio transcription
- Store alongside other memory objects
- Basic player for UI/CLI replay

## 🧪 Tests
- Record and replay short walkthroughs
- Link to memory contexts
- Upload demo from local file

## 🏁 Output
- Memory `type: "demo"`
- Files stored in object store (video, timeline)
- Replay linkable from CLI/UI

# SPEC-048: Memory Intent Classifier

## 🔍 Purpose
Automatically classify user-recorded memory into **contextual**, **procedural (macro)**, or **narrative** types — reducing user friction.

## 🤖 Strategy
- Use heuristics and ML classification on memory stream
- Prompt user when ambiguity arises (e.g., "Would you like to save this as a macro?")

## 📦 Features
- Memory classification pipeline
- Repetition detection (keyboard/mouse event patterns)
- Audio/narrative signal detection
- CLI feedback suggestions

## 🔄 Workflow
1. User performs an action or triggers `e^M record`
2. System analyzes event pattern
3. If macro/demonstration signals found, prompt user
4. Tag memory appropriately

## 🧪 Tests
- Detect macro behavior across sessions
- Feedback confirmation flow
- Reclassification support

## 🏁 Output
- Auto-tagged memory entries
- Classification metadata (`confidence`, `suggestedType`)
- Optional audit trail

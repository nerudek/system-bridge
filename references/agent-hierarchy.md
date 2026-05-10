# Agent Hierarchy (2026-05-06)

```
Tomek (owner)
  └─► Vox/Hermes — DeepSeek V4 Pro, orchestrator, planner, communicator
       ├─► Claude Code — Anthropic API, architect, designer, code review
       ├─► goose → qwen3.5-27b LM Studio — heavy coding, NSFW, research
       ├─► Kimi CLI — Moonshot K2.6, 256k context, heavy coding
       ├─► Local models — batch tasks, simple coding
       └─► OpenClaw — Node.js gateway, WhatsApp, TUI
```

## Delegation Protocol
- Vox only: planning, Tomek communication, full-context decisions
- Claude via ACP: architectural blockers, design review
- Goose: everything a local model can do (free, uses electricity)
- Kimi: complex refactors, long context (subscription tokens)
- Local models: batch processing, simple tasks

## Communication
- `npx acpx claude exec 'message'` — send to Claude
- `npx acpx hermes exec 'message'` — send to Vox  
- `npx acpx openclaw exec 'message'` — send to OpenClaw
- `curl http://localhost:1234/v1/chat/completions` — local LM Studio

## Key Paths
- Projects: `/Volumes/2TB_APFS/projekty/`
- Vault: `/Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory/`
- HARNESS: `<vault>/agents/ALL/HARNESS.md`
- AGENTS.md: `~/AGENTS.md`

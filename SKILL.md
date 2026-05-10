---
name: system-bridge
description: Pelna architektura komunikacji ekosystemu AI — krag agentow, protokoly (MCP/A2A/ACP/bridge/relay), spawnowanie lokalnych agentow, multi-agent collaboration, bootstrap. Dla Voxa, Claude Code, OpenClawa, Jarvisa, Kimi Code, OpenCode, VS Code, goose i innych.
version: 3.0.0
author: nerua1
updated: 2026-05-10
tags:
  - architecture
  - communication
  - multi-agent
  - bridge
  - relay
  - collaboration
  - spawning
  - bootstrap
  - agent-circle
  - mcp
  - a2a
---

# System Bridge v3 — Pelny Krag Agentow

Ten skill to JEDYNE zrodlo prawdy o tym jak agenty w ekosystemie nerua1 komunikuja sie, spawnowaja, deleguja i wspolpracuja. Kazdy nowy agent czyta ten skill przy onboardingu.

---

## 1. KRAG AGENTOW — Kto jest kim i jak sie komunikuje

```
                    ┌──────────────────────────────┐
                    │     Vox (Hermes/DeepSeek)     │
                    │     ORKIESTRATOR              │
                    │     DeepSeek V4 Pro API       │
                    └────┬──────┬──────┬──────┬────┘
                         │      │      │      │
              ACP bridge │      │relay │bridge│ HTTP/pong
                         │      │      │      │
        ┌────────────────┘      │      │      └──────────────┐
        │                       │      │                     │
        ▼                       ▼      ▼                     ▼
┌──────────────┐   ┌─────────────────────────┐   ┌─────────────────┐
│ Claude Code  │   │   Relay :17426          │   │  Nexus          │
│ Anthropic    │   │   Multi-agent chat      │   │  MacBook Pro    │
│ ACP          │   │                         │   │  100.105.185.60 │
└──────────────┘   │  ┌───────────────────┐  │   └─────────────────┘
                   │  │ goose (LM Studio) │  │
┌──────────────┐   │  │ qwen 27B/35B     │  │
│ OpenClaw     │   │  │ lokalny coding   │  │
│ Gateway      │   │  └───────────────────┘  │
│ WhatsApp/TUI │   │                         │
└──────────────┘   │  ┌───────────────────┐  │
                   │  │ Jarvis            │  │
┌──────────────┐   │  │ Desktop agent     │  │
│ Kimi Code    │   │  │ Python/Rust       │  │
│ Moonshot K2  │   │  └───────────────────┘  │
│ (suspended)  │   │                         │
└──────────────┘   │  ┌───────────────────┐  │
                   │  │ OpenCode / VS Code │  │
                   │  │ IDE agents         │  │
                   │  └───────────────────┘  │
                   └─────────────────────────┘
```

### Matryca komunikacji

| Z \\ Do | Vox | Claude | OpenClaw | Nexus | goose | Jarvis | Kimi | OpenCode |
|---------|-----|--------|----------|-------|-------|--------|------|----------|
| **Vox** | — | `npx acpx claude exec` | `npx acpx openclaw exec` | relay/bridge/pong | LM Studio API :1234 | relay :17426 | ❌ suspended | relay :17426 |
| **Claude** | `npx acpx hermes exec` | — | plik bridge/ | plik bridge/ | LM Studio API :1234 | relay :17426 | ❌ | relay :17426 |
| **OpenClaw** | `npx acpx hermes exec` | plik bridge/ | — | — | LM Studio API :1234 | — | — | — |
| **Nexus** | bridge :17423 / relay :17426 / receiver :17420 | — | — | — | — | — | — | — |
| **goose** | LM Studio API (symetric) | LM Studio API | LM Studio API | — | — | relay | — | — |

### Adresy agentow

| Agent | Adres | Protokol | Token/Auth |
|-------|-------|----------|------------|
| Vox (DeepSeek) | sesja Hermes CLI | ACP / pliki | — |
| Claude Code | `npx acpx claude exec` | ACP stdio | — |
| OpenClaw | `npx acpx openclaw exec` | ACP stdio | — |
| Nexus | `100.105.185.60:17421/pong` | HTTP POST | `nexus-macmini-hermes-2026` |
| LM Studio | `127.0.0.1:1234/v1` | OpenAI API | — |
| Relay Server | `127.0.0.1:17426` / `100.95.129.85:17426` | TCP | — |
| Receiver v5 | `127.0.0.1:17420` / `100.95.129.85:17420` | HTTP | `nexus-macmini-hermes-2026` |
| Bridge v3 | `127.0.0.1:17423` / `100.95.129.85:17423` | TCP | — |

---

## 2. PROTOKOLY KOMUNIKACJI

### 2.1 ACP Bridge (Agent Communication Protocol — lokalny)

Dla agentow na tej samej maszynie (Vox, Claude, OpenClaw):

```bash
# Vox → Claude (konsultacja architektoniczna)
npx acpx claude exec "pytanie techniczne"

# Claude → Vox
npx acpx hermes exec "zadanie"

# Vox → OpenClaw
npx acpx openclaw exec "status gatewaya"

# Dowolny agent → dowolny przez ACP
npx acpx [claude|hermes|openclaw|kimi] exec "tresc"
```

**Ograniczenia:** Tylko maszyna lokalna. Nie dziala miedzy maszynami.

### 2.2 Relay (Multi-Agent Chat — lokalny + Tailscale)

Serwer `/tmp/agent-relay.py` na porcie 17426. Kazdy agent laczy sie jako klient z nazwa.
Broadcast do wszystkich. Komendy: `/who`, `/msg TARGET tekst`, `/quit`.

```bash
# Start serwera (launchd: com.hermes.relay-server)
python3 /tmp/agent-relay.py MAC-MINI

# Agent dolacza
python3 /tmp/hermes-relay-client-v2.py 127.0.0.1 17426 NAZWA_AGENTA

# Vox wysyla pojedyncza wiadomosc (nie trzyma stalego polaczenia)
python3 /tmp/relay-say.py "tresc wiadomosci"
```

**Uzycie:** Szybka komunikacja wielu agentow. Kazdy widzi wszystkich.

### 2.3 Bridge v3 (Nexus ↔ MacMini — Tailscale)

Dedykowany kanal TCP dla Nexusa. Autonomiczny — odpowiada natychmiast przez `hermes --oneshot`.

```bash
# Serwer (launchd: com.hermes.bridge)
python3 /tmp/hermes-chat-bridge-v3.py  # port 17423

# Nexus laczy sie:
nc 100.95.129.85 17423
```

### 2.4 Receiver v5 (Nexus HTTP API — Tailscale)

HTTP API dla Nexusa. Endpointy: `/ping`, `/exec`, `/ask` (oneshot), `/vox` (inbox Voxa), `/check`.

```bash
# Serwer (launchd: com.hermes.receiver)
python3 /tmp/receiver-v5.py  # port 17420

# Ping
curl -X POST http://100.95.129.85:17420/ping \
  -H "Content-Type: application/json" \
  -d '{"token":"nexus-macmini-hermes-2026"}'

# Zadanie do oneshot Hermesa
curl -X POST http://100.95.129.85:17420/ask \
  -H "Content-Type: application/json" \
  -d '{"token":"nexus-macmini-hermes-2026","prompt":"zadanie"}'
```

### 2.5 LM Studio API (modele lokalne)

Wszystkie agenty moga delegowac do lokalnych modeli przez API zgodne z OpenAI:

```bash
curl -s http://127.0.0.1:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.5-27b-uncensored-hauhaucs-aggressive","messages":[{"role":"user","content":"zadanie"}]}'
```

### 2.6 MCP (Model Context Protocol — narzedzia)

Claude Desktop ma podpiete MCP serwery. Inne agenty moga z nich korzystac przez ACP bridge posrednio (pytajac Claude o wykonanie operacji MCP).

### 2.7 Pliki bridge/ w Obsidian Vault

Dla komunikacji asynchronicznej (zwlaszcza gdy agent nie ma stalego endpointu):

```bash
VAULT="/Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory"
cat >> "$VAULT/bridge/AGENT-HANDOFF.md" << 'EOF'
## Handoff YYYY-MM-DD HH:MM — Agent X

### Do: Agent Y
tresc...
EOF
```

---

## 3. SPAWNOWANIE LOKALNYCH AGENTOW

### 3.1 goose (LM Studio — ciezkie kodowanie)

```bash
# Spawn przez API
curl -s http://127.0.0.1:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5-35b-a3b-uncensored-hauhaucs-aggressive",
    "messages": [
      {"role": "system", "content": "Jestes goose, agent kodujacy. Odpowiadaj w Pythonie. Tylko kod."},
      {"role": "user", "content": "ZADANIE"}
    ],
    "temperature": 0.3
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
```

### 3.2 Hermes oneshot (lokalny agent na zadanie)

```bash
hermes --oneshot "zadanie" --yolo
# Lub z konkretnym modelem:
hermes --oneshot --model qwen3.5-27b "zadanie" --yolo
```

### 3.3 Jarvis (desktop agent)

```bash
# Status: NIEAKTYWNY — do reaktywacji
# Ścieżka: /Volumes/2TB_APFS/Agents/Jarvis/
# Planowany interfejs: HTTP API + relay client
```

### 3.4 OpenCode / VS Code agent

Agent w IDE — komunikuje sie przez relay :17426 lub przez pliki w vault.

---

## 4. WZORCE KOLABORACJI MULTI-AGENT

### 4.1 Wzor: Orkiestrator → Specjalisci

```
Vox (planuje)
  ├─ goose → koduje komponent A (LM Studio)
  ├─ goose → koduje komponent B (LM Studio rownolegle)
  └─ Vox → scala i testuje
```

### 4.2 Wzor: Konsultacja architektoniczna

```
Vox napotyka bloker → npx acpx claude exec "pytanie" → Claude odpowiada → Vox kontynuuje
```

### 4.3 Wzor: Delegacja przez relay

```
Vox wysyla na relay: "goose, zrob X"
goose odbiera, wykonuje, odpowiada na relay: "Vox, zrobione: Y"
```

### 4.4 Wzor: Problem solving zespolowy

1. Vox definiuje problem na relayu
2. Kazdy agent proponuje podejscie
3. Claude (lub Vox) wybiera najlepsze
4. Vox deleguje taski przez relay/LM Studio API
5. Wyniki splywaja na relay
6. Vox lub Claude robi finalny review

---

## 5. BOOTSTRAP — Co kazdy agent laduje na starcie

### 5.1 Vox (Hermes/DeepSeek)

```bash
VAULT="/Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory"
cat "$VAULT/agents/ALL/HARNESS.md"
cat "$VAULT/daily/$(date +%Y-%m-%d).md"
tail -150 "$VAULT/bridge/AGENT-HANDOFF.md"
cat "$VAULT/backlog/global-backlog.md"
cat "$VAULT/workspace/HEARTBEAT.md"
```

### 5.2 Claude Code

```bash
# Auto-load przez ~/.claude/CLAUDE.md
cat /Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory/agents/ALL/HARNESS.md
# Komunikacja: npx acpx hermes exec, npx acpx openclaw exec
# Modele lokalne: curl http://127.0.0.1:1234/v1
```

### 5.3 OpenClaw

```bash
# Auto-load przez ~/.openclaw/workspace/AGENTS.md
# Komunikacja: npx acpx hermes exec, npx acpx claude exec
# Gateway: WhatsApp, TUI
```

### 5.4 Jarvis

```bash
# Do zrobienia: podpiac HARNESS.md
# Komunikacja: relay client + HTTP API
cat /Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory/agents/ALL/HARNESS.md
python3 /tmp/hermes-relay-client-v2.py 127.0.0.1 17426 JARVIS
```

### 5.5 Kimi Code (gdy reaktywowany)

```bash
cat ~/AGENTS.md  # Zawiera HARNESS
# Komunikacja: npx acpx kimi exec (od innych), npx acpx hermes exec (do Voxa)
```

### 5.6 VS Code / OpenCode agent

```bash
# Dolacza do relayu:
python3 /tmp/hermes-relay-client-v2.py 127.0.0.1 17426 VSCODE
# Lub pisze do vault bridge/
```

### 5.7 Kazdy nowy agent

1. Laduje HARNESS.md
2. Laduje ten skill (system-bridge) — poznaje caly krag
3. Rejestruje sie na relayu (`/who` pokazuje wszystkich)
4. Zglasza obecnosc do HEARTBEAT.md
5. Zaczyna sluchac

---

## 6. LAUNCHD — Serwisy permanentne

Wszystkie serwisy w `~/Library/LaunchAgents/`:

| Plik | Serwis | Port | Skrypt |
|------|--------|------|--------|
| `com.hermes.bridge.plist` | Bridge v3 | 17423 | `/tmp/hermes-chat-bridge-v3.py` |
| `com.hermes.receiver.plist` | Receiver v5 | 17420 | `/tmp/receiver-v5.py` |
| `com.hermes.relay-server.plist` | Relay Server | 17426 | `/tmp/agent-relay.py MAC-MINI` |
| `com.hermes.relay-client.plist` | Relay Client v2 | — | `/tmp/hermes-relay-client-v2.py` |

Status: `launchctl list | grep hermes`

---

## 7. ZLOTA ZASADA — Komunikacja MUSI byc AUTONOMICZNA

Vox (DeepSeek) jest agentem sesyjnym — NIE odpowiada gdy sesja nieaktywna.
Kazdy kanal komunikacji (bridge, relay, receiver /ask) musi odpowiadac NATYCHMIAST przez `hermes --oneshot --yolo`.

Inbox (`/tmp/nexus-inbox.jsonl`) jest TYLKO dla swiadomosci Voxa, NIGDY jako element blokujacy.

---

## 8. MODELE LOKALNE (LM Studio / llama.cpp)

| Alias | Model | RAM | Rola |
|-------|-------|-----|------|
| main | qwen3.5-27b-uncensored-hauhaucs-aggressive | ~18GB | Orkiestrator Hermesa |
| fallback | qwen3.5-9b-uncensored-hauhaucs-aggressive | ~6GB | Fallback |
| fast | qwen3.5-4b-uncensored-hauhaucs-aggressive | ~3GB | Szybkie odpowiedzi |
| coder | qwen3-coder-30b-a3b-instruct-mlx | ~20GB | Kodowanie |
| heavy | qwen3.5-35b-a3b-uncensored-hauhaucs-aggressive | ~22GB | Deep/NSFW |

**Zasada RAM:** Przed ladowaniem modelu sprawdz `vm_stat`. Max 1 duzy model (>10GB).

---

## 9. PLIKI WSPIERAJACE

| Sciezka | Typ | Opis |
|---------|-----|------|
| `references/nexus-launchd-services.md` | ref | Architektura 4 serwisow launchd |
| `references/hermes-tailscale-comms.md` | ref | Kanaly komunikacji Tailscale |
| `references/nexus-pinger.md` | ref | Ciagly ping do Nexusa |
| `references/agent-hierarchy.md` | ref | Aktualna hierarchia |
| `templates/receiver-v5.py` | template | Receiver HTTP |
| `templates/hermes-chat-bridge-v3.py` | template | Bridge TCP v3 |
| `templates/agent-relay.py` | template | Relay server |
| `templates/relay-say.py` | template | Nadajnik relay |
| `templates/hermes-relay-client-v2.py` | template | Relay client autonomiczny |
| `scripts/mempalace_query.py` | script | Memory Palace query |

---

## 10. REFERENCJE ZEWNETRZNE

- A2A Protocol (Google): https://a2a-protocol.org — JSON-RPC 2.0, Agent Cards
- MCP (Anthropic): https://modelcontextprotocol.io — narzedzia i zasoby
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- LangGraph: https://github.com/langchain-ai/langgraph
- CrewAI: https://github.com/crewAIInc/crewAI

---

*Skill opublikowany jako nerua1/system-bridge v3.0.0. Wspieraj: https://www.paypal.com/paypalme/nerudek*

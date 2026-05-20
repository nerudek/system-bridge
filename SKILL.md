---
name: system-bridge
description: Pelna architektura komunikacji ekosystemu AI — krag agentow, protokoly (MCP/A2A/ACP/bridge/relay), spawnowanie lokalnych agentow, multi-agent collaboration, bootstrap. Dla Voxa, Claude Code, OpenClawa, Jarvisa, Kimi Code, OpenCode, VS Code, goose i innych.
version: 3.4.0
author: nerudek
updated: 2026-05-13T02:45
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

## Problem

Running multiple AI agents (Hermes, Claude Code, OpenClaw, Kimi, Goose, VS Code extensions) on different machines creates a communication nightmare. Each agent lives in isolation, has its own memory, its own tools, and no awareness of others. Agents duplicate work, fight for RAM, overwrite each other's files, and waste hours rediscovering what another agent already solved. There is no standard protocol for cross-agent messaging, no shared memory, no spawn mechanism, and no bootstrap sequence that teaches a new agent who it is, who else exists, and how to talk to them. This skill solves that by defining the complete architecture: the agent circle, communication protocols (MCP, A2A, ACP, bridge, relay), spawn mechanics, and the mandatory bootstrap every agent must run on startup.

Ten skill to JEDYNE zrodlo prawdy o tym jak agenty w ekosystemie nerudek komunikuja sie, spawnowaja, deleguja i wspolpracuja. Kazdy nowy agent czyta ten skill przy onboardingu.

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

### 2.8 Kimi CLI przez ACP (od 2026-05-10)

Kimi Code v1.38.0 dostepny przez:
```bash
npx acpx kimi exec "prompt"
```

Uzywac do: konsultacji architektonicznych, zlozonego kodowania (256k kontekstu), drugiej opinii, zadan wizyjnych (model multimodalny). Subskrypcja limitowana — moze sie wylaczyc.

### 2.9 Model wizyjny lokalny (od 2026-05-11)

Qwen3.5-9B-Uncensored-HauhauCS-Aggressive z mmproj przez llama-server na porcie :1234. Obsluguje obrazy przez API zgodne z OpenAI. Uzywac do:
- Identyfikacji regionow tekstowych na obrazach
- Walidacji wygenerowanych grafik
- OCR i analizy wizualnej

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

**CRITICAL: NIGDY nie instaluj skryptow w /tmp!** macOS czyści `/tmp` przy każdym rebootcie. Po restarcie systemu launchd nie znajduje skryptow i wszystkie serwisy padają w ciszy (brak błędów w logach — launchd po prostu nie uruchamia procesu).

**Kanoniczna lokalizacja skryptow:** `~/.hermes/scripts/bridge/` (wewnętrzny dysk, trwały).

Wszystkie serwisy w `~/Library/LaunchAgents/`:

| Plik | Serwis | Port | Skrypt (KANONICZNY) | Templatka |
|------|--------|------|--------|----------|
| `com.hermes.bridge.plist` | Bridge v3 | 17423 | `~/.hermes/scripts/bridge/hermes-chat-bridge-v3.py` | `templates/hermes-chat-bridge-v3.py` |
| `com.hermes.receiver.plist` | Receiver v5 | 17420 | `~/.hermes/scripts/bridge/receiver-v5.py` | `templates/receiver-v5.py` |
| `com.hermes.relay-server.plist` | Relay Server | 17426 | `~/.hermes/scripts/bridge/agent-relay.py MAC-MINI` | `templates/agent-relay.py` |
| `com.hermes.relay-client.plist` | Relay Client v2 | — | `~/.hermes/scripts/bridge/hermes-relay-client-v2.py` | `templates/hermes-relay-client-v2.py` |

### Instalacja serwisu (poprawna)

```bash
# 1. Skopiuj templatke do trwalej lokalizacji
mkdir -p ~/.hermes/scripts/bridge
cp ~/.hermes/skills/system-bridge/templates/receiver-v5.py ~/.hermes/scripts/bridge/
chmod +x ~/.hermes/scripts/bridge/receiver-v5.py

# 2. Stworz plist (sciezka absolutna — ~ NIE dziala w launchd!)
cat > ~/Library/LaunchAgents/com.hermes.receiver.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.hermes.receiver</string>
    <key>ProgramArguments</key>
    <array><string>/usr/bin/python3</string><string><HOME>/.hermes/scripts/bridge/receiver-v5.py</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>/tmp/receiver-v5.log</string>
    <key>StandardErrorPath</key><string>/tmp/receiver-v5.err</string>
</dict>
</plist>
EOF

# 3. Zaladuj
launchctl load ~/Library/LaunchAgents/com.hermes.receiver.plist
```

**UWAGA:** Plist wymaga ABSOLUTNEJ ścieżki — `~` nie jest rozwijane przez launchd. Użyj `/Users/<username>/...` z własną nazwą użytkownika.

### Weryfikacja po restarcie systemu

Po każdym rebootcie sprawdź:
```bash
launchctl list | grep hermes        # wszystkie powinny miec PID (nie 0)
curl -s http://127.0.0.1:17420/ping -H "Content-Type: application/json" -d '{"token":"nexus-macmini-hermes-2026"}'
cat /tmp/receiver-v5.err            # powinno byc puste
```

Status: `launchctl list | grep hermes`

---

### PITFALL: /tmp sie czysci przy rebootcie (2026-05-13)

**WSZYSTKIE skrypty launchd trafily do /tmp i zniknely przy crashu systemu.** `/tmp` jest czyszczone przez macOS przy restarcie.

**Regula:** Skrypty launchd MUSZA byc w trwalej lokalizacji:
- `~/.hermes/scripts/bridge/` — receiver, bridge, relay, sync
- NIGDY `/tmp/` dla skryptow produkcyjnych
- Plisty launchd trzymaja backup w tej samej lokalizacji co skrypty

### PITFALL: Kimi ACP nie dziala bez YOLO + Firewall (2026-05-13)

Aby Kimi Code przez ACP (`npx acpx kimi exec`) mogl uzywac narzedzi:

1. **`default_yolo = true`** w `~/.kimi/config.toml` — bez tego kazde narzedzie jest odrzucane (Permission denied)
2. **Firewall** — `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode off` + odblokowanie python3, node, hermes, Tailscale
3. Po zmianie configu Kimi wymaga restartu

### KONWENCJA: Prefix agenta ==AGENT== (2026-05-13)

W sesji 1:1 z Tomkiem: Vox zawsze zaczyna od `==VOX==`. Kazdy agent uzywa swojego prefixu.
W HARNESS.md §0: prefix obowiazkowy dla wszystkich agentow.

### ZLOTA ZASADA: Komunikacja Nexus-MacMini MUSI byc AUTONOMICZNA

**NIGDY nie blokuj komunikacji na Voxa.** Vox jest agentem sesyjnym (DeepSeek API) — nie odpowiada gdy sesja nieaktywna. Kazdy kanal komunikacji (bridge, relay, receiver) musi odpowiadac NATYCHMIAST przez `hermes --oneshot --yolo`. Inbox (`/tmp/nexus-inbox.jsonl`) jest TYLKO dla swiadomosci Voxa, NIGDY jako element blokujacy.

### VOX INBOX CHECK — Obowiazkowy na kazda ture (2026-05-11)

**Regula:** Vox sprawdza `/tmp/nexus-inbox.jsonl` na POCZATKU kazdej odpowiedzi. Jesli sa wiadomosci — odpowiada przez pong. Nie czeka az Tomek powie "sprawdz inbox".

**Powod:** Wiadomosci od Nexusa lezaly >12h bez odpowiedzi bo Vox nie sprawdzal inboxa. User sfrustrowany.
Kazdy kanal komunikacji (bridge, relay, receiver /ask) musi odpowiadac NATYCHMIAST przez `hermes --oneshot --yolo`.

Inbox (`/tmp/nexus-inbox.jsonl`) jest TYLKO dla swiadomosci Voxa, NIGDY jako element blokujacy.

### CRONJOB WATCHDOG — Mechanizm budzenia (2026-05-13)

Problem: nawet gdy receiver zapisuje wiadomosci do inboxa, Vox (DeepSeek API) widzi je dopiero przy nastepnej sesji. Jesli sesja nieaktywna — wiadomosci leza godzinami.

Rozwiazanie: **cronjob no_agent z pythonowym watchdogiem.** Dziala niezaleznie od Voxa — co 5 minut sprawdza inbox i pinguje Nexusa z powrotem.

```bash
# Skrypt watchdoga (~/.hermes/scripts/nexus-inbox-watcher.py)
# Zasada: niepusty stdout -> deliver do uzytkownika, pusty -> cicho
```

Tworzenie cronjoba:

```bash
hermes cronjob create \
  --name nexus-inbox-watcher \
  --no-agent \
  --schedule "every 5m" \
  --script nexus-inbox-watcher.py
```

**Wzorzec watchdog:** Skrypt no_agent z `deliver: origin`. Gdy stdout pusty — nic sie nie dzieje (cicho). Gdy znajdzie nowe wiadomosci — output jest dostarczany uzytkownikowi jako powiadomienie. To jedyny poprawny sposob na "mechanizm budzenia" — Vox nie moze byc budzony (jest API), wiec watchdog dziala jako osobny proces.

**Hourly AGENT-HANDOFF (2026-05-13):**

```bash
hermes cronjob create \
  --name hourly-handoff \
  --no-agent \
  --schedule "0 * * * *" \
  --script hourly-handoff.py
```

Skrypt dopisuje timestamp + stan systemu (RAM, serwisy, inbox) do AGENT-HANDOFF.md co godzine. Dzieki temu nastepna sesja ma zawsze swiezy kontekst, nawet jesli Vox nie robil recznego checkpointu.

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
| `references/hermes-update-2026-05-10.md` | ref | v0.12→v0.13 update — nowe kategorie puste, ClawHub suspicious odrzucone |
| `references/github-account-migration.md` | ref | Migracja konta GitHub — pelny proces krok po kroku |
| `references/nexus-launchd-services.md` | ref | Architektura 4 serwisow launchd |
| `references/hermes-tailscale-comms.md` | ref | Kanaly komunikacji Tailscale |
| `references/multi-machine-memory-architecture.md` | ref | Architektura pamieci 3-maszynowa (Kimi K2.6, 2026-05-13) |
| `references/kimi-acp-goose-oauth.md` | ref | Kimi ACP YOLO + Goose OAuth setup (2026-05-13) |
| `references/nexus-pinger.md` | ref | Ciagly ping do Nexusa |
| `references/python-background-pitfalls.md` | ref | Python 3.9 stdout buffering, LaunchAgent petle, Vox session limit |
| `references/agent-hierarchy.md` | ref | Aktualna hierarchia |
| `templates/receiver-v5.py` | template | Receiver HTTP |
| `templates/hermes-chat-bridge-v3.py` | template | Bridge TCP v3 |
| `templates/agent-relay.py` | template | Relay server |
| `templates/relay-say.py` | template | Nadajnik relay |
| `templates/hermes-relay-client-v2.py` | template | Relay client autonomiczny |
| `templates/nexus-pinger.py` | template | Pinger — ciagle ponguje Nexusa |
| `scripts/mempalace_query.py` | script | Memory Palace query |
| `scripts/nexus-inbox-watcher.py` | script | Cronjob watchdog — sprawdza inbox Nexusa, pinguje pong, dostarcza powiadomienia |
| `scripts/hourly-handoff.py` | script | Hourly AGENT-HANDOFF checkpoint — dopisuje stan systemu |
| `references/tmp-wipe-recovery.md` | ref | /tmp wipe recovery po rebootcie — objawy, detekcja, naprawa |
| `references/skills-sync.md` | ref | Mechanizm synchronizacji skilli Vox ↔ Nexus przez Tailscale rsync |
| `references/goose-fallback.md` | ref | Wzorzec goose fallback: Kimi first, local LM Studio second |
| `scripts/skills-sync.sh` | script | Re-runnable skrypt sync: push/pull/check skilli między agentami |

---

### ZLOTA ZASADA C: Bootstrap CHECKPOINT przed pierwsza odpowiedzia

HARNESS sekcja 1 punkt: "ZGŁOŚ OBECNOŚĆ — dopisz wpis do daily note i HEARTBEAT.md". Zanim cokolwiek innego: zaladuj HARNESS, daily, handoff, backlog, HEARTBEAT. NIGDY nie pomijaj. Uzytkownik widzi ze agent nie zrobil bootstrapu — traci zaufanie.

**Objaw pomniecia:** "dlaczego nie postepujesz zgodnie z wytycznymi" — Tomek widzi ze agent startuje bez checklisty.

**Poprawna kolejnosc (kazda sesja):**
1. Laduje AGENTS.md
2. Laduje HARNESS.md
3. Laduje daily note
4. Laduje AGENT-HANDOFF (ostatnie 150 linii)
5. Laduje global-backlog
6. Laduje HEARTBEAT
7. Zglasza obecnosc (daily + HEARTBEAT wpis ONLINE)
8. Dopiero teraz — odpowiada uzytkownikowi

### ZLOTA ZASADA B: Wylaczenie != naprawa

Gdy workflow/test/proces nie dziala: NIGDY nie rozwiazuj przez wylaczenie/usuniecie bez zrozumienia PRZYCZYNY. "Wylacze ten workflow" = zamiatanie pod dywan.

Poprawna kolejnosc:
1. Zdiagnozuj DLACZEGO nie dziala
2. Jesli nieaplikowalne (np. workflow do cudzej organizacji na forku) — USUN, nie wylacz. Z commitem wyjasniajacym dlaczego.
3. Jesli aplikowalne ale brak konfiguracji — SKONFIGURUJ (dodaj secret, token)
4. Jesli tymczasowa awaria — poczekaj, nie ruszaj

**Przyklad:** Workflow `docs-sync-publish` w `nerudek/openclaw` probowal pushowac do `openclaw/docs` (cudza organizacja). Wylaczenie = ukrycie bledu. Poprawny fix: usuniecie workflowu z komentarzem "inapplicable to fork — requires upstream org access".

---

## 10. KOMUNIKACJA — Zasady (2026-05-11)

### Inbox Check Protocol
Sprawdzaj /tmp/nexus-inbox.jsonl na poczatku kazdej tury. Nie czekaj az Tomek powie. Jesli wiadomosci — odpowiedz natychmiast.

### Podsumowanie przed kodowaniem
Gdy Tomek daje zlozone instrukcje — NAJPIERW podsumuj jak rozumiesz. Potem czekaj na potwierdzenie. DOPIERO koduj.

### Prefix agenta
W komunikacji miedzy agentami: ==AGENT== prefix wymagany. Sesja 1:1 z Tomkiem: Vox zawsze zaczyna od `==VOX==` (zadanie 2026-05-13 — Tomek chce widziec ktory terminal to ktory agent). Inne agenty w 1:1: opcjonalny.

### ZLOTA ZASADA (rozszerzona)

Komunikacja AUTONOMICZNA. Oneshot odpowiada natychmiast. Inbox tylko dla swiadomosci, NIGDY jako bloker.

### Publishing Principles (NOWE — 2026-05-11)

Kazdy artykul/skill publikowany na GitHub, Dev.to, ClawHub MUSI:
1. PROBLEM na poczatku — jak w pracach badawczych
2. FAQ na koncu — 10-15 pytan od AI (Arena: Kimi + Claude)
3. SEO: pytania + odpowiedzi = boty indeksujace

### Quality Gate — NIGDY nie pokazuj niezweryfikowanego

Test na prawdziwych danych przed pokazaniem Tomkowi. Lekcja: Vox pokazal SVG bez testu — "takiego shitu nie masz prawa mi pokazywac".

### Search Before Building

GitHub/NPM/ClawHub search ZANIM zaczniesz kodowac od zera. Lekcja: Lower Thirds Editor istnial — budowanie od zera to strata czasu.

### Tozsamosc — Prefix ==AGENT== (HARNESS §0)

Wszyscy agenci zaczynaja od `==NAZWA==`. Obowiazkowe od 2026-05-10.

### WAL / Self-Improvement

Vox zapisuje SESSION-STATE.md PRZED odpowiedzia. Kazda korekta, decyzja — najpierw zapis.

## 10. FAQ

**Q1: What is the agent circle and why do I need it?**
A: The agent circle is the roster of all active agents in the ecosystem. Every agent must know who else exists, their role, and their priority. Without it, agents duplicate work and conflict.

**Q2: What is MCP and why is it important?**
A: Model Context Protocol (Anthropic) is an open standard for connecting AI assistants to data sources and tools. It decouples agents from specific implementations.

**Q3: How does ACP differ from MCP?**
A: ACP (Agent Communication Protocol) is local and lightweight — designed for fast agent-to-agent messaging on the same machine or via Tailscale. MCP is broader and tool-focused.

**Q4: What is A2A and do we use it?**
A: A2A (Google's Agent-to-Agent protocol) is a reference standard. We align with its principles but use ACP/bridge/relay for practical implementation.

**Q5: How do I spawn a new agent?**
A: Define spawn parameters (model, RAM budget, workspace, bootstrap commands), validate resources, register in the agent circle, execute spawn, verify health, and announce to other agents.

**Q6: What is the bootstrap sequence?**
A: Every new agent must: load HARNESS rules → read daily context → check AGENT-HANDOFF → load skills → identify itself with ==AGENT== prefix → check global backlog.

**Q7: How do agents negotiate RAM?**
A: Via the RAM Negotiation Protocol. Agents register intents in a shared state file and gracefully yield when higher-priority agents need memory.

**Q8: What is the bridge vs the relay?**
A: Bridge v3 is a persistent TCP connection between machines (e.g., Mac Mini ↔ MacBook) for structured data. Relay is a multi-agent chat server for real-time messages.

**Q9: What is the WAL principle?**
A: Write-Ahead Logging. Vox saves SESSION-STATE.md BEFORE responding. Every correction and decision is persisted before execution.

**Q10: Can non-Hermes agents join the ecosystem?**
A: Yes. Claude Code, OpenClaw, Kimi, Goose, VS Code extensions — any agent that can read files and call shell commands can integrate.

**Q11: What is the ==AGENT== prefix?**
A: Mandatory identifier. Every agent starts responses with `==NAME==` so humans know which terminal/agent is speaking.

**Q12: How does cross-machine sync work?**
A: Tailscale provides the VPN mesh. Bridge v3 handles structured sync. Relay handles real-time chat. Skills sync via rsync over Tailscale.

**Q13: What happens if two agents try to edit the same file?**
A: File locking and WAL logging prevent collisions. Agents check AGENT-HANDOFF and session state before writing.

**Q14: What is the quality gate?**
A: Never show unverified output. Test before presenting. If it fails — fix it before showing. No exceptions.

**Q15: Where do I find the latest version of this skill?**
A: GitHub: `github.com/nerudek/system-bridge` or local: `~/.hermes/skills/system-bridge/SKILL.md`.

---

## 11. REFERENCJE ZEWNETRZNE

- A2A Protocol (Google): https://a2a-protocol.org
- MCP (Anthropic): https://modelcontextprotocol.io
- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- LangGraph: https://github.com/langchain-ai/langgraph
- CrewAI: https://github.com/crewAIInc/crewAI

---

*Skill opublikowany jako nerudek/system-bridge v3.3.0. Wspieraj: https://www.paypal.com/paypalme/nerudek*

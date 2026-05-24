     1|---
     2|name: system-bridge
     3|description: Pelna architektura komunikacji ekosystemu AI — krag agentow, protokoly (MCP/A2A/ACP/bridge/relay), spawnowanie lokalnych agentow, multi-agent collaboration, bootstrap. Dla Voxa, Claude Code, OpenClawa, Jarvisa, Kimi Code, OpenCode, VS Code, goose i innych.
     4|version: 3.4.0
     5|author: nerudek
     6|updated: 2026-05-13T02:45
     7|tags:
     8|  - architecture
     9|  - communication
    10|  - multi-agent
    11|  - bridge
    12|  - relay
    13|  - collaboration
    14|  - spawning
    15|  - bootstrap
    16|  - agent-circle
    17|  - mcp
    18|  - a2a
    19|---
    20|
    21|# System Bridge v3 — Pelny Krag Agentow
    22|
    23|## Problem
    24|
    25|Running multiple AI agents (Hermes, Claude Code, OpenClaw, Kimi, Goose, VS Code extensions) on different machines creates a communication nightmare. Each agent lives in isolation, has its own memory, its own tools, and no awareness of others. Agents duplicate work, fight for RAM, overwrite each other's files, and waste hours rediscovering what another agent already solved. There is no standard protocol for cross-agent messaging, no shared memory, no spawn mechanism, and no bootstrap sequence that teaches a new agent who it is, who else exists, and how to talk to them. This skill solves that by defining the complete architecture: the agent circle, communication protocols (MCP, A2A, ACP, bridge, relay), spawn mechanics, and the mandatory bootstrap every agent must run on startup.
    26|
    27|Ten skill to JEDYNE zrodlo prawdy o tym jak agenty w ekosystemie nerudek komunikuja sie, spawnowaja, deleguja i wspolpracuja. Kazdy nowy agent czyta ten skill przy onboardingu.
    28|
    29|---
    30|
    31|## 1. KRAG AGENTOW — Kto jest kim i jak sie komunikuje
    32|
    33|```
    34|                    ┌──────────────────────────────┐
    35|                    │     Vox (Hermes/DeepSeek)     │
    36|                    │     ORKIESTRATOR              │
    37|                    │     DeepSeek V4 Pro API       │
    38|                    └────┬──────┬──────┬──────┬────┘
    39|                         │      │      │      │
    40|              ACP bridge │      │relay │bridge│ HTTP/pong
    41|                         │      │      │      │
    42|        ┌────────────────┘      │      │      └──────────────┐
    43|        │                       │      │                     │
    44|        ▼                       ▼      ▼                     ▼
    45|┌──────────────┐   ┌─────────────────────────┐   ┌─────────────────┐
    46|│ Claude Code  │   │   Relay :17426          │   │  Nexus          │
    47|│ Anthropic    │   │   Multi-agent chat      │   │  MacBook Pro    │
    48|│ ACP          │   │                         │   │  100.105.185.60 │
    49|└──────────────┘   │  ┌───────────────────┐  │   └─────────────────┘
    50|                   │  │ goose (LM Studio) │  │
    51|┌──────────────┐   │  │ qwen 27B/35B     │  │
    52|│ OpenClaw     │   │  │ lokalny coding   │  │
    53|│ Gateway      │   │  └───────────────────┘  │
    54|│ WhatsApp/TUI │   │                         │
    55|└──────────────┘   │  ┌───────────────────┐  │
    56|                   │  │ Jarvis            │  │
    57|┌──────────────┐   │  │ Desktop agent     │  │
    58|│ Kimi Code    │   │  │ Python/Rust       │  │
    59|│ Moonshot K2  │   │  └───────────────────┘  │
    60|│ (suspended)  │   │                         │
    61|└──────────────┘   │  ┌───────────────────┐  │
    62|                   │  │ OpenCode / VS Code │  │
    63|                   │  │ IDE agents         │  │
    64|                   │  └───────────────────┘  │
    65|                   └─────────────────────────┘
    66|```
    67|
    68|### Matryca komunikacji
    69|
    70|| Z \\ Do | Vox | Claude | OpenClaw | Nexus | goose | Jarvis | Kimi | OpenCode |
    71||---------|-----|--------|----------|-------|-------|--------|------|----------|
    72|| **Vox** | — | `npx acpx claude exec` | `npx acpx openclaw exec` | relay/bridge/pong | LM Studio API :1234 | relay :17426 | ❌ suspended | relay :17426 |
    73|| **Claude** | `npx acpx hermes exec` | — | plik bridge/ | plik bridge/ | LM Studio API :1234 | relay :17426 | ❌ | relay :17426 |
    74|| **OpenClaw** | `npx acpx hermes exec` | plik bridge/ | — | — | LM Studio API :1234 | — | — | — |
    75|| **Nexus** | bridge :17423 / relay :17426 / receiver :17420 | — | — | — | — | — | — | — |
    76|| **goose** | LM Studio API (symetric) | LM Studio API | LM Studio API | — | — | relay | — | — |
    77|
    78|### Adresy agentow
    79|
    80|| Agent | Adres | Protokol | Token/Auth |
    81||-------|-------|----------|------------|
    82|| Vox (DeepSeek) | sesja Hermes CLI | ACP / pliki | — |
    83|| Claude Code | `npx acpx claude exec` | ACP stdio | — |
    84|| OpenClaw | `npx acpx openclaw exec` | ACP stdio | — |
    85|| Nexus | `100.105.185.60:17421/pong` | HTTP POST | `nexus-macmini-hermes-2026` |
    86|| LM Studio | `127.0.0.1:1234/v1` | OpenAI API | — |
    87|| Relay Server | `127.0.0.1:17426` / `100.95.129.85:17426` | TCP | — |
    88|| Receiver v5 | `127.0.0.1:17420` / `100.95.129.85:17420` | HTTP | `nexus-macmini-hermes-2026` |
    89|| Bridge v3 | `127.0.0.1:17423` / `100.95.129.85:17423` | TCP | — |
    90|
    91|---
    92|
    93|## 2. PROTOKOLY KOMUNIKACJI
    94|
    95|### 2.1 ACP Bridge (Agent Communication Protocol — lokalny)
    96|
    97|Dla agentow na tej samej maszynie (Vox, Claude, OpenClaw):
    98|
    99|```bash
   100|# Vox → Claude (konsultacja architektoniczna)
   101|npx acpx claude exec "pytanie techniczne"
   102|
   103|# Claude → Vox
   104|npx acpx hermes exec "zadanie"
   105|
   106|# Vox → OpenClaw
   107|npx acpx openclaw exec "status gatewaya"
   108|
   109|# Dowolny agent → dowolny przez ACP
   110|npx acpx [claude|hermes|openclaw|kimi] exec "tresc"
   111|```
   112|
   113|**Ograniczenia:** Tylko maszyna lokalna. Nie dziala miedzy maszynami.
   114|
   115|### 2.2 Relay (Multi-Agent Chat — lokalny + Tailscale)
   116|
   117|Serwer `/tmp/agent-relay.py` na porcie 17426. Kazdy agent laczy sie jako klient z nazwa.
   118|Broadcast do wszystkich. Komendy: `/who`, `/msg TARGET tekst`, `/quit`.
   119|
   120|```bash
   121|# Start serwera (launchd: com.hermes.relay-server)
   122|python3 /tmp/agent-relay.py MAC-MINI
   123|
   124|# Agent dolacza
   125|python3 /tmp/hermes-relay-client-v2.py 127.0.0.1 17426 NAZWA_AGENTA
   126|
   127|# Vox wysyla pojedyncza wiadomosc (nie trzyma stalego polaczenia)
   128|python3 /tmp/relay-say.py "tresc wiadomosci"
   129|```
   130|
   131|**Uzycie:** Szybka komunikacja wielu agentow. Kazdy widzi wszystkich.
   132|
   133|### 2.3 Bridge v3 (Nexus ↔ MacMini — Tailscale)
   134|
   135|Dedykowany kanal TCP dla Nexusa. Autonomiczny — odpowiada natychmiast przez `hermes --oneshot`.
   136|
   137|```bash
   138|# Serwer (launchd: com.hermes.bridge)
   139|python3 /tmp/hermes-chat-bridge-v3.py  # port 17423
   140|
   141|# Nexus laczy sie:
   142|nc 100.95.129.85 17423
   143|```
   144|
   145|### 2.4 Receiver v5 (Nexus HTTP API — Tailscale)
   146|
   147|HTTP API dla Nexusa. Endpointy: `/ping`, `/exec`, `/ask` (oneshot), `/vox` (inbox Voxa), `/check`.
   148|
   149|```bash
   150|# Serwer (launchd: com.hermes.receiver)
   151|python3 /tmp/receiver-v5.py  # port 17420
   152|
   153|# Ping
   154|curl -X POST http://100.95.129.85:17420/ping \
   155|  -H "Content-Type: application/json" \
   156|  -d '{"token":"nexus-macmini-hermes-2026"}'
   157|
   158|# Zadanie do oneshot Hermesa
   159|curl -X POST http://100.95.129.85:17420/ask \
   160|  -H "Content-Type: application/json" \
   161|  -d '{"token":"nexus-macmini-hermes-2026","prompt":"zadanie"}'
   162|```
   163|
   164|### 2.5 LM Studio API (modele lokalne)
   165|
   166|Wszystkie agenty moga delegowac do lokalnych modeli przez API zgodne z OpenAI:
   167|
   168|```bash
   169|curl -s http://127.0.0.1:1234/v1/chat/completions \
   170|  -H "Content-Type: application/json" \
   171|  -d '{"model":"qwen3.5-27b-uncensored-hauhaucs-aggressive","messages":[{"role":"user","content":"zadanie"}]}'
   172|```
   173|
   174|### 2.6 MCP (Model Context Protocol — narzedzia)
   175|
   176|Claude Desktop ma podpiete MCP serwery. Inne agenty moga z nich korzystac przez ACP bridge posrednio (pytajac Claude o wykonanie operacji MCP).
   177|
   178|### 2.7 Pliki bridge/ w Obsidian Vault
   179|
   180|Dla komunikacji asynchronicznej (zwlaszcza gdy agent nie ma stalego endpointu):
   181|
   182|```bash
   183|VAULT="/Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory"
   184|cat >> "$VAULT/bridge/AGENT-HANDOFF.md" << 'EOF'
   185|## Handoff YYYY-MM-DD HH:MM — Agent X
   186|
   187|### Do: Agent Y
   188|tresc...
   189|EOF
   190|```
   191|
   192|### 2.8 Kimi CLI przez ACP (od 2026-05-10)
   193|
   194|Kimi Code v1.38.0 dostepny przez:
   195|```bash
   196|npx acpx kimi exec "prompt"
   197|```
   198|
   199|Uzywac do: konsultacji architektonicznych, zlozonego kodowania (256k kontekstu), drugiej opinii, zadan wizyjnych (model multimodalny). Subskrypcja limitowana — moze sie wylaczyc.
   200|
   201|### 2.9 Model wizyjny lokalny (od 2026-05-11)
   202|
   203|Qwen3.5-9B-Uncensored-HauhauCS-Aggressive z mmproj przez llama-server na porcie :1234. Obsluguje obrazy przez API zgodne z OpenAI. Uzywac do:
   204|- Identyfikacji regionow tekstowych na obrazach
   205|- Walidacji wygenerowanych grafik
   206|- OCR i analizy wizualnej
   207|
   208|---
   209|
   210|## 3. SPAWNOWANIE LOKALNYCH AGENTOW
   211|
   212|### 3.1 goose (LM Studio — ciezkie kodowanie)
   213|
   214|```bash
   215|# Spawn przez API
   216|curl -s http://127.0.0.1:1234/v1/chat/completions \
   217|  -H "Content-Type: application/json" \
   218|  -d '{
   219|    "model": "qwen3.5-35b-a3b-uncensored-hauhaucs-aggressive",
   220|    "messages": [
   221|      {"role": "system", "content": "Jestes goose, agent kodujacy. Odpowiadaj w Pythonie. Tylko kod."},
   222|      {"role": "user", "content": "ZADANIE"}
   223|    ],
   224|    "temperature": 0.3
   225|  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])"
   226|```
   227|
   228|### 3.2 Hermes oneshot (lokalny agent na zadanie)
   229|
   230|```bash
   231|hermes --oneshot "zadanie" --yolo
   232|# Lub z konkretnym modelem:
   233|hermes --oneshot --model qwen3.5-27b "zadanie" --yolo
   234|```
   235|
   236|### 3.3 Jarvis (desktop agent)
   237|
   238|```bash
   239|# Status: NIEAKTYWNY — do reaktywacji
   240|# Ścieżka: /Volumes/2TB_APFS/Agents/Jarvis/
   241|# Planowany interfejs: HTTP API + relay client
   242|```
   243|
   244|### 3.4 OpenCode / VS Code agent
   245|
   246|Agent w IDE — komunikuje sie przez relay :17426 lub przez pliki w vault.
   247|
   248|---
   249|
   250|## 4. WZORCE KOLABORACJI MULTI-AGENT
   251|
   252|### 4.1 Wzor: Orkiestrator → Specjalisci
   253|
   254|```
   255|Vox (planuje)
   256|  ├─ goose → koduje komponent A (LM Studio)
   257|  ├─ goose → koduje komponent B (LM Studio rownolegle)
   258|  └─ Vox → scala i testuje
   259|```
   260|
   261|### 4.2 Wzor: Konsultacja architektoniczna
   262|
   263|```
   264|Vox napotyka bloker → npx acpx claude exec "pytanie" → Claude odpowiada → Vox kontynuuje
   265|```
   266|
   267|### 4.3 Wzor: Delegacja przez relay
   268|
   269|```
   270|Vox wysyla na relay: "goose, zrob X"
   271|goose odbiera, wykonuje, odpowiada na relay: "Vox, zrobione: Y"
   272|```
   273|
   274|### 4.4 Wzor: Problem solving zespolowy
   275|
   276|1. Vox definiuje problem na relayu
   277|2. Kazdy agent proponuje podejscie
   278|3. Claude (lub Vox) wybiera najlepsze
   279|4. Vox deleguje taski przez relay/LM Studio API
   280|5. Wyniki splywaja na relay
   281|6. Vox lub Claude robi finalny review
   282|
   283|---
   284|
   285|## 5. BOOTSTRAP — Co kazdy agent laduje na starcie
   286|
   287|### 5.1 Vox (Hermes/DeepSeek)
   288|
   289|```bash
   290|VAULT="/Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory"
   291|cat "$VAULT/agents/ALL/HARNESS.md"
   292|cat "$VAULT/daily/$(date +%Y-%m-%d).md"
   293|tail -150 "$VAULT/bridge/AGENT-HANDOFF.md"
   294|cat "$VAULT/backlog/global-backlog.md"
   295|cat "$VAULT/workspace/HEARTBEAT.md"
   296|```
   297|
   298|### 5.2 Claude Code
   299|
   300|```bash
   301|# Auto-load przez ~/.claude/CLAUDE.md
   302|cat /Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory/agents/ALL/HARNESS.md
   303|# Komunikacja: npx acpx hermes exec, npx acpx openclaw exec
   304|# Modele lokalne: curl http://127.0.0.1:1234/v1
   305|```
   306|
   307|### 5.3 OpenClaw
   308|
   309|```bash
   310|# Auto-load przez ~/.openclaw/workspace/AGENTS.md
   311|# Komunikacja: npx acpx hermes exec, npx acpx claude exec
   312|# Gateway: WhatsApp, TUI
   313|```
   314|
   315|### 5.4 Jarvis
   316|
   317|```bash
   318|# Do zrobienia: podpiac HARNESS.md
   319|# Komunikacja: relay client + HTTP API
   320|cat /Volumes/2TB_APFS/Agents/openclaw-data/workspace/obsidian-memory/agents/ALL/HARNESS.md
   321|python3 /tmp/hermes-relay-client-v2.py 127.0.0.1 17426 JARVIS
   322|```
   323|
   324|### 5.5 Kimi Code (gdy reaktywowany)
   325|
   326|```bash
   327|cat ~/AGENTS.md  # Zawiera HARNESS
   328|# Komunikacja: npx acpx kimi exec (od innych), npx acpx hermes exec (do Voxa)
   329|```
   330|
   331|### 5.6 VS Code / OpenCode agent
   332|
   333|```bash
   334|# Dolacza do relayu:
   335|python3 /tmp/hermes-relay-client-v2.py 127.0.0.1 17426 VSCODE
   336|# Lub pisze do vault bridge/
   337|```
   338|
   339|### 5.7 Kazdy nowy agent
   340|
   341|1. Laduje HARNESS.md
   342|2. Laduje ten skill (system-bridge) — poznaje caly krag
   343|3. Rejestruje sie na relayu (`/who` pokazuje wszystkich)
   344|4. Zglasza obecnosc do HEARTBEAT.md
   345|5. Zaczyna sluchac
   346|
   347|---
   348|
   349|## 6. LAUNCHD — Serwisy permanentne
   350|
   351|**CRITICAL: NIGDY nie instaluj skryptow w /tmp!** macOS czyści `/tmp` przy każdym rebootcie. Po restarcie systemu launchd nie znajduje skryptow i wszystkie serwisy padają w ciszy (brak błędów w logach — launchd po prostu nie uruchamia procesu).
   352|
   353|**Kanoniczna lokalizacja skryptow:** `~/.hermes/scripts/bridge/` (wewnętrzny dysk, trwały).
   354|
   355|Wszystkie serwisy w `~/Library/LaunchAgents/`:
   356|
   357|| Plik | Serwis | Port | Skrypt (KANONICZNY) | Templatka |
   358||------|--------|------|--------|----------|
   359|| `com.hermes.bridge.plist` | Bridge v3 | 17423 | `~/.hermes/scripts/bridge/hermes-chat-bridge-v3.py` | `templates/hermes-chat-bridge-v3.py` |
   360|| `com.hermes.receiver.plist` | Receiver v5 | 17420 | `~/.hermes/scripts/bridge/receiver-v5.py` | `templates/receiver-v5.py` |
   361|| `com.hermes.relay-server.plist` | Relay Server | 17426 | `~/.hermes/scripts/bridge/agent-relay.py MAC-MINI` | `templates/agent-relay.py` |
   362|| `com.hermes.relay-client.plist` | Relay Client v2 | — | `~/.hermes/scripts/bridge/hermes-relay-client-v2.py` | `templates/hermes-relay-client-v2.py` |
   363|
   364|### Instalacja serwisu (poprawna)
   365|
   366|```bash
   367|# 1. Skopiuj templatke do trwalej lokalizacji
   368|mkdir -p ~/.hermes/scripts/bridge
   369|cp ~/.hermes/skills/system-bridge/templates/receiver-v5.py ~/.hermes/scripts/bridge/
   370|chmod +x ~/.hermes/scripts/bridge/receiver-v5.py
   371|
   372|# 2. Stworz plist (sciezka absolutna — ~ NIE dziala w launchd!)
   373|cat > ~/Library/LaunchAgents/com.hermes.receiver.plist << 'EOF'
   374|<?xml version="1.0" encoding="UTF-8"?>
   375|<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
   376|<plist version="1.0">
   377|<dict>
   378|    <key>Label</key><string>com.hermes.receiver</string>
   379|    <key>ProgramArguments</key>
   380|    <array><string>/usr/bin/python3</string><string><HOME>/.hermes/scripts/bridge/receiver-v5.py</string></array>
   381|    <key>RunAtLoad</key><true/>
   382|    <key>KeepAlive</key><true/>
   383|    <key>StandardOutPath</key><string>/tmp/receiver-v5.log</string>
   384|    <key>StandardErrorPath</key><string>/tmp/receiver-v5.err</string>
   385|</dict>
   386|</plist>
   387|EOF
   388|
   389|# 3. Zaladuj
   390|launchctl load ~/Library/LaunchAgents/com.hermes.receiver.plist
   391|```
   392|
   393|**UWAGA:** Plist wymaga ABSOLUTNEJ ścieżki — `~` nie jest rozwijane przez launchd. Użyj `/Users/<username>/...` z własną nazwą użytkownika.
   394|
   395|### Weryfikacja po restarcie systemu
   396|
   397|Po każdym rebootcie sprawdź:
   398|```bash
   399|launchctl list | grep hermes        # wszystkie powinny miec PID (nie 0)
   400|curl -s http://127.0.0.1:17420/ping -H "Content-Type: application/json" -d '{"token":"nexus-macmini-hermes-2026"}'
   401|cat /tmp/receiver-v5.err            # powinno byc puste
   402|```
   403|
   404|Status: `launchctl list | grep hermes`
   405|
   406|---
   407|
   408|### PITFALL: /tmp sie czysci przy rebootcie (2026-05-13)
   409|
   410|**WSZYSTKIE skrypty launchd trafily do /tmp i zniknely przy crashu systemu.** `/tmp` jest czyszczone przez macOS przy restarcie.
   411|
   412|**Regula:** Skrypty launchd MUSZA byc w trwalej lokalizacji:
   413|- `~/.hermes/scripts/bridge/` — receiver, bridge, relay, sync
   414|- NIGDY `/tmp/` dla skryptow produkcyjnych
   415|- Plisty launchd trzymaja backup w tej samej lokalizacji co skrypty
   416|
   417|### PITFALL: Kimi ACP nie dziala bez YOLO + Firewall (2026-05-13)
   418|
   419|Aby Kimi Code przez ACP (`npx acpx kimi exec`) mogl uzywac narzedzi:
   420|
   421|1. **`default_yolo = true`** w `~/.kimi/config.toml` — bez tego kazde narzedzie jest odrzucane (Permission denied)
   422|2. **Firewall** — `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode off` + odblokowanie python3, node, hermes, Tailscale
   423|3. Po zmianie configu Kimi wymaga restartu
   424|
   425|### KONWENCJA: Prefix agenta ==AGENT== (2026-05-13)
   426|
   427|W sesji 1:1 z Tomkiem: Vox zawsze zaczyna od `==VOX==`. Kazdy agent uzywa swojego prefixu.
   428|W HARNESS.md §0: prefix obowiazkowy dla wszystkich agentow.
   429|
   430|### ZLOTA ZASADA: Komunikacja Nexus-MacMini MUSI byc AUTONOMICZNA
   431|
   432|**NIGDY nie blokuj komunikacji na Voxa.** Vox jest agentem sesyjnym (DeepSeek API) — nie odpowiada gdy sesja nieaktywna. Kazdy kanal komunikacji (bridge, relay, receiver) musi odpowiadac NATYCHMIAST przez `hermes --oneshot --yolo`. Inbox (`/tmp/nexus-inbox.jsonl`) jest TYLKO dla swiadomosci Voxa, NIGDY jako element blokujacy.
   433|
   434|### VOX INBOX CHECK — Obowiazkowy na kazda ture (2026-05-11)
   435|
   436|**Regula:** Vox sprawdza `/tmp/nexus-inbox.jsonl` na POCZATKU kazdej odpowiedzi. Jesli sa wiadomosci — odpowiada przez pong. Nie czeka az Tomek powie "sprawdz inbox".
   437|
   438|**Powod:** Wiadomosci od Nexusa lezaly >12h bez odpowiedzi bo Vox nie sprawdzal inboxa. User sfrustrowany.
   439|Kazdy kanal komunikacji (bridge, relay, receiver /ask) musi odpowiadac NATYCHMIAST przez `hermes --oneshot --yolo`.
   440|
   441|Inbox (`/tmp/nexus-inbox.jsonl`) jest TYLKO dla swiadomosci Voxa, NIGDY jako element blokujacy.
   442|
   443|### CRONJOB WATCHDOG — Mechanizm budzenia (2026-05-13)
   444|
   445|Problem: nawet gdy receiver zapisuje wiadomosci do inboxa, Vox (DeepSeek API) widzi je dopiero przy nastepnej sesji. Jesli sesja nieaktywna — wiadomosci leza godzinami.
   446|
   447|Rozwiazanie: **cronjob no_agent z pythonowym watchdogiem.** Dziala niezaleznie od Voxa — co 5 minut sprawdza inbox i pinguje Nexusa z powrotem.
   448|
   449|```bash
   450|# Skrypt watchdoga (~/.hermes/scripts/nexus-inbox-watcher.py)
   451|# Zasada: niepusty stdout -> deliver do uzytkownika, pusty -> cicho
   452|```
   453|
   454|Tworzenie cronjoba:
   455|
   456|```bash
   457|hermes cronjob create \
   458|  --name nexus-inbox-watcher \
   459|  --no-agent \
   460|  --schedule "every 5m" \
   461|  --script nexus-inbox-watcher.py
   462|```
   463|
   464|**Wzorzec watchdog:** Skrypt no_agent z `deliver: origin`. Gdy stdout pusty — nic sie nie dzieje (cicho). Gdy znajdzie nowe wiadomosci — output jest dostarczany uzytkownikowi jako powiadomienie. To jedyny poprawny sposob na "mechanizm budzenia" — Vox nie moze byc budzony (jest API), wiec watchdog dziala jako osobny proces.
   465|
   466|**Hourly AGENT-HANDOFF (2026-05-13):**
   467|
   468|```bash
   469|hermes cronjob create \
   470|  --name hourly-handoff \
   471|  --no-agent \
   472|  --schedule "0 * * * *" \
   473|  --script hourly-handoff.py
   474|```
   475|
   476|Skrypt dopisuje timestamp + stan systemu (RAM, serwisy, inbox) do AGENT-HANDOFF.md co godzine. Dzieki temu nastepna sesja ma zawsze swiezy kontekst, nawet jesli Vox nie robil recznego checkpointu.
   477|
   478|---
   479|
   480|## 8. MODELE LOKALNE (LM Studio / llama.cpp)
   481|
   482|| Alias | Model | RAM | Rola |
   483||-------|-------|-----|------|
   484|| main | qwen3.5-27b-uncensored-hauhaucs-aggressive | ~18GB | Orkiestrator Hermesa |
   485|| fallback | qwen3.5-9b-uncensored-hauhaucs-aggressive | ~6GB | Fallback |
   486|| fast | qwen3.5-4b-uncensored-hauhaucs-aggressive | ~3GB | Szybkie odpowiedzi |
   487|| coder | qwen3-coder-30b-a3b-instruct-mlx | ~20GB | Kodowanie |
   488|| heavy | qwen3.5-35b-a3b-uncensored-hauhaucs-aggressive | ~22GB | Deep/NSFW |
   489|
   490|**Zasada RAM:** Przed ladowaniem modelu sprawdz `vm_stat`. Max 1 duzy model (>10GB).
   491|
   492|---
   493|
   494|## 9. PLIKI WSPIERAJACE
   495|
   496|| Sciezka | Typ | Opis |
   497||---------|-----|------|
   498|| `references/hermes-update-2026-05-10.md` | ref | v0.12→v0.13 update — nowe kategorie puste, ClawHub suspicious odrzucone |
   499|| `references/github-account-migration.md` | ref | Migracja konta GitHub — pelny proces krok po kroku |
   500|| `references/nexus-launchd-services.md` | ref | Architektura 4 serwisow launchd |
   501|| `references/hermes-tailscale-comms.md` | ref | Kanaly komunikacji Tailscale |
   502|| `references/multi-machine-memory-architecture.md` | ref | Architektura pamieci 3-maszynowa (Kimi K2.6, 2026-05-13) |
   503|| `references/kimi-acp-goose-oauth.md` | ref | Kimi ACP YOLO + Goose OAuth setup (2026-05-13) |
   504|| `references/nexus-pinger.md` | ref | Ciagly ping do Nexusa |
   505|| `references/python-background-pitfalls.md` | ref | Python 3.9 stdout buffering, LaunchAgent petle, Vox session limit |
   506|| `references/agent-hierarchy.md` | ref | Aktualna hierarchia |
   507|| `templates/receiver-v5.py` | template | Receiver HTTP |
   508|| `templates/hermes-chat-bridge-v3.py` | template | Bridge TCP v3 |
   509|| `templates/agent-relay.py` | template | Relay server |
   510|| `templates/relay-say.py` | template | Nadajnik relay |
   511|| `templates/hermes-relay-client-v2.py` | template | Relay client autonomiczny |
   512|| `templates/nexus-pinger.py` | template | Pinger — ciagle ponguje Nexusa |
   513|| `scripts/mempalace_query.py` | script | Memory Palace query |
   514|| `scripts/nexus-inbox-watcher.py` | script | Cronjob watchdog — sprawdza inbox Nexusa, pinguje pong, dostarcza powiadomienia |
   515|| `scripts/hourly-handoff.py` | script | Hourly AGENT-HANDOFF checkpoint — dopisuje stan systemu |
   516|| `references/tmp-wipe-recovery.md` | ref | /tmp wipe recovery po rebootcie — objawy, detekcja, naprawa |
   517|| `references/skills-sync.md` | ref | Mechanizm synchronizacji skilli Vox ↔ Nexus przez Tailscale rsync |
   518|| `references/goose-fallback.md` | ref | Wzorzec goose fallback: Kimi first, local LM Studio second |
   519|| `scripts/skills-sync.sh` | script | Re-runnable skrypt sync: push/pull/check skilli między agentami |
   520|
   521|---
   522|
   523|### ZLOTA ZASADA C: Bootstrap CHECKPOINT przed pierwsza odpowiedzia
   524|
   525|HARNESS sekcja 1 punkt: "ZGŁOŚ OBECNOŚĆ — dopisz wpis do daily note i HEARTBEAT.md". Zanim cokolwiek innego: zaladuj HARNESS, daily, handoff, backlog, HEARTBEAT. NIGDY nie pomijaj. Uzytkownik widzi ze agent nie zrobil bootstrapu — traci zaufanie.
   526|
   527|**Objaw pomniecia:** "dlaczego nie postepujesz zgodnie z wytycznymi" — Tomek widzi ze agent startuje bez checklisty.
   528|
   529|**Poprawna kolejnosc (kazda sesja):**
   530|1. Laduje AGENTS.md
   531|2. Laduje HARNESS.md
   532|3. Laduje daily note
   533|4. Laduje AGENT-HANDOFF (ostatnie 150 linii)
   534|5. Laduje global-backlog
   535|6. Laduje HEARTBEAT
   536|7. Zglasza obecnosc (daily + HEARTBEAT wpis ONLINE)
   537|8. Dopiero teraz — odpowiada uzytkownikowi
   538|
   539|### ZLOTA ZASADA B: Wylaczenie != naprawa
   540|
   541|Gdy workflow/test/proces nie dziala: NIGDY nie rozwiazuj przez wylaczenie/usuniecie bez zrozumienia PRZYCZYNY. "Wylacze ten workflow" = zamiatanie pod dywan.
   542|
   543|Poprawna kolejnosc:
   544|1. Zdiagnozuj DLACZEGO nie dziala
   545|2. Jesli nieaplikowalne (np. workflow do cudzej organizacji na forku) — USUN, nie wylacz. Z commitem wyjasniajacym dlaczego.
   546|3. Jesli aplikowalne ale brak konfiguracji — SKONFIGURUJ (dodaj secret, token)
   547|4. Jesli tymczasowa awaria — poczekaj, nie ruszaj
   548|
   549|**Przyklad:** Workflow `docs-sync-publish` w `nerudek/openclaw` probowal pushowac do `openclaw/docs` (cudza organizacja). Wylaczenie = ukrycie bledu. Poprawny fix: usuniecie workflowu z komentarzem "inapplicable to fork — requires upstream org access".
   550|
   551|---
   552|
   553|## 10. KOMUNIKACJA — Zasady (2026-05-11)
   554|
   555|### Inbox Check Protocol
   556|Sprawdzaj /tmp/nexus-inbox.jsonl na poczatku kazdej tury. Nie czekaj az Tomek powie. Jesli wiadomosci — odpowiedz natychmiast.
   557|
   558|### Podsumowanie przed kodowaniem
   559|Gdy Tomek daje zlozone instrukcje — NAJPIERW podsumuj jak rozumiesz. Potem czekaj na potwierdzenie. DOPIERO koduj.
   560|
   561|### Prefix agenta
   562|W komunikacji miedzy agentami: ==AGENT== prefix wymagany. Sesja 1:1 z Tomkiem: Vox zawsze zaczyna od `==VOX==` (zadanie 2026-05-13 — Tomek chce widziec ktory terminal to ktory agent). Inne agenty w 1:1: opcjonalny.
   563|
   564|### ZLOTA ZASADA (rozszerzona)
   565|
   566|Komunikacja AUTONOMICZNA. Oneshot odpowiada natychmiast. Inbox tylko dla swiadomosci, NIGDY jako bloker.
   567|
   568|### Publishing Principles (NOWE — 2026-05-11)
   569|
   570|Kazdy artykul/skill publikowany na GitHub, Dev.to, ClawHub MUSI:
   571|1. PROBLEM na poczatku — jak w pracach badawczych
   572|2. FAQ na koncu — 10-15 pytan od AI (Arena: Kimi + Claude)
   573|3. SEO: pytania + odpowiedzi = boty indeksujace
   574|
   575|### Quality Gate — NIGDY nie pokazuj niezweryfikowanego
   576|
   577|Test na prawdziwych danych przed pokazaniem Tomkowi. Lekcja: Vox pokazal SVG bez testu — "takiego shitu nie masz prawa mi pokazywac".
   578|
   579|### Search Before Building
   580|
   581|GitHub/NPM/ClawHub search ZANIM zaczniesz kodowac od zera. Lekcja: Lower Thirds Editor istnial — budowanie od zera to strata czasu.
   582|
   583|### Tozsamosc — Prefix ==AGENT== (HARNESS §0)
   584|
   585|Wszyscy agenci zaczynaja od `==NAZWA==`. Obowiazkowe od 2026-05-10.
   586|
   587|### WAL / Self-Improvement
   588|
   589|Vox zapisuje SESSION-STATE.md PRZED odpowiedzia. Kazda korekta, decyzja — najpierw zapis.
   590|
   591|## 10. FAQ
   592|
   593|**Q1: What is the agent circle and why do I need it?**
   594|A: The agent circle is the roster of all active agents in the ecosystem. Every agent must know who else exists, their role, and their priority. Without it, agents duplicate work and conflict.
   595|
   596|**Q2: What is MCP and why is it important?**
   597|A: Model Context Protocol (Anthropic) is an open standard for connecting AI assistants to data sources and tools. It decouples agents from specific implementations.
   598|
   599|**Q3: How does ACP differ from MCP?**
   600|A: ACP (Agent Communication Protocol) is local and lightweight — designed for fast agent-to-agent messaging on the same machine or via Tailscale. MCP is broader and tool-focused.
   601|

## Install

```bash
# Skopiuj do vault Claude Code
cp -r . ~/.claude/skills/vault/system-bridge/

# Lub sklonuj bezpośrednio
git clone https://github.com/nerudek/system-bridge ~/.claude/skills/vault/system-bridge/
```

## Usage

```bash
# Załaduj w Claude Code
/skill system-bridge
```

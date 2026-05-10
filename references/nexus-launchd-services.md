# Architektura Komunikacji Nexus-MacMini

## Stan 2026-05-10

### 4 serwisy launchd (auto-start, auto-restart)

| Label | Port | Skrypt | Rola |
|-------|------|--------|------|
| `com.hermes.bridge` | 17423 TCP | `hermes-chat-bridge-v3.py` | Chat bridge — oneshot + inbox |
| `com.hermes.receiver` | 17420 HTTP | `receiver-v5.py` | Receiver — /ask(oneshot), /vox(inbox), /exec, /ping |
| `com.hermes.relay-server` | 17426 TCP | `agent-relay.py MAC-MINI` | Multi-party relay server |
| `com.hermes.relay-client` | — | `hermes-relay-client-v2.py` | Autonomiczny klient relayu MAC-MINI-HERMES |

### Pliki plist

Wszystkie w `~/Library/LaunchAgents/`:
- `com.hermes.bridge.plist` — `/usr/bin/python3 /tmp/hermes-chat-bridge-v3.py`
- `com.hermes.receiver.plist` — `/usr/bin/python3 /tmp/receiver-v5.py`
- `com.hermes.relay-server.plist` — `/usr/bin/python3 /tmp/agent-relay.py MAC-MINI`
- `com.hermes.relay-client.plist` — `/usr/bin/python3 /tmp/hermes-relay-client-v2.py`

### Zasada krytyczna

WSZYSTKIE kanaly autonomizne. Oneshot odpowiada natychmiast. Inbox tylko dla swiadomosci Voxa.

Zlamanie tej zasady (bridge v2 czekajacy na outbox) = Nexus czeka >30 minut.
